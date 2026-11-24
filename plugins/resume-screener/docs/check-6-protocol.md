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

### The unseen test (run once, 2026-11-24; look number 1, and the only one)

980 unseen texts, read once by the agent and judged once. Nothing was changed after it.

**In one sentence: the named signals fire on fraud-shaped applications from a builder never seen and rarely on
real people, but Ada's whole decision calls half of the real people from unseen sources fake, so the headline
fails.**

| Unseen set | n | Ada says fake | A signal fired | Flagged (either) | Bar |
|---|---|---|---|---|---|
| **fraud-shaped, unseen builder** | 192 | 182 | 174 | **188 (98%)** | at least 80%: met |
| of those, careful | 96 | 94 | 82 | 95 (99%) | at least 70%: met |
| **real people, pooled** | 304 | 151 | 31 | **167 (55%)** | at most 20%: **missed** |
| `gh` (GitHub) | 19 | 7 | 4 | 9 (47%) | at most 30%: missed |
| `up` | 146 | 67 | 21 | 78 (53%) | missed |
| `lrec-real` | 139 | 77 | 6 | 80 (58%) | missed |
| polished real (`gh`, `up`) | 79 | 46 | 8 | 52 (66%) | at most 20%: missed |
| invented, nothing planted: `tpl` | 100 | 87 | 6 | 87 | no bar |
| invented: `lrec-fake` | 125 | 125 | 2 | 125 | no bar |
| invented, written to pass: `gh-fake`, `up-fake` | 180 | 106 | 2 | 107 (59%) | no bar |

**Why the real side failed, as far as the run shows.** Ada's learning put its heaviest weight on how the
employers and schools are given. In the one seen real source the site had replaced every employer with a stand-in,
so "employers withheld" came to mean "real", and real people who name their employers looked like the fakes. The
split the protocol asked for shows it: of unseen real resumes left as their source gave them, Ada's decision or a
signal flagged 79%; of those given a contact block by code, 34%. The decision followed the form of the one real
source it had seen. The confound was in the data, and one real source could not remove it.

**Per signal, each on its own (the firing rules, frozen before the test):**

| Planted signal | Careless: its part fired | Careful: its part fired | Fired on real people (false alarm) | Bar (70% / 50% / at most 10%) |
|---|---|---|---|---|
| location (phone or email time against the home) | 12 of 12 | 12 of 12 | 5 of 304 (1.6%) | met |
| name (email address named for someone else) | 12 of 12 | 12 of 12 | 5 of 304 (1.6%) | met |
| address (mail drop, or elsewhere) | 12 of 12 | 9 of 12 | 19 of 304 (6.3%) | met |
| dates and facts (something did not exist then) | 11 of 12 | **3 of 12** | 4 of 304 (1.3%) | careful: **missed** |
| built (vague employers, nothing checkable) | 9 of 12 | 10 of 12 | 4 of 304 (1.3%) | met |

Taken together, some signal fired on 174 of the 192 fraud-shaped applications (91%; 85% of the careful ones) and
on 31 of the 304 real people (10%: `gh` 4 of 19, `up` 21 of 146, `lrec-real` 6 of 139). Most of the address alarms
are on resumes whose contact block code made up. **This "signals only" reading was not the protocol's headline and
is not claimed as a pass:** it is what the frozen rules did, and it would need its own run on fresh unseen
material to count.

**The memory signals** (run once; 60 held, 60 controls, unseen real resumes):

| Variant | Flagged by its own signal | Bar 90% |
|---|---|---|
| another body, the same email and phone, a new name (`shared`) | 60 of 60 | met |
| another body, the same name, new contact details (`name`) | 60 of 60 | met |
| the same body under a new name and contacts (`pattern`) | **4 of 60** | **missed** |
| controls flagged by any | 0 of 60 | met |

`pattern` missed because the comparison reads a resume by its section headings, and these two unseen sources
(one with its punctuation stripped, one with damaged encoding) have none it recognises: there was no body to
compare. On this plugin's own corpus the same comparison caught 100% (check 1).

**Controls and baselines on the same unseen test:**

| | Real people right | Fraud-shaped caught | |
|---|---|---|---|
| Layout only | 62% | 49% | balanced 56%: at or under 60%, so **format alone does not separate the unseen test**, as required |
| Words only (check 4's model) | 0% | 38% | calls every unseen real person fake |
| Claude alone | 78% | 89% | and caught 2 of the 180 invented-to-pass fakes |
| Ada alone (no firing rule) | 50% | 95% | |

Fraud-shaped applications were flagged alike whatever form they were written in (`gh` 9 of 9, `up` 87 of 89,
`lrec-real` 92 of 94).

**Confidence is not meaningful on unseen sources.** When Ada said 90% or more it was right 80% of the time (543
cases); at 80 to 90%, 62%; at 70 to 80%, 60%; at 60 to 70%, 57%. It overstates, and must not be shown as a
probability of fraud.

### What this does and does not show

- It shows: an agent reading with a fixed schema, and plain rules over that reading, find planted location, name,
  address and built-to-order defects written by a model and prompt never seen, with few alarms on real people
  from three sources never seen; and Ada's memory finds a reused email, phone or name every time.
- It does not show: that Ada's learned decision can tell fraud from real people across sources. It could not: it
  flagged half of the real people.
- It does not show anything about **real** fraud. Every fraudulent application here was built for the test. The
  schemes documented in [fraud-indicators.md](fraud-indicators.md) often use a real person's identity and work
  history, which no reading of a resume can tell from that person.
- Careful date and fact conflicts are not found (3 of 12), and on the seed real people's dates conflicted more
  often than built ones.

### What the evidence suggests is needed

1. **Real people from more than one source in the seed**, ideally the customer's own past applicants: with one
   real source Ada learned that source. A design that holds out one seen source at a time would have shown this
   before the test.
2. **Ada's decision limited to facts that mean the same in every source**, or the verdict taken from the named
   signals with Ada used for memory (shared contacts, names, bodies) and for learning from the person's answers,
   which is where it did its work here.
3. **A fresh unseen test** for whichever of those is built: this one has been looked at and must not be used to
   design.
4. **A customer's own flagged cases**, to say anything about real fraud.

Money: 38.36 US dollars spent of the 80 cap across checks 5 and 6 (Claude wrote 1,091 texts,
read 4,227 and was asked alone 2,451 times; the ledger is local).
