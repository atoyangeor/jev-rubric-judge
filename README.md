# jev-rubric-judge

## The result, on our data

**Data:** 1,115 real yes/no quality questions about LLM-written texts from the public dataset InFoBench.
Three experts had already answered every question.

**What we did:** the model Jev answered first. A person answered only the questions Jev was unsure about.

**What we got:**

- **Money:** the expert's work cost **$117 and not $464**. That is 75% less.
- **Time:** the expert spent **2.0 hours and not 7.9**.
- **Quality: not lower, slightly higher.** 94.9% right answers with Jev first, 93.3% when the expert
  answers everything.
- **Jev itself** cost **1.6 cents** and took **72 seconds** for all 1,115 questions.

| # | Who answers the 1,115 questions | Questions the expert answers | Expert's pay | Expert's time | Model's bill | Model's time | Right answers |
|---|---|---|---|---|---|---|---|
| 1 | The expert alone | 1,115 | $464 | 7.9 hours | no model | no model | 93.3% |
| 2 | **Jev first, the expert on the rest** | **282** | **$117** | **2.0 hours** | **$0.016** | **72 seconds** | **94.9%** |
| 3 | An ordinary LLM first, the expert on the rest | 308 | $128 | 2.2 hours | $0.20 | 74 minutes | 95.1% |
| 4 | Jev alone, no expert | 0 | $0 | 0 | $0.016 | 72 seconds | 92.8% |
| 5 | An ordinary LLM alone, no expert | 0 | $0 | 0 | $0.20 | 74 minutes | 91.1% |

**In words:**

1. **Put Jev in front of the expert: you pay for a quarter of his work and the quality does not drop**
   (row 2 against row 1). It even goes up a little, by 1.6 points.
2. **Why it can go up.** On the questions Jev is sure about, Jev is right more often than a single
   person: 97.4% against 95.3%.
3. **An ordinary LLM** (`gpt-6-luna`) does the same job equally well (row 3), but costs 4 to 12 times
   more than Jev and is 20 to 60 times slower.
4. **With no expert at all**, Jev is almost at the level of one person: 92.8% against 93.3%. The
   ordinary LLM is lower: 91.1% at best.

**How "right answers" is counted.** Two of the three experts act as judges. Where the two judges agree,
their answer is the right answer. The third expert is "the person": he and the model are both graded by
the two judges. Each expert takes the role of the person in turn. Section 5 explains why.

**Three things to know before trusting this.**

1. Two decisions were made after we had seen first results: to tune on more data (section 8, check 2)
   and to grade the person and the model the same way (section 5). Both have a reason, both are
   described in full, and section 9 shows what the numbers were before each of them.
2. In our very first check, done exactly as planned in advance, Jev fell one point short of the bar:
   93 right answers out of 100 where 94 were needed.
3. The data is small: 50 tasks. Differences of 1 to 2 points are at the edge of what it can show.

Where the numbers in the table come from:

- Expert's pay and time: one expert answer costs $0.42 and takes 25 seconds (section 1); multiply by
  the number of questions the expert answers.
- Model's bill: what our own run on these questions cost at the price lists of TypeSafe and OpenAI.
- Model's time: the sum of the waiting times of all requests, measured once, from one laptop. The
  ordinary LLM was asked every question three times; we later saw that once gives the same result,
  which would be $0.07 and 25 minutes.
- Right answers: `runs/fair_yardstick.txt`. Row 5 uses the best cut-off for the LLM; with the same
  simple rule as Jev ("above 0.5 means yes") it is 87.3%.

Every table and the exact method are in [DETAILS.md](DETAILS.md).

## 1. The problem

A company builds a product in which an LLM writes texts. Someone has to check whether the texts are good.

The usual way: for every text, ask a few simple questions that can be answered "yes" or "no". An example
from our data. An LLM was asked to convert a paper citation to MLA style (one of the standard ways to
format citations). It wrote:

```
Vaswani, Ashish, et al. "Attention Is All You Need." arXiv, 2017, https://doi.org/10.48550/arXiv.1706.03762.
```

The questions about this text:

1. Is it a paper citation?
2. Does it follow MLA style?
3. Does it match the citation given in the task?

A person answers these questions. That is slow and expensive: **one answer from an expert costs $0.42
and takes 25 seconds.**

Where these two numbers come from: the authors of our dataset report that three experts spent 1,440
minutes on 1,135 questions, and price that work at $1,416 ($59 an hour, a salary figure they took from
ZipRecruiter). Divide by three experts and by 1,135 questions. So $0.42 is an estimate of what an
expert's answer costs, not an invoice.

## 2. The idea

Let a model called Jev answer first. Jev is a model by the company TypeSafe, built for one job:
answering questions about a text. An ordinary LLM, like ChatGPT, can write anything; it costs more and
answers more slowly.

The useful thing about Jev: it does not answer with the word "yes" or "no". It answers with a number
from 0 to 1 that says how sure it is that the answer is "yes":

- 0.97: almost certainly "yes";
- 0.05: almost certainly "no";
- 0.60: it is not sure.

So the rule is:

- Jev is sure: we take its answer, and the person never looks at the question.
- Jev is not sure: the person answers.

The person is left with only part of the questions.

## 3. What we wanted to find out

Three guesses, written down before any run:

1. Jev alone, with no person, answers at least as well as an ordinary LLM.
2. With Jev answering first: (a) the person is left with fewer than half of the questions; (b) the
   answers we take from Jev are right at least as often as one person's answers.
3. Jev paired with a person works at least as well as an ordinary LLM paired with a person.

## 4. What we checked it on

To check a model you need questions whose right answer is already known.

We took a public dataset called InFoBench. It has 1,135 questions like the ones above, and **three
experts have already answered every one of them.** We removed 12 questions where one expert's answer is
missing, and gave 8 to Jev as examples of how to answer. 1,115 are left.

## 5. How we decide who is right

We want to compare Jev with one person. So we need a right answer for every question, and a fair way to
grade both.

**The obvious way, and why it is unfair.** Let the three experts vote; the right answer is what at least
two of them said. Now grade one of those experts against it. His own vote is part of the right answer.
Look at a question where the other two disagree:

| Expert B | Expert C | Expert A says | The vote | Is expert A right? |
|---|---|---|---|---|
| yes | no | yes | yes (two against one) | yes |
| yes | no | no | no (two against one) | yes |

Whatever expert A says, he is right, because his vote decides. Jev has no vote, so on the same question
it can be wrong. This happens in about 1 question out of 9. Graded this way a person looks better than
he is: 94.1%.

**The fair way.** Take two experts as judges. Where the two judges agree, their answer is the right
answer. The third expert is "the person", and he had no part in it. Grade the person and Jev against the
two judges in exactly the same way. Then let each expert be the person in turn and average.

Graded this way, **one person is right 93.3 times out of 100.** That is the level to beat.

What this leaves out: the questions where the two judges disagree, about 1 in 9. There is no right
answer to grade against, so nobody is graded on them. These are the hardest questions.

## 6. What we compared Jev with

With an ordinary LLM: `gpt-6-luna` by OpenAI. It got the same questions. It can also show how sure it is
of its answer.

Why compare with it: replacing the person with an ordinary LLM is the known way to do this. The authors
of InFoBench did it with GPT-4. We need to know whether Jev gives anything beyond that.

## 7. Result 1: Jev alone against an ordinary LLM alone

Here there is no person at all. The model answers all 1,115 questions.

| # | Who answers | Right answers | Cost of all 1,115 answers | Time for all 1,115 answers |
|---|---|---|---|---|
| 1 | Jev | 92.8% | $0.016 | 72 seconds |
| 2 | Ordinary LLM | 91.1% at best | $0.20 | 74 minutes |
| 3 | One person | 93.3% | $464 | 7.9 hours |

**Guess 1 is confirmed.** Jev is right at least as often as the ordinary LLM, costs 4 to 12 times less
and is 20 to 60 times faster.

Details behind the table:

- "At best" for the LLM: a model's number has to be turned into "yes" or "no" by a cut-off. With the
  simple rule "above 0.5 means yes" Jev gets 92.8% and the LLM 87.3%. This LLM's numbers lean towards
  "no", so the simple rule is unfair to it. With the best cut-off for each model, found on other
  questions, the LLM gets 91.1% and Jev 92.2%.
- Jev against the person: 0.5 points apart. That is too small for our data to tell them apart. The LLM
  at its best is 2.2 points below the person, and that gap is confirmed.
- 4 and 20 times are for asking the LLM once per question; 12 and 60 for three times, as we ran it.
- Time was measured once, from one laptop. On another day it may differ.

## 8. Result 2: Jev first, the person on the rest

Before using the rule "Jev is sure / not sure" you have to decide what "sure" means: above which number
we take "yes", below which number we take "no". We call this tuning. You tune on questions with known
answers. Then you must check the result on **other** questions. Tuning and checking on the same
questions is like a student who has seen the exam in advance: the score comes out better than real life.

We did this twice.

### Check 1: tuned on a small part, checked on the rest

We split the questions into two piles: 479 for tuning and 644 for checking. Tuning gave this rule:
0.83 and above, take "yes"; 0.42 and below, take "no"; anything in between goes to the person.

On the 644 questions Jev was sure about 516. The person was left with 128: **20 out of 100.**

| # | What is compared, on the questions Jev was sure about | Jev | The person |
|---|---|---|---|
| 1 | Right answers | 95.4% | 94.2% |

Jev and the person together were right on 93.9% of the 644 questions; the person alone on 92.9%.

Jev is ahead by about one point in both lines. With this amount of data a one-point gap can be chance,
so the careful reading is: **Jev was not worse than the person.**

### Check 2: tuned on most of the data, checked on the rest, in turns

To give tuning more data, we did it in turns. The questions come from 50 different tasks. Tune on the
questions of 45 tasks, check on the other 5. Then take another 5 for checking, and so on, until every
question has been checked by a rule that was tuned without it.

| # | Who answers first | Questions out of 100 left to the person | Right answers on the questions taken from the model: the model | The person on those same questions | Model and person together | The person alone |
|---|---|---|---|---|---|---|
| 1 | Jev | 25 | 97.4% | 95.3% | 94.9% | 93.3% |
| 2 | Ordinary LLM | 28 | 97.6% | 95.3% | 95.1% | 93.3% |

**With Jev first, the person does a quarter of the work, and the result is right more often than the
person alone: 94.9% against 93.3%.** Here the gap, 1.6 points, is large enough to be confirmed: when we
reshuffled the tasks 2,000 times it stayed between 0.2 and 3.0 points in 95% of the reshuffles.

In money and time, on our 1,115 questions: the expert answers 282 questions and not 1,115. That is $117
and not $464, and 2.0 hours and not 7.9. Jev itself adds 1.6 cents and 72 seconds.

### What the two checks say about our guesses

| # | Guess | Check 1 | Check 2 |
|---|---|---|---|
| 2a | The person is left with fewer than half of the questions | Yes: 20 out of 100 | Yes: 25 out of 100 |
| 2b | Answers taken from Jev are right at least as often as a person's | Yes by the numbers (95.4% against 94.2%); the gap is too small to be sure | Yes, confirmed (97.4% against 95.3%) |
| 3 | Jev with a person is at least as good as an ordinary LLM with a person | The LLM pair is 0.9 points ahead (94.8% against 93.9% together with the person); the gap is too small to be sure | Equal: 94.9% and 95.1%; Jev leaves the person slightly less work and costs less |

## 9. What changed along the way, with nothing hidden

We made two decisions after seeing first results. A reader should know both, and what the numbers were
before them.

**Decision 1: tune on more data (check 2).** Check 1 was planned and saved before the 644 questions were
touched. Check 2 was added afterwards. Every question in check 2 is still judged by a rule tuned without
it, and nothing was adjusted by hand.

**Decision 2: grade the person and the model the same way (section 5).** In the first version the right
answer was the vote of all three experts, including the person being graded. An independent review of
this work pointed out that this favours the person. We changed the grading for everyone.

| # | Check | How the right answer was decided | Jev's taken answers | The level to reach | Reached? |
|---|---|---|---|---|---|
| 1 | Check 1, as first planned | Vote of three, the person's own vote included | 93.0% | 94.1% | No, one point short |
| 2 | Check 1 | Two judges, the person graded like the model | 95.4% | 94.2% | Yes by the numbers, gap too small to be sure |
| 3 | Check 2 | Vote of three, the person's own vote included | 95.6% | 95.7% | Equal |
| 4 | Check 2 | Two judges, the person graded like the model | 97.4% | 95.3% | Yes, confirmed |

"The level to reach" in rows 2 to 4 is how often one person is right on the very same questions.

A sceptic can say: you kept changing things until it worked. The honest reply: row 1 is the only result
that was fully planned in advance, and it is a miss by one point. Rows 2 to 4 each fix a specific flaw
(too little data for tuning; a grading rule that favours the person), and each flaw can be checked by
anyone with the files in this repository. A new set of questions, graded the fair way from the start,
would settle it.

## 10. If you want the answer of three experts, not one

Some teams want every answer to match what three experts would say together. Then send the questions
Jev is unsure about to three experts and not one. In this table "matches" means: equals the vote of the
three experts. A question that goes to the three experts matches automatically.

| # | Who answers the 1,115 questions | Expert answers needed | Experts' pay | Matches the vote of three experts |
|---|---|---|---|---|
| 1 | One expert alone | 1,115 | $464 | 94.1% |
| 2 | Jev first, three experts on the rest | 846 (282 questions × 3) | $352 | 96.7% |
| 3 | Jev first and stricter, three experts on the rest | 1,296 (432 questions × 3) | $539 | 97.9% |
| 4 | Jev first and strictest, three experts on the rest | 1,920 (640 questions × 3) | $798 | 98.7% |
| 5 | Two experts on everything, a third only where the two disagree | 2,345 | $975 | 100% by definition |

Read this table with care: part of the gain from row 2 to row 4 comes only from sending more questions
to the three experts, where a match is automatic. Whether the three experts themselves are right, nobody
has checked.

## 11. How far to trust all of this

- **Few questions.** 1,115 questions from 50 tasks. Gaps of one point cannot be told from chance.
- **Fair grading leaves out the hardest questions**, about 1 in 9, where the two judges disagree.
- **The expert's price is an estimate** (section 1), and the saving ignores one cost: to tune Jev you
  first need about a thousand questions answered by three experts. The saving starts after that.
- **Results vary from run to run.** Tuned on a different set of tasks, Jev's answers come out a little
  better or a little worse; check 1 and check 2 show the spread.
- **One ordinary LLM, a cheap one.** A stronger one might answer better.
- **Speed was measured once, from one laptop**, as the sum of the waiting times of all requests.
- **The texts are old.** They were written by 2023 models, in English only.

## 12. Run it yourself

```
uv sync
cp .env.example .env            # put TYPESAFE_API_KEY and OPENAI_API_KEY there; never commit .env
uv run pytest
uv run python runs/fair_yardstick.py        # the fair grading: alone, check 1, check 2
uv run python runs/crossval.py              # check 2 with the first grading
uv run python runs/crossval_strict.py       # section 10
uv run python -m jev_rubric_judge.cli report --part test --variants noul-fewshot \
  --thresholds '{"Jev noul-fewshot": [0.83, 0.42], "LLM judge gpt-6-luna instruction": [0.69, -0.01]}'   # check 1, first grading
```

Every model answer is saved in `runs/`, so these commands cost nothing. The full method, all tables, the
independent review and the list of weak points are in [DETAILS.md](DETAILS.md).

The files in `data/raw/` are a copy of part of InFoBench (Qin et al., MIT licence). The code in this
repository is under the MIT licence too (see `LICENSE`).

Sources: InFoBench paper https://arxiv.org/abs/2401.03601 (time and cost of the experts, Table 4);
data https://github.com/qinyiwei/InfoBench; Jev https://docs.typesafe.ai. Last updated 2026-11-24.
