# jev-rubric-judge: Jev as the first reader of yes/no rubric questions

[Jev](https://docs.typesafe.ai) (TypeSafe's decision model) answered 644 expert-labelled yes/no questions
about LLM responses from InFoBench. With no human it was right on 576 of them (89.4%), against 542
(84.2%) for an LLM judge reading first-token logprobs, at about 1/11 of the cost and 1/61 of the
request time. The judge is `gpt-6-luna` (OpenAI's cheap tier, reasoning off), called three times per
question; against one call the ratios are 1/3.8 and 1/20.

**The main condition written down before the runs was not met.** The condition: a human labels at most
50 questions of 100, and at least 94.1% of the answers taken from Jev are right. 94.1% is how often one
expert's answer equals the answer of at least two of the three experts, on all 1,123 questions. Result:
the human labels 19.9 questions of 100, but 480 of the 516 answers taken from Jev are right (93.0%);
486 were needed. The 95% interval is 90.6–95.1, so this test cannot tell 93.0% from 94.1%. The LLM judge
passed the bar by the number (461 of 482, 95.6%) and left more questions to the human (25.2 of 100).

| On the 644 test questions | Jev `jev-1.14.0` | LLM judge `gpt-6-luna`, three calls per question | One human expert (cost and time rescaled from the paper) |
|---|---|---|---|
| **Quality:** right with no human | 576 (89.4%) | 542 (84.2%) | 93.8% (mean of the three experts) |
| **Money:** cost of all 644 answers | $0.0096 | $0.11 | $268 = 644 × $0.4159 |
| **Speed:** seconds per question | 0.065 | 3.97 (1.32 for one call) | 25.4 |
| **With one expert on the rest:** questions per 100 left to the expert; taken answers that are right | 19.9; 480 of 516 (93.0%) | 25.2; 461 of 482 (95.6%) | 100; the expert answers everything |
| **Whole process right** (taken answers plus one expert on the rest) | 92.4% | 94.0% | 93.8% |

Notes to the table:

- "Right with no human": every answer is the model's, "yes" when the probability is above 0.5.
  The gap between Jev and the LLM judge is 5.3 points, 95% interval 1.2–9.3. Always answering "yes"
  gives 84.9% on these questions.
- The LLM judge's prompt variant was chosen for routing, not for this row. On the dev set another judge
  prompt was 2.5 points better with no human (87.9% against 85.4%; Jev 90.4%); it was not run on the
  test set. Jev's request carries eight examples; the tested judge's prompt carries the instruction.
- Jev against the LLM judge with one expert on the rest: the answers taken from Jev are right 2.6 points
  less often (interval −5.0 to −0.5); that Jev leaves fewer questions is not established (−5.3 per 100,
  interval −13.0 to 1.8).
- The expert's 93.8% flatters the expert: his own vote is one of the three that define the correct
  answer. "Whole process right" and all intervals were computed after the test run.
- Ratios: cost 0.11 / 0.0096 ≈ 11; time 3.97 / 0.065 ≈ 61; 25.4 / 0.065 ≈ 390 against the expert.
  Jev's 0.065 s is the summed request time, 41.9 s, divided by 644: Jev answers the 4.3 questions of a
  response in one request, and the median request takes 0.21 s. The LLM judge gets one call per question.
- The expert's cost and time come from the InFoBench paper: $1,416 and 1,440 minutes for three experts
  on 1,135 questions, so $0.4159 and 25.4 s per answer.
- Timings are from one laptop on one day. They are not a benchmark.

**Money on the test set.** With Jev first, the expert labels 19.9 of 100 questions: $8.27 instead of
$41.59 per 100 questions. The price is quality: the whole process is right on 92.4% of the questions
against 93.8% for one expert alone.

**Not a clean test, computed after the test run.** In cross-validation over all 50 instructions (1,115
questions) Jev left 25.4 questions per 100 to a human with 95.6% of the taken answers right; the LLM
judge left 27.5 with 95.8%; the difference between them was not tested. With boundaries tuned to 94.1%,
as first designed, Jev met the bar in 0 of 20 cuts. The same 96% rule gave 93.0% on the real test.

Status: test set run once on 2026-11-24. Last updated 2026-11-24.

## Words used below

| Word | Meaning |
|---|---|
| InFoBench | Public dataset (arXiv 2401.03601). LLMs were given instructions; people checked each LLM response against a list of yes/no questions |
| Response | The text one of five LLMs (`gpt-3.5-turbo`, `gpt-4`, `claude-v1`, `alpaca-7b`, `vicuna-13b`) wrote for an instruction. It is the thing being checked |
| Question | One yes/no question about one response. The unit of every count in this file |
| Correct answer | The answer at least two of the three experts gave |
| Jev | TypeSafe's decision model. For a yes/no question (its question type `noul`) it returns a number from 0 to 1: the probability that the answer is yes |
| LLM judge | A general LLM asked the same question. Here `gpt-6-luna` (OpenAI), reasoning off |
| Boundaries `t_yes`, `t_no` | Two numbers. Probability of yes at or above `t_yes`: take "yes" from the model. At or below `t_no`: take "no". In between: a human labels the question |
| Taken answers | The answers taken from the model under the boundaries. The other questions are "left to a human" |
| Dev set, test set | Two parts of the data, split by instruction. Settings are chosen on the dev set; the result is computed once on the test set |
| Right with no human | Every answer is taken from the model: "yes" when the probability is above 0.5, otherwise "no" |
| One expert's level, 94.1% | The share of all 1,123 questions on which one expert's answer equals the correct answer, mean of the three experts. The quality bar |
| Request variant | One way of building the request to a model. Jev `noul-fewshot`: the request also holds eight judged questions as examples. "LLM judge with the instruction": the prompt also holds the original instruction. All variants are listed under Method |
| Takes no "no" | No boundary for "no" was safe enough on the dev set, so every "no" of that model goes to a human |
| 96% rule | Boundaries are chosen on the dev set so that at least 96% of the taken answers are right there; the reason for the margin over 94.1% is under Method |
| Cross-validation | The instructions are cut into ten parts; boundaries are chosen on nine and applied to the tenth, in rotation, so every question is judged with boundaries chosen without it |

## The idea

A team that checks its LLM with rubric questions pays a person for every answer. Suppose instead a
model answers first and says how sure it is. Answers it is sure of are taken as they are; the rest go
to the person. The useful number is how many questions the person still has to label, on the condition
that the answers taken from the model are not worse than the person's own.

Three experts are **not** replaced. Their answers define the correct answer. What the model replaces is
part of the work of **one** labeler, and the quality bar is the level of one expert measured against
the answer of two of three.

## The test result

644 questions, 30 instructions, one run, settings frozen beforehand (`data/frozen.json`, commit `11f0f23`).
In brackets: 95% bootstrap intervals, the 30 test instructions resampled with replacement 2,000 times.

| # | Model | Right with no human | Questions per 100 left to a human | Taken answers that are right | At least 94.1% of the taken answers right? |
|---|---|---|---|---|---|
| 1 | Jev `noul-fewshot`, `t_yes` 0.83, `t_no` 0.42 | 576 of 644, 89.4% (86.6–91.8) | 19.9: 128 of 644 (15.4–24.8) | 480 of 516, 93.0% (90.6–95.1) | **No**: 486 of 516 were needed; the interval also contains 94.1 |
| 2 | LLM judge with the instruction, `t_yes` 0.69, takes no "no" | 542 of 644, 84.2% (80.4–88.0) | 25.2: 162 of 644 (18.8–31.4) | 461 of 482, 95.6% (93.5–97.6) | Yes by the number (454 of 482 were needed); the interval also contains 94.1 |

"Right with no human": probability above 0.5 counts as "yes", otherwise "no".

One real example from the test set (shown in full under Data), as it went through the run:

| Question | Correct answer | Jev's probability of yes | What happens with Jev's answer | LLM judge's probability of yes | What happens with the LLM judge's answer |
|---|---|---|---|---|---|
| Is the generated text a paper citation? | yes | 0.97 | "yes" is taken; it is right | 1.00 | "yes" is taken; it is right |
| Does the generated text comply with the requested citation style (MLA citation style)? | yes | 0.68 | goes to a human | 1.00 | "yes" is taken; it is right |
| Does the generated paper citation match the citation in the given input? | yes | 0.40 | "no" is taken; it is **wrong** | 0.63 | goes to a human |

Jev against the LLM judge on the same resampled instructions (paired bootstrap, 2,000 resamples):

| What is compared | Jev minus LLM judge | 95% interval | Reading |
|---|---|---|---|
| Right with no human, points | +5.3 | 1.2 to 9.3 | Does not contain 0: Jev alone is right more often |
| Questions per 100 left to a human | −5.3 | −13.0 to 1.8 | Contains 0: that Jev leaves fewer questions is not established |
| Share of taken answers that are right, points | −2.6 | −5.0 to −0.5 | Does not contain 0: the answers taken from Jev are right less often |

The three success conditions written down before the runs:

| # | Condition | Outcome |
|---|---|---|
| 1 | A human labels at most 50 questions of 100, and at least 94.1% of the answers taken from Jev are right | **Not met**: 19.9 of 100, but 93.0% |
| 2 | Jev alone is right at least as often as crowd workers in the paper (84%) | Met: 89.4%. Always answering "yes" already gives 84.9% on the test set, so this bar is low |
| 3 | Jev's probability is not worse for this purpose than the LLM's logprobs | **Not met as measured.** Jev left 19.9 questions per 100 against 25.2, a difference that is not established (interval −13.0 to 1.8), and Jev's taken answers were below 94.1% (93.0%) while the LLM judge's were above (95.6%) |

## After the test run

Everything in this section was computed after the test set had been seen. It explains the result and
points to the next test. It is not a result itself. Scripts: `runs/test_breakdown.py`,
`runs/test_extra.py`, `runs/explore_after_test.py`.

### Where Jev lost the 1.1 points: its "no" answers

| Answers taken from Jev | Dev set | Test set |
|---|---|---|
| "yes" | 319 of 333 right (95.8%) | 433 of 450 right (96.2%) |
| "no" | 51 of 52 right (98.1%) | 47 of 66 right (71.2%) |

The boundary for "no" (0.42) looked safe on the dev set and did not hold on the test set. The LLM judge
met the condition because it took no "no" answers at all. Of the 36 wrong answers taken from Jev, 22 are
on questions where the experts themselves disagreed.

### What other boundaries would have given on the test set

| `t_yes` | `t_no` | Questions per 100 left to a human | Taken answers that are right |
|---|---|---|---|
| 0.83 | 0.42 (the frozen pair) | 19.9 | 480 of 516 (93.0%) |
| 0.83 | 0.30 | 23.0 | 469 of 496 (94.6%) |
| 0.83 | 0.10 | 26.2 | 456 of 475 (96.0%) |
| 0.83 | no "no" taken | 30.1 | 433 of 450 (96.2%) |
| 0.90 | 0.42 | 30.7 | 415 of 446 (93.0%) |

A stricter boundary for "no" reaches 94.1%; a stricter boundary for "yes" does not. None of these pairs
can be claimed: they are chosen with the test answers in view.

### Cross-validation over all 50 instructions

1,115 questions (the 1,123 minus the eight few-shot examples). Boundaries are chosen on 45 instructions
under the 96% rule and applied to the other 5, in rotation; repeated for 20 random cuts.

| Model | Questions per 100 left to a human (range over the 20 cuts) | Taken answers that are right (range) | Cuts of 20 with at least 94.1% |
|---|---|---|---|
| Jev `noul-fewshot` | 25.4 (24.2–26.5) | 95.6% (94.9–96.0) | 20 |
| LLM judge with the instruction | 27.5 (27.1–27.9) | 95.8% (95.6–96.1) | 20 |

With boundaries tuned to exactly 94.1% instead of 96%, Jev left 13.1 per 100 with 93.7% right and met
94.1% in 0 of 20 cuts; the LLM judge left 25.8 with 95.5% right, 20 of 20.

Why this is not a pass: the 20 cuts reuse the same 50 instructions; the request variant and the eight
examples were chosen on the dev instructions, which are part of them; and the same 96% rule gave 93.0%
on the real test. It is a reason for a second clean test.

With no human, on all 1,115 questions: Jev 1,002 right (89.9%), LLM judge 944 (84.7%), difference 5.2
points, interval 2.1–8.3.

### How one expert does on the same questions

The 94.1% bar is one expert's level on all questions. The questions a model is sure of are the easier
ones, and experts are right on them more often too:

| Test set questions, Jev first | How many | One expert right (mean of three) | Jev right |
|---|---|---|---|
| All | 644 | 93.8% | 89.4% |
| Taken from Jev | 516 | 94.8% | 93.0% |
| Left to a human | 128 | 89.8% | 96 of 128 (75.0%) with no human; here a human answers |

| Test set questions, LLM judge first | How many | One expert right (mean of three) | LLM judge right |
|---|---|---|---|
| All | 644 | 93.8% | 84.2% |
| Taken from the LLM judge | 482 | 95.3% | 95.6% |
| Left to a human | 162 | 89.3% | 81 of 162 (50.0%) with no human; here a human answers |

On the questions it took, Jev is 1.8 points below one expert and the LLM judge is level with one. The
questions left to the human are the ones where a single expert is right only about 9 times in 10.

The whole process on the 644 questions, the model's taken answers plus one expert on the rest, computed
with each of the three experts in turn:

| Process | Right with expert 1, 2, 3 on the rest | Mean |
|---|---|---|
| Jev, then one expert | 92.1%, 92.9%, 92.2% | 92.4% |
| LLM judge, then one expert | 93.2%, 94.3%, 94.7% | 94.0% |
| One expert alone | 94.4%, 94.7%, 92.2% | 93.8% |

## Data

Files in `data/raw/`, copied from the authors' public folder
(https://github.com/qinyiwei/InfoBench, `expert_annotation/`) and from
https://huggingface.co/datasets/kqsong/InFoBench:

| File | What one row is | Rows used |
|---|---|---|
| `expert_easy.csv`, `expert_hard.csv` | One instruction: its `input`, five responses, and for each response the answers of three experts to every question. "Easy" and "hard" are the authors' names for their two sets of instructions | 25 + 25 instructions |
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
instruction stay in one part, so the test never contains questions that resemble the ones the settings
were chosen on.

## Method, step by step

1. **Load** the three files into one table: one row per question about one response (`data.py`).
2. **Correct answer** = the answer of at least two of three experts.
3. **Split** into dev set and test set by instruction (`split.py`).
4. **Ask Jev** (`jev-1.14.0`): one request per response, carrying the `input`, the response and all its
   questions. Jev returns one probability per question. Four request variants were tried on the dev set:

   | Variant | What the request holds besides `input`, response and questions |
   |---|---|
   | `noul-plain` | Nothing |
   | `noul-criteria` | A rule for what counts as yes and as no |
   | `noul-instruction` | The original instruction |
   | `noul-fewshot` | Eight dev set questions with their correct answers as examples (`data/fewshot_examples.json`); the same eight go into the test requests |

5. **Ask the LLM judge** (`gpt-6-luna`): one call per question, with the judge prompt from the InFoBench
   repository (`evaluation.py`) plus "Answer with one word: YES or NO." The probability of yes is
   P(yes) / (P(yes) + P(no)) over the first token's logprobs. Every question is asked three times and
   the mean is used, because the probability changes between identical calls (on the dev set the three
   repeats differ by 0.10 or more on 30 of 479 questions for the authors' prompt). Three variants: the authors' prompt as is,
   with the original instruction, with the same eight examples.
6. **Choose the variant and the boundaries on the dev set.** For every pair of boundaries on a 0.01
   grid: keep the pairs under which at least 96% of the taken answers are right, and among them take the
   pair that leaves the fewest questions to a human. Per model, the variant with the fewest questions
   left goes to the test set.
7. **Freeze.** The chosen variants and boundaries are written to `data/frozen.json` and committed
   before any model saw the test set.
8. **Run the test set once.**

Why 96% on the dev set when the condition is 94.1%: the 20 dev instructions were cut in half at random
200 times; boundaries tuned to exactly 94.1% on one half reached 94.1% on the other half in only 90 of
the 200 cuts (Jev `noul-fewshot`); tuned to 96%, in 135 of 200. This margin was added after the first
dev set results and before the test run. It is a change from the original design, which tuned to 94.1%.

Dev set results. Settings were chosen here, so these numbers are optimistic. All rows use the same 471
questions: 8 of the 479 are the few-shot examples.

| # | Model and variant | Right with no human | `t_yes` / `t_no` | Questions per 100 left to a human | Taken answers that are right |
|---|---|---|---|---|---|
| 1 | Jev `noul-fewshot` | 426 of 471 (90.4%) | 0.83 / 0.42 | 18.3 | 370 of 385 (96.1%) |
| 2 | Jev `noul-instruction` | 427 of 471 (90.7%) | 0.81 / 0.21 | 18.7 | 368 of 383 (96.1%) |
| 3 | Jev `noul-plain` | 416 of 471 (88.3%) | 0.91 / 0.34 | 28.2 | 325 of 338 (96.2%) |
| 4 | Jev `noul-criteria` | 411 of 471 (87.3%) | 0.86 / 0.24 | 33.3 | 302 of 314 (96.2%) |
| 5 | LLM judge, with instruction | 402 of 471 (85.4%) | 0.69 / takes no "no" | 29.3 | 321 of 333 (96.4%) |
| 6 | LLM judge, authors' prompt | 414 of 471 (87.9%) | 0.91 / takes no "no" | 29.9 | 317 of 330 (96.1%) |
| 7 | LLM judge, with examples | 411 of 471 (87.3%) | 0.85 / takes no "no" | 30.4 | 315 of 328 (96.0%) |

"Takes no no": no boundary for "no" kept the taken answers at 96%, so every "no" of the LLM judge goes
to a human. Rows 1 and 5 went to the test set. The rule "questions of category `Number` go straight to
a human" was tried and dropped: with it more questions were left to a human for every variant.

How the columns are computed, on seven real dev set questions with Jev's probabilities
(0.99, 0.99, 0.88, 0.80, 0.56, 0.22, 0.05; correct answers yes, yes, yes, no, yes, no, no):

- *Right with no human.* Above 0.5 means "yes": the first five are answered "yes", the last two "no".
  The fourth is wrong (0.80, correct answer "no"). 6 of 7 right.
- *Boundaries 0.83 and 0.42.* The first three are at or above 0.83: "yes" is taken. The last two are at
  or below 0.42: "no" is taken. The fourth and fifth (0.80, 0.56) are in between: a human labels them.
- *Left to a human:* 2 of 7. *Taken answers that are right:* 5 of 5.
- Lower `t_yes` to 0.80 and the fourth question is taken as "yes", which is wrong: 1 of 7 left to a
  human, 5 of 6 taken answers right. Wider boundaries mean less work for the human and more errors.

## Compared with what the dataset and the paper already had

Rows 1, 3 and 4 are the paper's numbers (Table 4), measured on all 1,135 questions and not recomputed
here. Row 2 is computed here from the experts' answers. Rows 5–7 are this run, on the 644 test
questions. The two groups are on different questions, so the comparison across them is rough: in the
test set the correct answer is "yes" more often (84.9% against 82.7% overall), Jev's request carries
eight examples, and GPT-4 in the paper answered all questions of a response in one conversation at 2023
prices.

| # | Way of checking | Questions | Right answers | Cost per 100 questions |
|---|---|---|---|---|
| 1 | Three experts | 1,135 | Define the correct answer | $124.76 |
| 2 | One expert | 1,123 | 94.1% | $41.59 |
| 3 | Crowd workers (three per task) | 1,135 | 84% | $16.52 |
| 4 | GPT-4 (`gpt-4-0314`) | 1,135 | 89% | $1.71 |
| 5 | Always answer "yes" | 644 | 84.9% | $0 |
| 6 | Jev alone | 644 | 89.4% | $0.0015 |
| 7 | LLM judge alone, three calls per question | 644 | 84.2% | $0.017 |

A model with one expert on the rest, test set:

| # | Way of checking | Answers taken from the model | Of them right | Questions left to the expert | Expert's cost per 100 questions |
|---|---|---|---|---|---|
| 1 | Jev, then one expert | 516 | 480 (93.0%) | 128 | $8.27 instead of $41.59 |
| 2 | LLM judge, then one expert | 482 | 461 (95.6%) | 162 | $10.46 instead of $41.59 |

Cost per 100 questions is the paper's total divided by 1,135 and multiplied by 100; for one expert,
$1,416 / 3 / 1,135 = $0.4159 per answer.

## Cost and speed details

- Whole experiment: about $0.51 (Jev $0.03, OpenAI $0.48), measured from the `usage` field of every response.
- Jev: $0.042 per million input tokens (docs.typesafe.ai, read 2026-11-22). Test set: 149 requests,
  227,787 input tokens, $0.0096. The requests took 41.9 s in total, 0.065 s per question; the median
  request took 0.21 s. Four requests ran in parallel.
- `gpt-6-luna`: $0.10 per million input and $0.50 per million output tokens (OpenAI pricing page,
  "Standard", read 2026-11-24). Test set: 1,932 calls, 1,074,519 input tokens, $0.11; mean 1.32 s and
  median 0.92 s per call. Eight calls ran in parallel.

## Weak points and risks

1. **Small data.** 50 instructions in total, 30 in the test set. Questions about one instruction
   resemble each other, so 644 questions carry less information than 644 independent ones.
2. **The test set is spent.** Any further tuning on these 50 instructions is no longer a clean test.
3. **The selection rule was changed once**, from 94.1% to 96% on the dev set, after dev results and
   before the test run.
4. **The 94.1% bar favours the expert.** An expert's own vote is one of the three that define the
   correct answer: he needs one of the other two to agree. A model needs two of three.
5. **The experts are a ceiling.** When two experts are wrong and the model is right, the model is
   counted wrong.
6. **"One labeler" is an assumption.** The savings are counted against one expert labeling everything.
   A team that puts three people on every question needs a different comparison, and for it 94.1% would
   be too low a bar.
7. **The LLM judge variant was chosen for routing, not for accuracy alone.** Its 84.2% with no human is
   below always answering "yes" (84.9%). On the dev set the authors' prompt was better with no human
   (87.9% against 85.4%, and against Jev's 90.4%); it was not run on the test set.
8. **One LLM judge, cheap tier, reasoning off, one-word answer.** A stronger model, reasoning, or a
   different way of getting a probability may do better. The comparison says nothing about them.
9. **Only yes and no.** InFoBench has no "not applicable" or "can't tell" labels, so those answers are
   not tested.
10. **Old responses, English only.** The responses were written by 2023 models.
11. **Boundaries drift.** On unseen instructions the share of right taken answers fell from 96.1% to
    93.0%. A team using this needs its own labeled sample and has to re-check it regularly, with "yes"
    and "no" checked separately.
12. **A new model version changes the probabilities.** Pin the version (`jev-1.14.0`, not `jev-latest`)
    and choose the boundaries again after an upgrade.

## Next

1. A separate boundary rule per side ("yes" only, or a stricter bar for "no"), checked on data the
   boundaries were not chosen on.
2. New expert-labeled data for a clean second test.

## Reproduce

```
uv sync
cp .env.example .env            # put TYPESAFE_API_KEY and OPENAI_API_KEY there; never commit .env
uv run pytest
uv run python -m jev_rubric_judge.cli prepare
uv run python runs/dev_margin.py     # the dev set table: every variant under the 94.1% and the 96% rule
uv run python -m jev_rubric_judge.cli report --part test --variants noul-fewshot \
  --thresholds '{"Jev noul-fewshot": [0.83, 0.42], "LLM judge gpt-6-luna instruction": [0.69, -0.01]}'
uv run python runs/test_extra.py            # paired comparison, the expert on the same questions
uv run python runs/explore_after_test.py    # other boundaries, cross-validation, seconds per question
```

Every model answer is cached in `runs/`, so the commands above cost nothing. `run-jev` and `run-llm`
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
| `runs/dev`, `runs/test` | Cached answers and `report.json`. `runs/dev/report.json` is the first dev report, under the 94.1% rule; the dev table above comes from `runs/dev_margin.txt` |
| `runs/dev_margin.py`, `runs/dev_checks.py` | Dev set: every variant under both rules, the `Number` rule, boundaries checked on unseen halves. Output in `runs/dev_margin.txt` |
| `runs/test_breakdown.py`, `runs/test_extra.py`, `runs/explore_after_test.py` | Checks made after the test run; their output is saved next to them as `.txt` |

## Sources

- InFoBench paper: https://arxiv.org/abs/2401.03601 (Table 4: cost, time and agreement of experts, crowd workers and GPT-4)
- InFoBench repository and data: https://github.com/qinyiwei/InfoBench, https://huggingface.co/datasets/kqsong/InFoBench
- TypeSafe documentation: https://docs.typesafe.ai/llms.txt
- OpenAI pricing: https://developers.openai.com/api/docs/pricing
