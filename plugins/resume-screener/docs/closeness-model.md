# The closeness model

One Ada model answers one question: **is this resume (and cover letter) nearer to real people's, or to fakes?**
This page is the whole of it: what it holds, every role, how each is read, its weight and why. The machine form is
[`models/closeness.json`](../skills/screen-application/models/closeness.json); the code that reads an application
into it is [`screener/closeness.py`](../skills/screen-application/scripts/screener/closeness.py).

## What it holds

Applications, each recorded with one of two outcomes:

| Outcome | What they are | Where they come from |
|---|---|---|
| `fake` | Generated, fictional applications: a program wrote each one | Ship with the plugin: 1,980 (`models/examples/closeness.jsonl.gz`) |
| `real` | Resumes written by people | **Not shipped.** You load your own past real applicants (`seed.py --real <folder>`) |

Until you load real ones, the model can only say how close an application is to fakes.

## What goes in for one application

The resume is split into its sections by the same code the rest of the screener uses, and each section becomes its
own role. Section order, headings and layout never reach the model. Before a section's words are handed to Ada
they are neutralised, so that only words are compared:

- lower case; digits, dates, punctuation and bullets removed;
- email addresses, phone numbers and links removed;
- a resume site's stand-in words removed ("Company Name", "City", "State", "N/A", "Current", "Present");
- only the section's first words are kept (the limit is in the table), so a long section and a short one are
  compared on the same footing.

## The spec

Every text role is read as a **bag of words**: Ada compares which words two sections share, not their order.

| Layer | Role | What it is | Words kept | Weight | Why this weight |
|---|---|---|---|---|---|
| `resume` | `summary` | the summary or profile section | 80 | 1.0 | free prose: where a writer's own voice shows most |
| `resume` | `duties` | the lines of the experience section that are not a job's title line | 200 | 1.0 | the bulk of a resume; **every resume is compared on this**: a resume with no experience section read is not compared at all |
| `resume` | `titles` | the job titles held | 30 | 0.5 | short and formulaic; says more about the trade than the writer |
| `resume` | `skills` | the skills listed | 60 | 0.5 | a list of terms: mostly the trade |
| `resume` | `school` | the education section | 30 | 0.3 | a line or two of names |
| `resume` | `resume_who` | a tag: side, label, id | | 0 | never compared; it is how a nearest application is named |
| `letter` | `letter` | the cover letter | 250 | 1.0 | compared apart from the resume |
| `letter` | `letter_who` | the same tag | | 0 | never compared |
| `side` | `is` | `fake` or `real`, as recorded | | 1.0 | not part of how alike two applications are: see below |
| `who` | `source`, `label`, `id` | where it came from; what is shown for it; its id (the key) | | 0 | never compared |

Layer weights: `resume` 0.3, `letter` 0.3, `side` 1.0, `who` 0. Ada's own learning is not run on this model: the
weights are the ones written here.

**What is shown for a nearest application** is its `label`: for a fake, the generated example's made-up name and
role; for a real one, its source and category only. A real person's name or contact details are never stored in a
label and never shown.

## How it is asked

For the resume, and separately for the cover letter:

1. **The two closeness numbers.** Ada is asked for its nearest applications (`ada_facts`) twice, once naming
   `side: fake` and once `side: real`. Naming the side only puts that side's applications first; the number
   reported is the `resume` layer's own score in Ada's fact tree for the nearest one, which the side does not
   touch. So "closest fake 0.31" means: on the resume's sections alone, weighted as above, the nearest fake is 0.31
   alike, on Ada's scale from 0 (nothing shared) to 1 (the same).
2. **The answer.** The side with the higher number: "reads like the fakes" or "reads like real people"; "between
   the two" when they are within 0.02.
3. **Ada's own decision.** Ada is also asked to decide (`ada_decide`) on the resume alone: `fake` or `real`, with
   its confidence and whether it would ask a person first, and its fact tree for that decision: per layer and role,
   what this application had, what the nearest precedent had, how alike they are, and the weight. The tree is
   shown as Ada gives it.

The cover letter never moves the resume's numbers. If the model holds no real cover letters, the letter can only
be compared with fakes, and the answer says so.

## What it can and cannot tell

It measures word overlap with what it holds. The fakes come from one generator; whatever real ones you load come
from your own inbox. It can therefore tell "like the fakes it holds" from "like the real ones it holds". Whether
that is the same as "fake" and "real" is a separate question, and the check for it is in [checks.md](checks.md)
(check 4).

**The check's result, plainly: it is not the same.** With the shipped fakes and a real side taken from one resume
website, the model found every unseen fake, but a format-only control separated the two sets just as well (599 of
600), and of 18 resumes that real people published themselves, none read as real and 12 read as fakes. The model
tells "like this generator" from "like that website". It is a fair reading of "reads like the generated examples";
it is not a detector of real people. Ada's confidence was 100% on answers whose nearest precedent was only 0.2 to
0.4 alike, so the confidence should not be leaned on either.
