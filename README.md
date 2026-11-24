# jev-rubric-judge

Can a decision model take over part of a human labeler's work on yes/no rubric questions, without
being wrong more often than the human?

**Short answer on this data: almost, and not proven.** With [Jev](https://docs.typesafe.ai) (TypeSafe)
a human still labels 19.9 questions out of 100, but the answers taken from Jev are right in 93.0% of
cases, below the 94.1% that one expert reaches. An LLM judge reading first-token logprobs meets the
condition (95.6%) but leaves 25.2 questions out of 100 to the human. The test set is small, and the
interval around 93.0% (90.6–95.1) contains 94.1.

Status: experiment run once on the test set on 2026-11-24. Last updated 2026-11-24.

## Words used below

| Word | Meaning |
|---|---|
| InFoBench | Public dataset (arXiv 2401.03601). LLMs were given instructions; people checked each LLM response against a list of yes/no questions |
| Response | The text one of five LLMs (`gpt-3.5-turbo`, `gpt-4`, `claude-v1`, `alpaca-7b`, `vicuna-13b`) wrote for an instruction. It is the thing being checked |
| Question | One yes/no question about one response. The unit of every count in this file |
| Correct answer | The answer at least two of the three experts gave |
| Jev | TypeSafe's decision model. For a yes/no question it returns a number from 0 to 1: the probability that the answer is yes |
| LLM judge | A general LLM asked the same question. Here `gpt-6-luna` (OpenAI), reasoning off |
| Boundaries `t_yes`, `t_no` | Two numbers. Probability of yes at or above `t_yes`: take "yes" from the model. At or below `t_no`: take "no". In between: a human labels the question |
| Dev set, test set | Two parts of the data, split by instruction. Settings are chosen on the dev set; the result is computed once on the test set |

## The idea

A team that checks its LLM with rubric questions pays a person for every answer. Suppose instead a
model answers first and says how sure it is. Answers it is sure of are taken as they are; the rest go
to the person. The useful number is how many questions the person still has to label, on the condition
that the answers taken from the model are not worse than the person's own.

Three experts are **not** replaced. Their answers are the yardstick: they define the correct answer.
What the model replaces is part of the work of **one** labeler, and the quality bar is the level of
one expert measured against that yardstick.

## Data

Files in `data/raw/`, copied from the authors' public folder
(https://github.com/qinyiwei/InfoBench, `expert_annotation/`) and from
https://huggingface.co/datasets/kqsong/InFoBench:

| File | What one row is | Rows used |
|---|---|---|
| `expert_easy.csv`, `expert_hard.csv` | One instruction: its `input`, five responses, and for each response the answers of three experts to every question | 25 + 25 instructions |
| `InfoBench.json` | One instruction with the clean text of its questions and a category per question (`Content`, `Format`, `Number`, `Linguistic`, `Style`) | the same 50 instructions |

The experts' cells come in three formats (`1. Yes\n2. No`, `yes\nno`, `1.0.1`); `data.py` parses all three.
The third expert's column has no "annotator3" in its name (`<model>-annotation`); treating it as the third
expert is an assumption.

One real example (test set, instruction `user_oriented_task_3`, response of `gpt-4`; the author list in
`input` is shortened here):

```
instruction: You are given a paper citation, convert it to the requested citation style.
input:       Chicago: Vaswani, Ashish, Shazeer, Noam, … "Attention Is All You Need." arXiv, (2017). https://doi.org/10.48550/arXiv.1706.03762.
             MLA:
response:    Vaswani, Ashish, et al. "Attention Is All You Need." arXiv, 2017, https://doi.org/10.48550/arXiv.1706.03762.
```

| # | Question | Expert 1 | Expert 2 | Expert 3 | Correct answer |
|---|---|---|---|---|---|
| 1 | Is the generated text a paper citation? | yes | yes | yes | yes |
| 2 | Does the generated text comply with the requested citation style (MLA citation style)? | yes | yes | no | yes |
| 3 | Does the generated paper citation match the citation in the given input? | yes | yes | yes | yes |

Counts:

- 50 instructions × 5 responses, 1,135 questions. Twelve questions (two `alpaca-7b` responses, six
  questions each) are dropped: for `domain_oriented_task_153` the second expert's cell is empty, for
  `domain_oriented_task_139` the third expert's cell holds five answers for six questions (`1.1.0.0.0.`).
  **1,123 questions** remain. One dropped response falls in the dev set and one in the test set, hence
  99 and 149 responses below.
- The correct answer is "yes" in 929 of 1,123 (82.7%).
- **One expert's level.** Each expert's answer equals the correct answer in 1,071, 1,060 and 1,040 of
  1,123 questions (95.4%, 94.4%, 92.6%); the mean is **94.1%**. This is the quality bar.
- All three experts agree on 925 of 1,123 questions (82.4%).

| Part | Instructions | Responses | Questions | Correct answer is "yes" |
|---|---|---|---|---|
| Dev set | 20 | 99 | 479 | 382 (79.7%) |
| Test set | 30 | 149 | 644 | 547 (84.9%) |

The split is random by instruction with a fixed seed (`data/split.json`); all questions of an
instruction stay in one part.

## Method, step by step

1. **Load** the three files into one table: one row per question about one response (`data.py`).
2. **Correct answer** = the answer of at least two of three experts.
3. **Split** into dev set and test set by instruction (`split.py`).
4. **Ask Jev** (`jev-1.14.0`): one request per response, carrying the `input`, the response and all its
   questions as `noul` questions. Jev returns one probability per question. Four request variants were
   tried on the dev set:

   | Variant | What the request holds besides `input`, response and questions |
   |---|---|
   | `noul-plain` | Nothing |
   | `noul-criteria` | A rule for what counts as yes and as no |
   | `noul-instruction` | The original instruction |
   | `noul-fewshot` | Eight dev set questions with their correct answers as examples (`data/fewshot_examples.json`) |

5. **Ask the LLM judge** (`gpt-6-luna`): one call per question, with the judge prompt from the InFoBench
   repository (`evaluation.py`) plus "Answer with one word: YES or NO." The probability of yes is
   P(yes) / (P(yes) + P(no)) over the first token's logprobs. Every question is asked three times and
   the mean is used, because the probability changes between identical calls (on the test set the three
   repeats differ by 0.10 or more on 44 of 644 questions). Three variants: the paper's prompt as is,
   with the original instruction, with the same eight examples.
6. **Choose the variant and the boundaries on the dev set.** For every pair of boundaries on a 0.01
   grid: keep the pairs under which at least 96% of the answers taken from the model are right, and
   among them take the pair that leaves the fewest questions to a human. Per model, the variant with the
   fewest questions left goes to the test set.
7. **Freeze.** The chosen variants and boundaries are written to `data/frozen.json` and committed
   (commit `11f0f23`) before any model saw the test set.
8. **Run the test set once** and compute the numbers below. Intervals are 95% bootstrap intervals:
   the 30 test instructions are resampled with replacement 2,000 times.

Why 96% on the dev set when the condition is 94.1%: boundaries tuned to exactly 94.1% on ten dev
instructions met 94.1% on the other ten in only 90 of 200 random halves (Jev `noul-fewshot`); with 96%,
in 135 of 200. This margin was added after the first dev set results and before the test run. It is a
change from the original design, which tuned to 94.1%.

## Results

### Dev set (settings were chosen here, so these numbers are optimistic)

All rows use the same 471 questions: 8 of the 479 are the few-shot examples.

| # | Model and variant | Right without a human | `t_yes` / `t_no` | Questions per 100 left to a human | Answers taken from the model that are right |
|---|---|---|---|---|---|
| 1 | Jev `noul-fewshot` | 426 of 471 (90.4%) | 0.83 / 0.42 | 18.3 | 370 of 385 (96.1%) |
| 2 | Jev `noul-instruction` | 427 of 471 (90.7%) | 0.81 / 0.21 | 18.7 | 368 of 383 (96.1%) |
| 3 | Jev `noul-plain` | 416 of 471 (88.3%) | 0.91 / 0.34 | 28.2 | 325 of 338 (96.2%) |
| 4 | Jev `noul-criteria` | 411 of 471 (87.3%) | 0.86 / 0.24 | 33.3 | 302 of 314 (96.2%) |
| 5 | LLM judge, with instruction | 402 of 471 (85.4%) | 0.69 / never takes "no" | 29.3 | 321 of 333 (96.4%) |
| 6 | LLM judge, paper's prompt | 414 of 471 (87.9%) | 0.91 / never takes "no" | 29.9 | 317 of 330 (96.1%) |
| 7 | LLM judge, with examples | 411 of 471 (87.3%) | 0.85 / never takes "no" | 30.4 | 315 of 328 (96.0%) |

"Right without a human": probability above 0.5 counts as "yes", otherwise "no". "Never takes no": no
boundary for "no" kept the taken answers at 96%, so every "no" of the LLM goes to a human.
Rows 1 and 5 went to the test set.

### Test set (the result)

644 questions, 30 instructions, one run, frozen settings.

| # | Model | Right without a human | Questions per 100 left to a human | Answers taken from the model that are right | Condition 94.1% |
|---|---|---|---|---|---|
| 1 | Jev `noul-fewshot` | 576 of 644, 89.4% (86.6–91.8) | 19.9: 128 of 644 (15.4–24.8) | 480 of 516, 93.0% (90.6–95.1) | **Not met**; 486 right answers were needed |
| 2 | LLM judge `gpt-6-luna`, with instruction | 542 of 644, 84.2% (80.4–88.0) | 25.2: 162 of 644 (18.8–31.4) | 461 of 482, 95.6% (93.5–97.6) | Met by the number itself (454 were needed); the interval also contains 94.1 |

Jev against the LLM judge on the same resampled instructions (paired bootstrap, 2,000 resamples):

| What is compared | Jev minus LLM judge | 95% interval | Reading |
|---|---|---|---|
| Questions per 100 left to a human | −5.3 | −13.0 to 1.8 | Contains 0: that Jev leaves fewer questions is not established |
| Share of taken answers that are right, points | −2.6 | −5.0 to −0.5 | Does not contain 0: the answers taken from Jev are right less often |

The example from the data section, as it went through the test run:

| Question | Correct answer | Jev's probability of yes | What happens with Jev | LLM's probability of yes | What happens with the LLM |
|---|---|---|---|---|---|
| 1 | yes | 0.97 | "yes" taken, right | 1.00 | "yes" taken, right |
| 2 | yes | 0.68 | goes to a human | 1.00 | "yes" taken, right |
| 3 | yes | 0.40 | "no" taken, **wrong** | 0.63 | goes to a human |

### Compared with what the dataset and the paper already had

Rows 1–4 come from the data and the paper and were not recomputed here. Rows 5–9 are computed in this
repository.

| # | Way of checking | Source of the number | Questions | Right answers | Cost |
|---|---|---|---|---|---|
| 1 | Three experts | Paper, Table 4 | 1,135 | The yardstick: the correct answer is theirs by definition | $1,416 |
| 2 | One expert | Computed here from the data; cost is a third of row 1 | 1,123 | 94.1% | $472 |
| 3 | Crowd workers (three per task) | Paper, Table 4 | 1,135 | 84% | $187.50 |
| 4 | GPT-4 (`gpt-4-0314`) | Paper, Table 4 | 1,135 | 89% | $19.40 |
| 5 | Always answer "yes" | Computed here | 644 (test set) | 84.9% | $0 |
| 6 | Jev alone | This run | 644 (test set) | 89.4% | $0.01 |
| 7 | LLM judge alone | This run | 644 (test set) | 84.2% | $0.11 for three calls per question |
| 8 | Jev, the rest by one expert | This run | 644 (test set) | 93.0% of the 516 answers taken from Jev | $53 for the expert's 128 questions instead of $268 for 644 |
| 9 | LLM judge, the rest by one expert | This run | 644 (test set) | 95.6% of the 482 answers taken from the LLM | $67 for the expert's 162 questions instead of $268 for 644 |

One expert answer costs $0.42: the paper's $1,416 divided by three experts and 1,135 questions.

### The three success conditions written down before the runs

| # | Condition | Outcome |
|---|---|---|
| 1 | A human labels at most 50 questions of 100, and at least 94.1% of the answers taken from Jev are right | **Not met**: 19.9 of 100, but 93.0% |
| 2 | Jev alone is right at least as often as crowd workers in the paper (84%) | Met: 89.4%. Note that always answering "yes" already gives 84.9% on the test set, so this bar is low |
| 3 | Jev's probability is not worse for this purpose than the LLM's logprobs | Not shown. Jev leaves fewer questions to a human, but only the LLM met the quality condition |

### What went wrong for Jev (looked at after the run; settings were not changed)

| Answers taken from Jev | Dev set | Test set |
|---|---|---|
| "yes" | 319 of 333 right (95.8%) | 433 of 450 right (96.2%) |
| "no" | 51 of 52 right (98.1%) | 47 of 66 right (71.2%) |

The boundary for "no" (0.42) looked safe on the dev set and did not hold on the test set. The LLM met
the condition because it took no "no" answers at all. "Take only yes from Jev" is a guess made after
seeing the test set. It is not a result, and there is no unseen expert-labeled data left in InFoBench
to check it.

Taking only "yes" from Jev on the test set would give 433 of 450 right (96.2%, interval 94.2–98.1) and
leave 194 of 644 questions to a human: 30.1 per 100, more than the LLM judge's 25.2.

Of the 36 wrong answers taken from Jev, 22 are on questions where the experts themselves disagreed.

### How one expert does on the same questions (computed after the run)

The 94.1% bar is one expert's level on all questions. The questions a model is sure of are the easier
ones, and experts are right on them more often too:

| Test set questions | How many | One expert right (mean of three) | The model right |
|---|---|---|---|
| All | 644 | 93.8% | not applicable |
| Taken from Jev | 516 | 94.8% | 93.0% |
| Left to a human by Jev | 128 | 89.8% | not applicable |
| Taken from the LLM judge | 482 | 95.3% | 95.6% |
| Left to a human by the LLM judge | 162 | 89.3% | not applicable |

So on the questions it took, Jev is 1.8 points below one expert, and the LLM judge is level with one.
The questions left to the human are the ones where a single expert is right only about 9 times in 10.

## Cost and speed

- Whole experiment: about $0.51 (Jev $0.03, OpenAI $0.48), measured from the `usage` field of every response.
- Jev: $0.042 per million input tokens (docs.typesafe.ai, read 2026-11-22). Test set: 149 requests,
  227,787 input tokens, $0.0096; median 0.21 s per request, 4.3 questions per request on average.
- `gpt-6-luna`: $0.10 per million input and $0.50 per million output tokens (OpenAI pricing page,
  "Standard", read 2026-11-24). Test set: 1,932 calls, 1,074,519 input tokens, $0.11; median 0.92 s per call.
- Timings are from one laptop on one day. They are not a benchmark.

## Weak points

1. **The main condition was missed, and the data cannot say by how much.** 93.0% with an interval of
   90.6–95.1. The interval contains 94.1, so neither "Jev is as good as one expert" nor "Jev is worse"
   is established.
2. **Small data.** 50 instructions in total, 30 in the test set. Questions about one instruction
   resemble each other, so 644 questions carry less information than 644 independent ones.
3. **The test set is spent.** Any further tuning on these 50 instructions is no longer a clean test.
4. **The selection rule was changed once**, from 94.1% to 96% on the dev set, after dev results and
   before the test run (see Method).
5. **The 94.1% bar favours the expert.** An expert's own vote is one of the three that define the
   correct answer: he needs one of the other two to agree. A model needs two of three.
6. **The yardstick is a ceiling.** When two experts are wrong and the model is right, the model is
   counted wrong.
7. **"One labeler" is an assumption.** The savings are counted against one expert labeling everything
   ($472 for 1,135 questions). A team that puts three people on every question needs a different
   comparison, and for it 94.1% would be too low a bar.
8. **Reference numbers are not on the same questions.** 84% (crowd workers) and 89% (GPT-4) are the
   paper's numbers on all 1,135 questions; ours are on the 644 test questions. GPT-4 in the paper also
   answered the questions of one response in one conversation, not one call per question.
9. **The LLM judge variant was chosen for routing, not for accuracy alone.** Its 84.2% without a human
   is below always answering "yes" (84.9%). On the dev set the paper's prompt was better without a human
   (87.9% against 85.4%); it was not run on the test set.
10. **One LLM judge, cheap tier, reasoning off, one-word answer.** A stronger model, reasoning, or a
   different way of getting a probability may do better. The comparison says nothing about them.
11. **Only yes and no.** InFoBench has no "not applicable" or "can't tell" labels, so those answers are
    not tested.
12. **Old responses, English only.** The responses were written by 2023 models.
13. **The third expert's column is assumed** from its name (see Data).

## Risks if someone uses this as is

- Boundaries chosen on a small labeled sample drift. On unseen instructions the share of right answers
  fell from 96.1% to 93.0%. A team needs its own labeled sample and has to re-check it regularly.
- A model's "no" was much less reliable than its "yes" on new data. Checking the two sides separately
  is cheap and should be done before trusting either.
- A change of model version changes the probabilities. Pin the version (`jev-1.14.0`, not `jev-latest`)
  and re-choose the boundaries after an upgrade.

## What could be done next

1. Cross-validated analysis over all 1,123 questions (choose boundaries on some instructions, check on
   the others, in rotation), reported separately and marked as planned after the test run.
2. A separate boundary rule per side ("yes" only, or a stricter bar for "no"), checked on data the
   boundaries were not chosen on.
3. New expert-labeled data for a clean second test.

## Reproduce

```
uv sync
cp .env.example .env            # put TYPESAFE_API_KEY and OPENAI_API_KEY there; never commit .env
uv run pytest
uv run python -m jev_rubric_judge.cli prepare
uv run python runs/dev_margin.py     # the dev set table: every variant under the 94.1% and the 96% rule
uv run python -m jev_rubric_judge.cli report --part test --variants noul-fewshot \
  --thresholds '{"Jev noul-fewshot": [0.83, 0.42], "LLM judge gpt-6-luna instruction": [0.69, -0.01]}'
```

Every model answer is cached in `runs/`, so the reports above cost nothing. `run-jev` and `run-llm`
call the paid APIs only for answers that are not cached; each has a `--budget` in USD and a `--limit`
for a dry run.

| Path | What it is |
|---|---|
| `src/jev_rubric_judge/data.py` | Loads the files, parses the experts' cells |
| `src/jev_rubric_judge/split.py` | Dev/test split by instruction |
| `src/jev_rubric_judge/variants.py` | Builds the Jev request for each variant |
| `src/jev_rubric_judge/clients.py` | Jev and OpenAI clients; P(yes) from logprobs |
| `src/jev_rubric_judge/metrics.py` | Routing by boundaries, choice of boundaries, calibration error, bootstrap |
| `src/jev_rubric_judge/cost.py` | Running cost and the budget stop |
| `src/jev_rubric_judge/cli.py` | `prepare`, `run-jev`, `run-llm`, `report` |
| `data/split.json`, `data/frozen.json` | The split and the settings fixed before the test run |
| `runs/dev`, `runs/test` | Cached answers and `report.json` |
| `runs/dev_checks.py`, `runs/dev_margin.py`, `runs/test_breakdown.py`, `runs/test_extra.py` | The extra checks quoted above |

## Sources

- InFoBench paper: https://arxiv.org/abs/2401.03601 (Table 4: cost, time and agreement of experts, crowd workers and GPT-4)
- InFoBench repository and data: https://github.com/qinyiwei/InfoBench, https://huggingface.co/datasets/kqsong/InFoBench
- TypeSafe documentation: https://docs.typesafe.ai/llms.txt
- OpenAI pricing: https://developers.openai.com/api/docs/pricing
