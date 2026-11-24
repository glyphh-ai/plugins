# Resume Screener

A Glyphh template as a plain Claude plugin. It screens a job application with **your own Ada models**:

1. **Is this a real person?** Answered from independent signals, each its own Ada model:
   - **the email's timestamps**: the `Date` header against each `Received` hop, their order, the gaps, a date in
     the future, an odd hour on the sender's clock, a burst of applications arriving together;
   - **the files themselves**: hidden, white or tiny text, characters never seen, tracked changes, marks of
     pasting from a chat, the program and author the file names;
   - **this application against the others seen**: the same work history under another name, the same phrasing,
     a shared phone or address, a burst of near-identical applications;
   - **Greenhouse signals**, when you have a Greenhouse connector in Claude (unproven, see below);
   - voice recording: **not built** ([docs/voice.md](docs/voice.md)).
2. **How well do they fit the role?** Strong, borderline or poor, from the resume read section by section.
3. One line: how much of the text reads as generated.

Code reads and measures. Ada decides, from precedents. When Ada is unsure, Claude asks you, and your answer becomes
a precedent.

**Nothing here is proven on real applicants or real fraud.** Every number we have was measured on generated
applications and on cases made for the purpose. Read [docs/checks.md](docs/checks.md) before you rely on it.

## Install

```
/plugin marketplace add glyphh-ai/plugins
/plugin install resume-screener@glyphh-plugins
```

You also need:

- an Ada Cloud account, and the Glyphh connector in Claude (its `ada_*` tools). Without the connector the skill
  uses the `glyphh` SDK instead (`pip install glyphh`, then `glyphh login`);
- Python 3.11 or later with `pypdf` (`pip install pypdf`).

## Set up your models

```
cd plugins/resume-screener/skills/screen-application/scripts
python seed.py                    # makes the six models, empty
python seed.py --corpus <folder>  # and loads examples into fit, made and others
```

Or ask Claude to "set up the Resume Screener": the skill makes the models through the connector.

The models, all in your own account:

| Model | Decides | Starts with |
|---|---|---|
| `screener-timing` | fine or suspect, from the email's timestamps | nothing: learns from your answers |
| `screener-files` | fine or suspect, from what the files themselves say | nothing: learns from your answers |
| `screener-others` | holds every application seen; Ada's nearest ones are compared | the examples, when seeded |
| `screener-greenhouse` | fine or suspect, from the candidate's Greenhouse record | nothing: learns from your answers |
| `screener-fit` | strong, borderline or poor | the examples, when seeded |
| `screener-made` | how much reads as generated: some, mostly, fully | the examples, when seeded |

Their specs, with weights, are in [`skills/screen-application/models`](skills/screen-application/models).

**The examples.** `seed.py --corpus` reads a folder of applications (`manifest.jsonl` and
`files/<id>/email.eml`) and loads its train split. The corpus the checks used (2,430 generated applications) is
not in this repository and is not published yet; write to support@glyphh.ai. Without examples the models start
empty and Ada asks you about every application until it has precedents.

## Use

In Claude, with the application's files at hand:

> Screen this application: application.eml

> Screen this applicant for Backend Engineer: (the email's text), resume.pdf, cover_letter.docx

Claude runs the steps in [the skill](skills/screen-application/SKILL.md) and answers with the verdict: real person,
suspect or unsure, with what each signal found; then the fit; then one line on how it was written.

Give it the email as an `.eml` file when you can. The timestamps are in the email's headers; a pasted email
without them cannot be checked for timing, and the verdict says so.

## What it keeps

Each screened application is recorded in your `screener-others` model (its work history, phrasing, contact details
and arrival time), so the next one can be compared with it. Tell Claude not to keep an application and it is not
recorded. The scripts' work folder holds the application's text during a screening and is deleted after.

## Greenhouse

The plugin ships no Greenhouse connection. If you have a Greenhouse connector in Claude, the skill reads the
candidate and the application through it and the `screener-greenhouse` model decides on what Greenhouse's Harvest
v3 API returns: the source, whether it was referred, the screening answers, the contact details on the record.
Harvest gives no IP address, no browser and no time taken to fill in the form, so none of those is used.
**Unproven:** written from Greenhouse's API reference, never run against a real Greenhouse account.

## The code

Everything deterministic is in
[`skills/screen-application/scripts/screener`](skills/screen-application/scripts/screener): plain Python, no model
of any kind. Tests: `pip install pytest pypdf && pytest plugins/resume-screener/tests`.

## Licence

MIT.
