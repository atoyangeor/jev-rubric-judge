# jev-rubric-judge

**In one sentence:** when the model Jev answers yes/no quality questions first and a person answers only
the ones Jev is unsure about, the result is as accurate as the person working alone (94 right answers
out of 100), the person does a quarter of the work, and Jev costs 11 times less and answers 60 times
faster than an ordinary LLM doing the same job.

One thing to know before trusting that sentence: we checked it twice. The first check missed the
accuracy bar by one point (93 out of 100 instead of 94). The second check, on more data, met it. Both
are described below, with nothing left out. Every table and the exact method are in [DETAILS.md](DETAILS.md).

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

Where these two numbers come from: the authors of our dataset paid three experts $1,416 for 1,135
questions, and the experts spent 1,440 minutes. Divide by three experts and by 1,135 questions.

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
missing. 1,123 are left.

**The right answer** to a question is the one at least two of the three experts gave. Three are needed
because one person can make a mistake, and two rarely make the same one.

## 5. What "as good as a person" means

We need one number: how often is one person right?

Take each of the three experts separately and count how often his answer equals the right answer:
95, 94 and 93 questions out of 100. **On average 94 out of 100.**

That is the bar for Jev. The answers we take from Jev must be right at least 94 times out of 100. Then
Jev makes mistakes no more often than a person does.

## 6. What we compared Jev with

With an ordinary LLM: `gpt-6-luna` by OpenAI. It got the same questions. It can also show how sure it is
of its answer.

Why compare with it: replacing the person with an ordinary LLM is the known way to do this. The authors
of InFoBench did it with GPT-4. We need to know whether Jev gives anything beyond that.

## 7. Result 1: Jev alone against an ordinary LLM alone

Here there is no person at all. The model answers every question. Numbers are for 1,000 questions.

| # | Who answers | Right answers out of 100 | Cost of 1,000 answers | Time for 1,000 answers |
|---|---|---|---|---|
| 1 | Jev | 90 | $0.015 | 65 seconds |
| 2 | Ordinary LLM | 85 | $0.17 | 66 minutes |
| 3 | One expert | 94 | $416 | 7 hours |

**Guess 1 is confirmed.** Jev is right more often than the ordinary LLM, costs 11 times less and is 60
times faster. Neither reaches the expert when working alone.

Where the numbers come from:

- Right answers: all 1,115 questions we could use. Jev was right on 1,002, the ordinary LLM on 944.
  (1,115 and not 1,123, because 8 questions were given to Jev as examples of how to answer.)
- Cost: the bill for our own run, scaled to 1,000 questions. The expert: 1,000 × $0.42.
- Time: we measured it ourselves, once, from one laptop. On another day it may differ.
- We asked the ordinary LLM every question three times, because its sureness jumps from one try to the
  next. Asked once, it costs $0.06 and takes 22 minutes; then Jev is 4 times cheaper and 20 times faster.

## 8. Result 2: Jev first, the person on the rest

Before using the rule "Jev is sure / not sure" you have to decide what "sure" means: above which number
we take "yes", below which number we take "no". We call this tuning. You tune on questions with known
answers. Then you must check the result on **other** questions. Tuning and checking on the same
questions is like a student who has seen the exam in advance: the score comes out better than real life.

We did this twice.

### Check 1: tuned on a small part, checked on the rest. Missed by one point

We split the questions into two piles: 479 for tuning and 644 for checking. Tuning gave this rule:
0.83 and above, take "yes"; 0.42 and below, take "no"; anything in between goes to the person.

On the 644 questions:

- Jev was sure about 516. The person was left with 128. That is **20 out of 100**: five times less work.
- Of Jev's 516 answers, 480 were right. That is **93 out of 100**.
- The bar is 94 out of 100, which is 486 right answers. **Jev was 6 answers short.**

The ordinary LLM in the same role left the person 25 questions out of 100 and passed the bar: 461 right
answers out of 482, which is 96 out of 100.

Why Jev fell short. Its "yes" answers were fine: 433 right out of 450. Its "no" answers were not: only
47 right out of 66. On the 479 tuning questions its "no" answers had been right 51 times out of 52, so
tuning decided to trust them. The tuning pile was too small to show the problem.

### Check 2: tuned on most of the data, checked on the rest, in turns. Passed

To give tuning more data, we did it in turns. The questions come from 50 different tasks. Tune on the
questions of 45 tasks, check on the other 5. Then take another 5 for checking, and so on, until every
question has been checked by a rule that was tuned without it. Then repeat the whole thing 20 times
with a different split and average.

| # | Who answers first | Questions out of 100 left to the person | Right answers out of 100 among those taken from the model | The bar: 94 | Right answers out of 100 for model and person together |
|---|---|---|---|---|---|
| 1 | Jev | 25 | 96 | passed | 94 |
| 2 | Ordinary LLM | 28 | 96 | passed | 94 |
| 3 | The person alone | 100 | the person answers everything | no model | 94 |

**With Jev first, the person does a quarter of the work, and the result is as accurate as the person
alone: 94 out of 100.**

In money and time, for 1,000 questions: the expert answers 253 questions and not 1,000. That is $105
and not $416, and 1.8 hours and not 7. Jev itself adds $0.015 and about a minute.

Exact figures behind the table: Jev's taken answers were right 95.6% of the time, the ordinary LLM's
95.8%; together with the person 94.0% and 94.2%; the person alone 94.1%.

### What the two checks say about our guesses

| # | Guess | Check 1 | Check 2 |
|---|---|---|---|
| 2a | The person is left with fewer than half of the questions | Yes: 20 out of 100 | Yes: 25 out of 100 |
| 2b | Answers taken from Jev are right at least as often as a person's (94 out of 100) | No: 93 | Yes: 96 |
| 3 | Jev with a person is at least as good as an ordinary LLM with a person | No: only the LLM passed the bar | Yes: both passed, and Jev left the person slightly less work |

## 9. Which check to believe

Both are true, and they answer slightly different questions.

- **Check 1 is the strict one.** Its plan was written down and saved before the 644 questions were
  touched. Nobody could adjust anything after seeing the answers. It shows what happens when you tune on
  very little data: the rule can come out too loose, and you miss the bar.
- **Check 2 uses more data for tuning, and that fixed the problem.** But we came up with it after seeing
  the result of check 1. A sceptic can say: you kept trying until it worked. The honest reply: every
  question in check 2 was still judged by a rule tuned without it, and nothing was fitted by hand.
  A third check on fresh questions would settle it.

Practical takeaway: tune on as many labeled questions as you can, and check "yes" and "no" answers
separately before trusting either.

## 10. How far to trust all of this

- **Few questions.** 1,123 questions from 50 tasks. The gap between 93 and 94 out of 100 in check 1 is
  6 answers. On another set of questions it could go either way.
- **One ordinary LLM, a cheap one.** A stronger one might answer better.
- **Speed was measured once, from one laptop.**
- **The texts are old.** They were written by 2023 models, in English only.
- **Three people per question are the yardstick.** If two of them are wrong and the model is right, we
  count the model as wrong.

## 11. Run it yourself

```
uv sync
cp .env.example .env            # put TYPESAFE_API_KEY and OPENAI_API_KEY there; never commit .env
uv run pytest
uv run python runs/crossval.py              # check 2
uv run python -m jev_rubric_judge.cli report --part test --variants noul-fewshot \
  --thresholds '{"Jev noul-fewshot": [0.83, 0.42], "LLM judge gpt-6-luna instruction": [0.69, -0.01]}'   # check 1
```

Every model answer is saved in `runs/`, so these commands cost nothing. The full method, all tables and
the list of weak points are in [DETAILS.md](DETAILS.md).

Sources: InFoBench paper https://arxiv.org/abs/2401.03601 (costs and time of the experts, Table 4);
data https://github.com/qinyiwei/InfoBench; Jev https://docs.typesafe.ai. Last updated 2026-11-24.
