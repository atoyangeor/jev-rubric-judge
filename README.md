# jev-rubric-judge

## The result, on our data

**Data:** 1,115 real yes/no quality questions about LLM-written texts from the public dataset InFoBench.
Three experts had already answered every question, so the right answer to each is known.

**What we did:** the model Jev answered first. A person answered only the questions Jev was unsure about.

**What we got:**

- **Same quality for a quarter of the price.** One expert on the unsure questions: his work cost
  **$117 and not $464**, 2.0 hours and not 7.9, with the same share of right answers (94.0% against 94.1%).
- **Closer to the three experts' answer, and still cheaper.** Three experts on the unsure questions:
  the result matches the answer of the three experts on **96.7% of the questions for $352**. One expert
  answering everything matches it on 94.1% for $464.
- **Jev itself** cost **1.6 cents** and took **72 seconds** for all 1,115 questions.

| # | Who answers the 1,115 questions | Expert answers needed | Experts' pay | Experts' time, person-hours | Model's bill | Model's time | Matches the answer of the three experts |
|---|---|---|---|---|---|---|---|
| 1 | One expert alone | 1,115 | $464 | 7.9 | no model | no model | 94.1% |
| 2 | **Jev first, one expert on the rest** | **282** | **$117** | **2.0** | $0.016 | 72 seconds | **94.0%** |
| 3 | **Jev first, three experts on the rest** | **846** (282 questions × 3) | **$352** | **6.0** | $0.016 | 72 seconds | **96.7%** |
| 4 | Jev first and stricter, three experts on the rest | 1,296 (432 questions × 3) | $539 | 9.1 | $0.016 | 72 seconds | 97.9% |
| 5 | Jev first and strictest, three experts on the rest | 1,920 (640 questions × 3) | $798 | 13.5 | $0.016 | 72 seconds | 98.7% |
| 6 | Two experts on everything, a third only where the two disagree | 2,345 | $975 | 16.5 | no model | no model | 100% by definition |
| 7 | An ordinary LLM first, one expert on the rest | 308 | $128 | 2.2 | $0.20 | 74 minutes | 94.2% |
| 8 | An ordinary LLM first, three experts on the rest | 924 (308 questions × 3) | $384 | 6.5 | $0.20 | 74 minutes | 97.0% |
| 9 | Jev alone, no expert | 0 | $0 | 0 | $0.016 | 72 seconds | 89.9% |
| 10 | An ordinary LLM alone, no expert | 0 | $0 | 0 | $0.20 | 74 minutes | 84.7% |

**In words:**

1. **Same quality, a quarter of the price** (row 2 against row 1). Jev answers what it is sure about,
   one expert answers the rest.
2. **Closer to the three experts and cheaper** (row 3 against row 1). Send the unsure questions to three
   experts and not one: the result matches the three experts' answer on 96.7% of the questions for $352,
   against 94.1% for $464 with one expert alone.
3. **You can get closer still by making Jev stricter** (rows 4 and 5). Jev then takes fewer answers and
   more questions go to the three experts: 97.9% for $539, 98.7% for $798. The cheapest way to get the
   three experts' answer on every question costs $975 (row 6), so the strictest row saves 18%.
   Read these rows with care: a question sent to the three experts counts as matched automatically,
   so part of the gain from row 3 to row 5 comes only from sending more questions to them.
4. **Making Jev stricter does not help if only one expert answers the rest.** The total stays at 94%
   whatever the setting, because one expert is himself right only 94 times out of 100. To go higher, the
   unsure questions need more than one person. That is why rows 3 to 5 use three.
5. **An ordinary LLM** (`gpt-6-luna`) does the first two jobs about as well (rows 7 and 8). It is 4 times
   more expensive and 20 times slower than Jev when asked each question once. We asked it three times
   per question (12 and 60 times), and afterwards saw that one time gives the same result. We could not
   test stricter settings for it: its sureness came back as exactly 1.000 for 716 of the 1,115 questions,
   and such answers cannot be ranked. That is a limit of how we asked, not a proven limit of the LLM.
6. **With no expert**, Jev matched the three experts on 1,002 questions and the ordinary LLM on 944 (row
   9 against row 10). Part of that gap is our rule "a number above 0.5 means yes", which does not suit
   this LLM: its numbers lean towards "no". With the cut-off tuned for each model on the tuning
   questions, the LLM gets 564 of the 644 check-1 questions and Jev 575. That gap, 2 out of 100, is too
   small for our data to confirm.
7. **Jev alone is close to one expert when the expert does not grade himself.** Take the questions where
   two experts agree and grade the third expert, Jev and the LLM against those two: the expert matches
   them on 93.3% of the questions, Jev on 92.8%, the LLM on 87.3% (with the 0.5 rule).

"100% by definition" in row 6: the right answer to a question is the answer of at least two of the three
experts, so three experts together always match it. For the same reason, in rows 3, 4, 5 and 8 every
question that goes to the three experts counts as matched; the misses in those rows are Jev's (or the
LLM's) own. These numbers say how close a process gets to the three experts' answer. Whether the three
experts themselves are right, nobody has checked.

**One thing to know before trusting this.** We checked "Jev first, one expert on the rest" twice. In the first, stricter check
Jev's answers were right 93 times out of 100 where 94 were needed. In the second check, with more data
for tuning, they passed (96 out of 100). The table above is the second check. Both checks are described
in section 8 with nothing left out; every table and the exact method are in [DETAILS.md](DETAILS.md).

Where the numbers in the table come from:

- Expert's pay and time: one expert answer costs $0.42 and takes 25 seconds (section 1); multiply by
  the number of questions the expert answers.
- Model's bill: what TypeSafe and OpenAI charged for our own run on these questions.
- Model's time: measured by us once, from one laptop. The ordinary LLM was asked every question three
  times (its sureness jumps between tries); asked once it costs $0.07 and takes 25 minutes.
- Right answers and the number of questions left to the experts: section 7 (rows 9, 10), section 8,
  check 2 (rows 2, 7), and `runs/crossval_strict.txt` (rows 3, 4, 5, 8). "Stricter" and "strictest" mean
  that the answers taken from Jev had to be right 97 and 98 times out of 100 on the tuning questions,
  where rows 2 and 3 ask for 96.

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

Here there is no person at all. The model answers all 1,115 questions.

| # | Who answers | Right answers | Cost of all 1,115 answers | Time for all 1,115 answers |
|---|---|---|---|---|
| 1 | Jev | 1,002 of 1,115 (90 out of 100) | $0.016 | 72 seconds |
| 2 | Ordinary LLM | 944 of 1,115 (85 out of 100) | $0.20 | 74 minutes |
| 3 | One expert | 94 out of 100 | $464 | 7.9 hours |

**Guess 1 is confirmed, with a caveat.** Jev is right at least as often as the ordinary LLM, costs 4 to
12 times less and is 20 to 60 times faster (the lower figures are for asking the LLM once per question,
which turned out to be enough). How much more often Jev is right depends on the cut-off: 5 out of 100
with the 0.5 rule used in this table, 2 out of 100 with a cut-off tuned for each model.

Where the numbers come from:

- 1,115 questions and not 1,123, because 8 questions were given to Jev as examples of how to answer.
- Cost: the bill for our own run on these questions. The expert: 1,115 × $0.42.
- Time: we measured it ourselves, once, from one laptop. On another day it may differ.
- We asked the ordinary LLM every question three times, because its sureness jumps from one try to the
  next. Asked once, it costs $0.07 and takes 25 minutes; then Jev is 4 times cheaper and 20 times faster.

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
alone: 94 out of 100.** This is the average. When we tuned on 40 randomly chosen tasks and checked on the
other 10, 300 times over, the answers taken from Jev fell below the bar in about 1 run out of 6.

In money and time, on our 1,115 questions: the expert answers 282 questions and not 1,115. That is $117
and not $464, and 2.0 hours and not 7.9. Jev itself adds 1.6 cents and 72 seconds.

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

- **The expert's price is an estimate** (section 1), and the saving ignores one cost: to tune Jev you
  first need about a thousand questions answered by three experts. The saving starts after that.
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
