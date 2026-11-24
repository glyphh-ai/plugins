# Check 6: fraud signals, on sources and fraud-builders never seen

Written and committed before any run that it judges. Results go at the end as they come.

## The question

Is this application from an invented or misrepresented person, and which signals does it share with fraudulent
applications: above all, what in it does **not line up**? Whether the text was written or polished by AI is not
the question and is not reported as a result: a real person's AI-polished resume counts as real, and one line
checks that polish does not trip the verdict.

**There is no corpus of real, caught fraud here.** Every fraudulent application in this check was built for it,
after the way documented schemes build them ([fraud-indicators.md](fraud-indicators.md): public advisories and
reporting, each indicator cited). So this check can show that the signals fire on fraud-shaped applications from a
builder the models never saw, and stay quiet on real people from sources they never saw. It cannot show that real
fraud is caught. That stays unproven until it is tried on a customer's own flagged cases.

## What happened to check 5

Check 5 asked "real person or AI-invented person". Its design was frozen and the agent read its unseen texts, but
its judging run was **never made**: no result on its unseen test was computed or looked at by anyone. It is
superseded by this check. Its unseen real sources (`gh`, `up`, `lrec-real`) are therefore still unseen and are the
unseen real side here; they are read again with the fraud reading.

## The agent and Ada

**The agent (Claude Sonnet 5.5) reads** each application with one fixed prompt and schema
(`checks/facts/reading2.py`): what lines up and what does not, with the evidence quoted, and, where an answer
needs knowledge of the world, how sure it is. It is never asked whether the applicant is genuine.

**Ada decides**, in one model, `fraud`, whose spec has a named part for each signal, each with its own roles and
weight, each showing in the fact tree:

| Part | What it holds | From |
|---|---|---|
| `location` | claimed home against the jobs' and schools' places; the phone's area or country code; the email's time zone and hour when there is an email | the agent's reading |
| `name` | the applicant's name against the email address's own name; this name seen before with other contact details | the reading; the person's own screened applications |
| `address` | the postal address: full, city only, none, a mail drop or virtual office, or not fitting the claimed home (what a reader can judge without looking anything up) | the reading |
| `pattern` | the same or near-same body, history or phrasing as another application held, among the person's own screened applications and among the known-fake examples | Ada's nearest applications (the `others` comparison) |
| `timestamps` | the email's Date against its Received hops, bursts, an hour that does not fit the claimed home | the timing code, when there is an email; "not checked" when there is none |
| `shared` | the same email or phone under a different name; the same name under a different email | the person's own screened applications |
| `aligned` | dates; study against work; whether employers, products and tools existed then; titles against duties and years; the role against the employer; the letter against the resume | the reading |
| `built` | how checkable the employers, schools and claims are; how generic the body is; how far it mirrors a posting; how wide the skills are; the shape and unevenness of the history | the reading |

One model rather than sibling models, so that weak signals add up in one decision and one fact tree; a part with
nothing to go on is left out of the case and weighs nothing. Beside Ada's decision, code names **which signals
fired** (a part with a "does not line up" or its like), so that one strong signal is enough to flag whatever the
whole says. The memory behind `name`, `pattern` and `shared` is the person's own Ada model of what they screened,
plus the fake examples; never anyone else's data.

## The data

Seen (design, seed, validation):

- real: `lc` (livecareer) and `lc-polished` (the same kind, rewritten by AI: counted as real);
- fake, invented with nothing planted: `gen` (our generator), `lc-fake` (Haiku, in `lc`'s form);
- fake, fraud-shaped: `fraud-seen`, written by **Claude Haiku 5.5 with prompt F1** in `lc`'s form: one planted
  signal at a time (location; name; address; dates and facts; built to a posting and uncheckable) and three
  combinations, each **careless** (meant to be noticed) and **careful** (written to pass): 240.

Unseen (the test; read by the agent once, judged once):

- real: `gh` (19), `up` (146), `lrec-real` (139 authentic resumes of the LREC 2026 corpus);
- fake, fraud-shaped: `fraud-unseen`, written by **Claude Opus 5.5 with prompt F2** (another model, another
  prompt) in the forms of the unseen real sets, the same eight kinds, careless and careful: 192;
- fake, invented with nothing planted, from builders never seen: `tpl` (a template program), `gh-fake` and
  `up-fake` (Opus, written to pass), `lrec-fake` (that corpus's Gemini, Meta and ChatGPT resumes). These are
  invented people, one kind of fake; they are reported apart from the fraud-shaped ones;
- one sanity line: `gh-polished` and `up-polished`, real people rewritten by AI.

The real resumes of `lc`, `up` and `lrec-real` carry no contact details (the sources removed them). So that having
a contact block is not itself a mark of a fake, half of them (by a hash of the id) are given a consistent block
made by code: a name, a home, a phone with that home's area code, an email address in that name, a street address
there. This is said wherever those lines are read.

## The headline and the bar (all on the unseen test)

1. **Fraud-shaped fakes from an unseen builder:** at least 80% of `fraud-unseen` flagged (Ada decides `fake`, or a
   signal fired), and at least 70% of the **careful** ones.
2. **Real people from unseen sources:** at most 20% of `gh`, `up` and `lrec-real` pooled flagged, and no source
   over 30%.
3. **Per signal:** for each planted signal alone, the share of its applications on which **that** part fired
   (catch), and the share of unseen real applications on which that part fired (false alarm). Bar: catch at least
   70% careless and 50% careful for each of location, name, address, dates, built; false alarm at most 10% each.
4. **The layout-only control must fail:** an Ada model over counts of the plain text, same seed, right on no more
   than 60% of the unseen test (balanced between real and fraud-shaped). If it does better, the headline does not
   count.
5. **Source control:** the unseen fakes were written in the unseen reals' forms; the flag rate on real texts with
   a code-made contact block and without one is reported, and on `fraud-unseen` by the form it was written in. A
   model keyed on form would split by form, not by truth.
6. **Confidence:** Ada's confidence in bands against how often it was right, as in check 5: within 10 points in
   every band of 30 or more, or the number is renamed for what it is.
7. Sanity: at most 20% of polished real flagged. Invented-with-nothing-planted fakes: reported, no bar (with
   nothing planted there may be nothing to find; that is said).

Baselines on the same unseen test: check 4's words-only model on the same seed; layout only; Claude alone, asked
directly "genuine or fraudulent".

**The memory signals** (`name` reuse, `pattern`, `shared`) need earlier applications. They are tested apart, on
unseen real resumes: 60 are held as "screened"; code makes from them the same body under a new name and contacts,
another person's body with the same email and phone under a new name, and another body under the same name with a
new email; 60 others, each with its own contacts, are the controls. Bar: each variant flagged by its own signal at
least 90% of the time; at most 5% of controls flagged by any of them.

## Rules

- Ada only; no other model of any kind, in the product or the analysis.
- Design (which facts are kept, weights, ask-below, what counts as "fired") on the seen sets only; frozen and
  committed; then the unseen test once. Any further look is numbered and named.
- Money: the ledger carries on from check 5 (15.18 US dollars spent before this check); the cap of 80 stands.
- Other people's resumes stay on one machine and are sent only to the Claude API for the reading and the writing
  described here. Evidence quotes never carry a name, an email address or a phone number.

## Results

### Design, on the seen sets only (2026-11-24)

Claude Sonnet 5.5 read the 1,280 seen texts with the fraud reading. Ada: 976 seeded (300 `lc`, 100 `lc-polished`,
200 `gen`, 200 `lc-fake`, 176 `fraud-seen`), learning run, 304 validation texts decided.

**What the seed showed that the plan had wrong.** The plan took "dates that do not line up" as a mark of fraud. On
the seed the agent found them in **46% of real resumes and 30% of the fraud-shaped ones**: real people's dates
overlap, contradict and trail off far more than built ones do. The same holds for study against work. So those
facts stay in Ada's model, where they are weighed with everything else, and they never flag on their own. The
first firing rules, which let them, flagged 60% of real people on validation (design run 1). The narrowed rules
(reasons in `checks/facts/fraud_check.py`): a phone or email time that does not fit the home; an email address
named for someone else; a mail drop or an address elsewhere; something that did not exist when the resume says it
did; vague employers with nothing checkable.

A flaw in the control: the contact blocks code gave to half the real resumes name a home at random, so on some of
them the agent rightly found the home not fitting the jobs' places. `places` alone therefore does not fire; it
stays in the model.

**Design run 2 (frozen), validation texts, never seeded:**

| Set | n | Ada says fake | A signal fired | Flagged (either) |
|---|---|---|---|---|
| `lc` real | 80 | 2 | 6 | 8 (10%) |
| `lc-polished` real | 40 | 3 | 5 | 7 (17.5%) |
| `fraud-seen` | 64 | 53 | 55 | 59 (92%) |
| of those, careful | 32 | 29 | 26 | 30 (94%) |
| `gen`, invented, nothing planted | 60 | 59 | 1 | 59 (98%) |
| `lc-fake`, invented, nothing planted | 60 | 59 | 0 | 59 (98%) |

Beside it on the same validation texts: layout only, real 89% right and fakes 95%; words only, real 43% and fakes
88%; Claude alone, real 93% and fakes 50% (it passed 75% of our generator's fakes and 65% of the `lc`-form ones as
genuine, and caught 88% of the fraud-shaped ones). Layout still separates the **seen** sets, as before; the test
is whether it does on the unseen ones.

What Ada's learning weighs most: how the employers are given (1.00), the schools (0.86), loose ends (0.77),
unrelated work (0.77), short stints (0.70), the career's shape (0.67), dates (0.62), one-off details (0.62).

None of this is the result. The result is the unseen test, run once with this design.
