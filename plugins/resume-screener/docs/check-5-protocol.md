# Check 5: the agent and Ada together, on sources neither has seen

Written and committed before any run that it judges. Results are added at the end, as they come; nothing above
them is changed once a result is seen. Every look at the unseen test is counted and named there.

## Why

Check 4 failed: a model over the words of a resume told our generator from one resume website, not real people
from fakes; a layout-only control did as well, and real people from another source read as fakes. The fix tried
here is in how the two parts work together. **The agent (Claude) reads** the application and reports what a careful
person would notice, as fixed, structured facts. **Ada decides** from those facts: a weighted model, precedents,
its confidence and its fact tree, and it learns. Nothing about wording or layout reaches Ada.

## What "fake" means here, and what it does not

- **Fake:** an invented person: an application for someone who does not exist, written by an AI model or a
  program.
- **Real:** a resume a person wrote about themselves.
- **A real person's resume rewritten by AI is real.** It is tested apart ("polished"): it should read as real. If it
  does not, that is said.
- **Not covered:** a fake a person wrote by hand to deceive; a real person lying; anything about cover letters or
  emails on the real side (no human source of those is at hand).

## The data: by source, and which sources are never seen

Seen (used to design, to seed and to validate):

| Set | What | Who made it |
|---|---|---|
| `lc` | real: resumes from livecareer.com (the Kaggle "Resume Dataset") | people, 2014 to 2016 mostly |
| `gen` | fake: this plugin's own generated examples (train split; the 450 test rows stay untouched) | the corpus generator |
| `lc-fake` | fake: invented people written to look like `lc`: same categories, same section conventions, the site's stand-in words, the same length range, two real `lc` resumes shown as the form to follow | Claude Haiku 5.5, prompt A |
| `lc-polished` | real, polished: `lc` resumes rewritten by AI, facts kept | Claude Haiku 5.5, prompt P |

Never seen until the test (no design choice, no seeding, no look):

| Set | What | Who made it |
|---|---|---|
| `gh` | real: resumes their authors published on GitHub under an open licence, before November 2022 | people |
| `up` | real: a second public resume set from another site and market, if one can be verified (else said) | people |
| `lrec-real` | real: the LREC 2026 corpus's authentic resumes, if it can be obtained (non-commercial: test only) | people |
| `tpl` | fake: applications another program wrote from sentence templates | a different program |
| `gh-fake`, `up-fake` | fake: invented people written to pass as real, in the form of `gh` and of `up`: one real resume of that set shown as the form to follow, told to be as uneven and specific as a real life | Claude Opus 5.5, prompt B (a different model and a different prompt from the seen fakes) |
| `lrec-fake` | fake: the LREC corpus's AI-generated resumes, if obtained | whoever made that corpus |
| `gh-polished`, `up-polished`, `lrec-enhanced` | real, polished: unseen real resumes rewritten by AI (ours by Claude Opus 5.5, prompt Q; LREC's own AI-enhanced set) | |

Every text is brought to one plain form before anyone reads it: runs of spaces that stand for line breaks become
line breaks, and it is cut at 6,000 characters. Each text gets a random id; the id, the file name and the set's
name never reach the agent.

Sizes aimed at: seed 300 `lc` + 100 `lc-polished` as real, 200 `gen` + 200 `lc-fake` as fake; validation (same
sources, never seeded) 120 real (`lc` 80, `lc-polished` 40), 120 fake (`gen` 60, `lc-fake` 60); test: every `gh`,
up to 150 `up`, 100 `tpl`, 60 `gh-fake`, up to 120 `up-fake`, the polished sets of about 20 and 60, and the LREC
sets whole if obtained.

## The agent's reading

One fixed prompt and one fixed JSON schema for every application (`checks/facts/reading.py`), run with Claude
Sonnet 5.5. The agent is asked what it observes, never whether the person is real: how the career timeline hangs
together, how specific and how odd the claims are, how uneven the life is, how tailored and generic the writing
is, whether anything contradicts. The first version of the schema is written before any data is read; facts are
kept, dropped or reworded on the seen sets only (design on the seed sets, checked on validation), and each kept
fact is justified in the model's doc by what it did there.

## Ada

One model over the kept facts: layers by kind of observation, numeric roles for counts and scales, categories for
kinds, written weights with reasons, then Ada's own learning run on the seed. Outcomes `real` and `fake`, with an
ask-below. Closeness to each side from Ada's nearest precedents on that side.

## The headline, and the bar

**The headline is on the unseen test only: unseen real sources against unseen fake generators.**

1. **Accuracy on unseen sources:** at least 80% of unseen real (`gh`, `up`, `lrec-real` pooled, and no single real
   source under 70%) decided `real`, and at least 80% of unseen fakes (`tpl`, `gh-fake`, `up-fake`, `lrec-fake`
   pooled, none under 70%) decided `fake`. A case Ada would ask about counts by the outcome Ada gave.
2. **Same form, different truth:** within `gh` against `gh-fake`, and within `up` against `up-fake`, where the
   fakes were written in the reals' own form, the same two 70% floors hold. This is the test that it is not format.
3. **The layout-only control must fail:** an Ada model that reads only counts of the plain text (words, lines,
   word and line length, digits, capitals, commas, bullets), seeded and learned on the same seed, must be right on
   no more than 60% of the same unseen test (balanced). If it does better, format still separates the test sets and
   the headline does not count.
4. **The reading must not carry the source:** an Ada model over the agent's facts, seeded to tell `lc-fake` from
   `gen` (both fake) and `lc` from `lc-polished` (both real) on the seed, is reported on validation. This says how
   much of the source the facts still carry. Reported, with what it means; not a pass line.
5. **Polished real people:** at least 70% of `gh-polished`, `up-polished` (and `lrec-enhanced`) decided `real`.
   Reported apart; a miss is said plainly and does not change line 1.
6. **Confidence:** on the unseen test, Ada's confidence is put in bands (under 60%, 60 to 70, 70 to 80, 80 to 90,
   90 and over) and how often it was right in each band is reported. It passes if in every band with at least 30
   cases the share right is within 10 points of the band's middle. If not, the number shown is renamed for what it
   is.

Baselines on the same unseen test: the bag-of-words closeness model of check 4 seeded on the same seed; the
layout-only control; and **the agent alone** (Claude Sonnet 5.5 asked directly "real person or invented?", no
Ada). What Ada adds is the headline against the agent alone; what the agent adds is the headline against the
bag of words.

## Rules

- Ada only. No other model of any kind is fitted, in the product or in the analysis. The baselines are Ada models
  and Claude itself.
- The unseen test is run once, after the schema, the model and the ask-below are frozen and committed. If it is
  looked at again for any reason, that look is numbered and named in the results.
- Money: Claude is called through the Batches API where it can be; every call's tokens and cost go in a ledger
  (`ledger.jsonl`, local); the whole pass stops before it would pass 80 US dollars.
- Other people's resumes stay on one machine. They are sent to the Claude API for the reading (and, for the
  polished sets, the rewriting) and nowhere else; they are not committed, not uploaded and not seeded into any
  model that leaves the machine. Names and contact details are never shown.

## Results

### What was obtained (2026-11-24)

Both hoped-for sets were obtained and join the unseen test as planned: `up` (the "UpdatedResumeDataSet": 146
distinct resumes of 600 characters or more, Indian IT market, to 2019; 100 of them carry encoding damage, kept as
given) and the LREC 2026 corpus from FIU Dataverse (CC BY-NC 4.0; distinct texts: 139 authentic, 125 AI-generated
by Gemini, Meta and ChatGPT, 139 AI-enhanced). `gh` is 19 resumes. Sizes on the seen side are as aimed at.

### Design, on the seen sets only (the unseen test has not been read, by the agent or by anyone)

Claude Sonnet 5.5 read the 1,040 seen texts with the first schema (23 facts). Ada: 800 seeded (300 `lc`, 100
`lc-polished`, 200 `gen`, 200 `lc-fake`), learning run, 240 validation texts decided.

**Design run 1, all 23 facts:** real 92.5%, fake 95.0%, polished 87.5%. Ada's learning put the most weight on how
even the writing is and on slips.

**What was dropped, and why** (reasons in `checks/facts/facts_check.py`): a fact is kept only if it is about the
person and not about how the text was produced. `slips` and `evenness_of_writing` were the strongest and were
dropped: they flip when the same real person's resume is polished (slips of 2 or 3: 82% of `lc`, 23% of
`lc-polished`). `dates` and `jobs` follow how a source writes things down. `letter` is the same everywhere.
`numbers`, `round_numbers` and `stock_phrases` told nothing apart. 15 facts are kept.

**Design run 2, the 15 kept facts (frozen):**

| Validation set (never seeded) | Decided as labelled | Ada would ask |
|---|---|---|
| `lc` real, 80 | 73 (91%) | 2 |
| `lc-polished` real, 40 | 35 (87.5%) | 2 |
| `gen` fake, 60 | 56 (93%) | 3 |
| `lc-fake` fake, 60 | 57 (95%) | 4 |

What Ada's learning weighs most: one-off details (1.00), the shape of the career path (0.99), loose ends (0.87),
named things (0.80), unrelated work (0.77), how neatly it fits one role (0.73).

Beside it on the same validation texts (run 1):

| | real | fake |
|---|---|---|
| The facts model | 91% | 94% |
| Layout only | 89% | 92.5% |
| Words only (check 4's model, same seed) | 61% | 97% |
| Claude alone | 99% | 57% |

- **Layout alone still separates the seen sets.** That is expected and is not the test: the seen sources differ
  in form. The bar is on the unseen test, where the fakes were written in the reals' own form.
- **Claude alone calls most things real**: it passed 62% of our generator's fakes and 25% of the `lc`-form fakes as
  real people.
- **How much of the source the facts still carry:** told `lc` from `lc-polished` on 79 of 120 (two thirds of them
  are `lc`, so this is chance: polishing does not move the kept facts). Told `gen` from `lc-fake` on 105 of 120:
  the facts still tell our generator's examples from the other fakes, partly because the examples were rebuilt
  from parts and lost their dates.

Confidence on validation (run 2): of 189 decided at 90% or more, 97% were right; 26 at 80 to 90%, 77% right; 14 at
70 to 80%, 71% right.

None of this is the result. The result is the unseen test, run once with this design.
