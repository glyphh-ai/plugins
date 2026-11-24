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

Not run yet.
