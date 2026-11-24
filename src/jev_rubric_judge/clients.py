"""HTTP clients for Jev (TypeSafe) and for the LLM judge (OpenAI Chat Completions)."""
from __future__ import annotations

import math
import time
from dataclasses import dataclass

import httpx

from .cost import CostMeter

RETRY_STATUS = {429, 500, 502, 503, 504, 529}

# Rules for YES and NO, copied from evaluation.py of the InFoBench repository (the prompt GPT-4 got in the paper).
INFOBENCH_SYS_MSG = "Based on the provided Input (if any) and Generated Text, answer the ensuing Questions with either a YES or NO choice. Your selection should be based on your judgment as well as the following rules:\n\n- YES: Select 'YES' if the generated text entirely fulfills the condition specified in the question. However, note that even minor inaccuracies exclude the text from receiving a 'YES' rating. As an illustration. consider a question that asks. \"Does each sentence in the generated text use a second person?” If even one sentence does not use the second person, the answer should NOT be 'YES'. To qualify for a 'YES' rating, the generated text must be entirely accurate and relevant to the question\n\n- NO: Opt for 'NO' if the generated text fails to meet the question's requirements or provides no information that could be utilized to answer the question. For instance, if the question asks. \"Is the second sentence in the generated text a compound sentence?\" and the generated text only has one sentence. it offers no relevant information to answer the question. Consequently, the answer should be 'NO'.'''"


def _post(http: httpx.Client, url: str, headers: dict, body: dict, attempts: int = 6) -> tuple[dict, float]:
    delay = 1.0
    for attempt in range(attempts):
        started = time.perf_counter()
        try:
            r = http.post(url, headers=headers, json=body)
        except httpx.TransportError:
            if attempt == attempts - 1:
                raise
            time.sleep(delay); delay *= 2
            continue
        elapsed = time.perf_counter() - started
        if r.status_code in RETRY_STATUS and attempt < attempts - 1:
            time.sleep(delay); delay *= 2
            continue
        if r.status_code != 200:
            raise RuntimeError(f"{url} -> {r.status_code}: {r.text[:300]}")
        return r.json(), elapsed
    raise RuntimeError("unreachable")


@dataclass
class JevClient:
    api_key: str
    model: str  # pin a version, e.g. "jev-1.14.0"
    http: httpx.Client
    meter: CostMeter
    url: str = "https://api.typesafe.ai/v1/systemone"

    def ask(self, state, questions: dict[str, dict]) -> tuple[dict[str, float], dict, float]:
        """One request: one state, many yes/no questions. Returns {question id: probability of yes}."""
        body = {"model": self.model, "state": state, "questions": questions}
        data, elapsed = _post(self.http, self.url, {"Authorization": f"Bearer {self.api_key}"}, body)
        usage = data.get("usage", {})
        self.meter.add(usage.get("input_tokens", 0), usage.get("output_tokens", 0))
        return {qid: a["noul"] for qid, a in data["answers"].items()}, usage, elapsed


@dataclass
class OpenAIJudge:
    api_key: str
    model: str
    http: httpx.Client
    meter: CostMeter
    url: str = "https://api.openai.com/v1/chat/completions"

    @staticmethod
    def build_prompt(input_text: str, response: str, question: str, instruction: str | None = None,
                     examples: list[dict] | None = None) -> str:
        """The paper's prompt. Optional additions mirror the Jev variants: the original instruction, or
        the same eight judged examples the few-shot Jev variant gets."""
        head = f"{INFOBENCH_SYS_MSG}\n\n"
        for n, ex in enumerate(examples or [], 1):
            head += f"Example {n}\n"
            if ex.get("input", "").strip():
                head += f"Input:\n\"{ex['input']}\"\n\n"
            head += f"Generated Text:\n\"{ex['generated_text']}\"\n\nQuestion:\n{ex['question']}\n\nAnswer: {ex['answer'].upper()}\n\n"
        if examples:
            head += "Now judge this one.\n\n"
        if instruction:
            head += f"Instruction given to the model:\n\"{instruction}\"\n\n"
        if input_text.strip():
            head += f"Input:\n\"{input_text}\"\n\n"
        return f"{head}Generated Text:\n\"{response}\"\n\nQuestion:\n{question}\n\nAnswer with one word: YES or NO."

    def ask(self, input_text: str, response: str, question: str, instruction: str | None = None,
            examples: list[dict] | None = None) -> tuple[float | None, str, dict, float]:
        """One call per question. Returns (P(yes) from first-token logprobs, answer text, usage, seconds)."""
        body = {
            "model": self.model,
            "messages": [{"role": "user", "content": self.build_prompt(input_text, response, question, instruction, examples)}],
            "logprobs": True,
            "top_logprobs": 5,
            # Cost safety: reasoning off, short answer. Checked 2026-11-24: 0 reasoning tokens, 4 output tokens.
            # 8 was too low: one dev set call in 1,175 failed with "max_tokens or model output limit was reached".
            "reasoning_effort": "none",
            "max_completion_tokens": 32,
        }
        data, elapsed = _post(self.http, self.url, {"Authorization": f"Bearer {self.api_key}"}, body)
        usage = data["usage"]
        reasoning = (usage.get("completion_tokens_details") or {}).get("reasoning_tokens") or 0
        self.meter.add(usage["prompt_tokens"], usage["completion_tokens"], reasoning)
        choice = data["choices"][0]
        return p_yes_from_logprobs(choice.get("logprobs")), choice["message"]["content"] or "", usage, elapsed


def p_yes_from_logprobs(logprobs: dict | None) -> float | None:
    """P(yes) / (P(yes) + P(no)) over the first token's alternatives; spellings 'Yes', 'YES', ' yes' are summed."""
    content = (logprobs or {}).get("content") or []
    if not content:
        return None
    yes = no = 0.0
    for alt in content[0]["top_logprobs"]:
        token = alt["token"].strip().lower()
        if token.startswith("yes"):
            yes += math.exp(alt["logprob"])
        elif token.startswith("no"):
            no += math.exp(alt["logprob"])
    return yes / (yes + no) if yes + no > 0 else None
