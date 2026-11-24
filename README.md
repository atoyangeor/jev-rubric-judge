# jev-rubric-judge

Jev (TypeSafe) answers yes/no rubric questions about LLM outputs and returns a probability.
Confident answers are taken from Jev, the rest go to a human. The experiment measures how many
questions out of 100 a human still has to label when the answers taken from Jev must be right at
least as often as one expert's (94.1% on InFoBench), and compares Jev's probability with the
first-token logprobs of an LLM judge.

Data: the expert-annotated part of InFoBench (arXiv 2401.03601), 50 instructions, 1,123 question-response
pairs with three readable expert answers. Files in `data/raw/` come from https://github.com/qinyiwei/InfoBench
and https://huggingface.co/datasets/kqsong/InFoBench.

```
uv sync
cp .env.example .env            # put TYPESAFE_API_KEY and OPENAI_API_KEY there
uv run pytest
uv run python -m jev_rubric_judge.cli prepare
uv run python -m jev_rubric_judge.cli run-jev --part dev --variant noul-plain
uv run python -m jev_rubric_judge.cli run-llm --part dev
uv run python -m jev_rubric_judge.cli report --part dev
```

`data/split.json` holds the dev/test split by instruction, `data/frozen.json` the variant and boundaries
fixed on the dev set before the test run. Every model answer is cached in `runs/`.
