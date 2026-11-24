---
name: screen-application
description: Check a resume and cover letter against the person's own Ada model - how close they are to real people's and how close to fakes - and, when asked for more, screen the whole application (the email's timestamps, the files themselves, the applications screened before, Greenhouse signals, the fit for the role). Use when the person asks to check, screen or vet a resume, a cover letter, a job application or an applicant's email, asks whether an applicant is real or fake, or asks to set up or seed the Resume Screener.
---

# Check a resume and cover letter

**This is the main path. Use it unless the person asks for the whole application to be screened.**

One thing in, one thing out: a resume and a cover letter (either may be missing) in; how close they are to real
people's and how close to fakes out. You judge nothing yourself: code reads the files, the person's `closeness`
Ada model answers.

```
pip install glyphh pypdf          # once
glyphh login                      # once; or set GLYPHH_API_KEY
python scripts/check.py --resume resume.pdf --letter cover_letter.docx
```

(Files given without `--resume` / `--letter` are told apart by the script.) If it says the model is missing, set
the screener up first (below). It prints, for the resume and for the cover letter apart:

- `fake` and `real`: the closeness of the nearest one on each side, from 0 (nothing shared) to 1 (the same), and
  the nearest few. A fake is named by its generated example's made-up name and role; a real one only by its source
  and category.
- `reads`: "reads like the fakes", "reads like real people" or "between the two".
- `decision`: Ada's own answer, `fake` or `real`, with its confidence, whether it would ask a person first, and
  its fact tree.

Tell the person, in this order: what it reads like, with the two numbers ("closest fake 0.91, closest real 0.62:
reads like the fakes"); Ada's decision and confidence; the nearest few on each side; then, if they want it, the
fact tree as Ada gave it (each layer and role, what this application had, what the nearest had, how alike, and the
weight). If the connector has the tool `screener_closeness`, call it with exactly what the script printed: it
shows the same as a card.

Say plainly, every time it applies:

- If `real` has no closeness, the model holds no real resumes yet: it can only say how close this is to fakes.
  The real side is the person's own past real applicants, loaded with `python scripts/seed.py --real <folder>`.
- The cover letter is compared apart and never moves the resume's numbers.
- This is how alike the words are to what the model holds. It is not proof that anyone is real or fake; what was
  and was not shown is in `docs/checks.md` (check 4) and the model itself is in `docs/closeness-model.md`.

# Screen the whole application

Only when the person asks for more than the resume and cover letter. You run fixed steps, in a fixed order. Code
reads and measures the application; Ada models decide; the person is asked when Ada is unsure, and their answer
becomes a precedent. You never judge the application yourself and you never change a case before it is decided.

## What you need

- The Glyphh connector's `ada_*` tools. If they are not there, use `scripts/run.py` instead (it asks Ada through
  the Glyphh SDK with the person's own key: `pip install glyphh pypdf`, then `glyphh login`), and tell the person
  that is what you did.
- Python 3.11 or later with `pypdf` (`pip install pypdf`) to read PDF files.
- The scripts are in this skill's folder: `${CLAUDE_PLUGIN_ROOT}/skills/screen-application/scripts`.

## Before the first screening: the models

The screener's seven models are named `screener-closeness`, `screener-fit`, `screener-files`, `screener-timing`,
`screener-others`, `screener-made` and `screener-greenhouse` (`ada_models` lists them). If any is missing, set the
screener up:

```
pip install glyphh pypdf
glyphh login          # once; or set GLYPHH_API_KEY
python scripts/seed.py
python scripts/seed.py --real <folder>    # the person's own past real applicants' resumes, when they have them
```

It makes the models in the person's own account and loads the examples that ship with the plugin: 1,980
generated, fictional applications, into `screener-closeness` as fakes and into `screener-fit` and `screener-made`
with their labels, and runs Ada's learning on those two. `--real` loads the person's own resumes into
`screener-closeness` as the real side; nothing of who the people are is kept, only the words of their resumes'
sections. It takes a few minutes and can be run again safely. `screener-others` starts empty and holds only the
applications the person screens; `screener-files`, `screener-timing` and `screener-greenhouse` start empty and
learn from the person alone. Tell the person what it did.

## The steps

Use one new empty work folder per application (for example `mktemp -d`).

**1. Read.** Get the application as files on disk: the email as an `.eml` file when you can (it carries the
timestamps), else its words in a text file, with the headers above them if the person has them; and the resume and
cover letter (PDF or DOCX), in any order.

```
python scripts/screen.py read --work <dir> --eml application.eml
python scripts/screen.py read --work <dir> --email email.txt --file resume.pdf --file cover_letter.docx --role "Backend Engineer"
```

If it prints `refused`, stop: tell the person why (for example, the sender's domain did not vouch for the
message). Otherwise it prints `asks`.

**2. Ask Ada which applications it holds are nearest.** For each of `asks`, call `ada_facts` with `name`
(`screener-others`), `data` and `top` exactly as given. Write the answers to a file as
`{"<part>": <the tool's answer>, ...}`.

**3. Compare and check.**

```
python scripts/screen.py compare --work <dir> --facts facts.json
```

It prints `found` (what each check found, in sentences) and `cases`.

**4. Ask Ada to decide.** For each of `cases`, call `ada_decide` with `name` (its `model`) and `data` exactly as
given. Write the answers to a file as `{"<signal>": <the tool's answer>, ...}`.

**5. The verdict.**

```
python scripts/screen.py verdict --work <dir> --answers answers.json
```

It prints the verdict: `person` (`real person`, `suspect` or `unsure`, and each signal with what it says and what
it found), `fit`, `made`, and `keep`.

**6. Show the card, and ask the person when asked to.** If the connector has the tool `screener_verdict`, call it
with the verdict from step 5 (without `keep`): it shows the verdict as a card, and for a signal Ada was unsure of
the person can answer on the card, which records the answer itself and tells you. Without the card, or when the
person answers in the chat: for each signal in `person.ask`, tell the person what that signal found and ask: is
this fine, or suspect? Record each answer with `ada_record`: the signal's `teach.args` (`name` and `data`) and
`outcome` `fine` or `suspect`. Never record the same answer twice. Then run step 5 again with
`--told <signal>=<answer>` for each answer given.
For the `others` signal there is no case to record: only pass `--told others=<answer>`.
If `fit.ask` is true, ask the person how well the applicant fits (strong, borderline or poor) and record it in
`screener-fit` the same way. Never record your own guess: only what the person said.

**7. Keep.** Call `ada_record` with `keep`'s `name` (its `model`), `data` and `outcome`, so the next application
is compared with this one. If the person told you the application repeats another, record `repeat` instead of
`alone`. Skip this step if the person asked you not to keep the application.

**8. Tell the person**, in this order and in plain words:

1. Real person, suspect or unsure, and for each signal what it found and who said so (Ada, with its confidence;
   the rule, when Ada had no close precedent; or the person).
2. The fit: strong, borderline or poor, with Ada's confidence, and what stood behind it.
3. One line: how much of the text reads as generated (`made`), or that Ada is unsure.

Then delete the work folder.

## Greenhouse

This plugin ships no Greenhouse connection. When the person has a Greenhouse connector in Claude and the applicant
is a Greenhouse candidate, read the candidate and the application with that connector (Harvest v3:
`GET /v3/candidates` and `GET /v3/applications` filtered to the candidate), write them to a file as
`{"candidate": {...}, "application": {...}}` exactly as returned, and pass `--greenhouse <file>` in step 1. The
verdict then has a `greenhouse` signal. This part is unproven: it was written from Greenhouse's API reference and
has never been run against a real Greenhouse account. Say so when you report it.

## Voice

Not built. Checking a voice recording is an open question (where the recording comes from, and what is judged).
There is no step for it; do not improvise one.

## Rules

- A verdict is a screening, not a judgement of the person. Never say a person is fake: say what was found.
- Nothing here has been proven on real applicants or real fraud. If the person asks how reliable it is, point them
  to `docs/checks.md` in the plugin and say plainly what was and was not measured.
- Say only what the application states. Never invent experience, skills or employers.
- Do not advise whom to hire or reject.
