# Check 7: each fraud signal its own Ada model, on a fresh unseen test

Written and committed before any run that it judges. Results go at the end as they come.

**No real, caught fraud is tested here.** Every fraudulent application is built for the test, after documented
schemes ([fraud-indicators.md](fraud-indicators.md)). A pass shows the signals fire on fraud-shaped applications
from a builder never seen and stay quiet on real people from sources never seen. It does not show that real fraud
is caught.

## What changes from check 6, and why

Check 6's whole-application Ada decision flagged 55% of real people from unseen sources: seeded with one real
source, it learned that source. Its named signals, taken alone, did well. So:

1. **Each named signal is its own small Ada model** with its own decision, confidence and fact tree: `location`,
   `name`, `address`, `built`, `aligned`. There is no whole-application model. Ada is also the memory (`shared`,
   `name` reuse, `pattern`) and the learner: a person's answer to a signal is a new precedent of that signal.
2. **Seeded from several sources.** Everything check 6 looked at is now design data: real people from four sources
   (`lc`, `gh`, `up`, `lrec-real`) and fraud-shaped applications from two builders (`fraud-seen`, Haiku;
   `fraud-unseen`, Opus). A signal's examples: an application in which that signal was planted is `fires`; every
   real application, and every fraud-shaped one in which it was not planted, is `quiet`.
3. **Facts a source rewrites are neutralised** before Ada sees them: an employer or school the source replaced
   with a stand-in is left out (it weighs nothing), and "named and checkable" and "named but unknown" are one value,
   `named` (which of the two an agent picks follows how famous the name is, not the person). On real resumes whose
   contact block was made by code, the facts that compare that block with the body (`places`, and an address "not
   fitting the home") are left out: the block was never part of that body.
4. **Leave one source out, before the test.** For each of the four real sources in turn, every signal model is
   seeded without it and asked about it. The design is not ready unless, for every source held out, at most 20% of
   its real people are flagged (and at most 30% for a source of fewer than 30). The same is done with each fraud
   builder held out, and reported.

## The verdict's rule (written before any run)

For each signal, Ada decides `fires` or `quiet` with a confidence.

- A signal **fires strongly** when Ada decides `fires` with confidence at or above that signal's strong line.
- It **fires weakly** when Ada decides `fires` below the strong line.
- **Flagged:** any signal fires strongly, or two or more fire weakly.
- **`aligned` never flags alone**: it can only ever count as a weak signal.
- **The strong line** of each signal is the lowest of 0.6, 0.7, 0.8 and 0.9 at which, in leave-one-source-out, it
  fires strongly on at most 5% of the held-out real people for every source. If none does, that signal can only
  fire weakly.
- What is shown is a band, **fired strongly / fired weakly / nothing fired**, with each signal's evidence and
  fact tree. Ada's confidence is shown as a percentage only if the fresh test finds it honest (below).

## Memory

`shared` and `name` reuse are kept as tested (60 of 60, no false alarm). `pattern` failed on resumes with no
headings the reader knows, so the `others` model gains a **body** part: the whole resume's words with the name,
email addresses, phone numbers and digits taken out, compared as a bag of words whatever the layout. Its ceiling
is chosen on the sources of check 6's memory run (now design data) and frozen.

## The fresh unseen test

Check 6's unseen test has been looked at and is design data. The headline is on material used nowhere so far:

- **Real people:** resumes newly gathered from public repositories whose authors published them under an open
  licence (other people than before), and one more public set of real resumes from a source not used so far. What
  each is, is said in the results. They are left as they are: no contact block is added.
- **Fraud-shaped:** written by a builder and prompt not used before (**Claude Sonnet 5.5, prompt F3**), in those
  sources' forms: each signal alone and in three combinations, careless and careful, 12 of each (192).
- **Memory cases** made by code from the fresh real resumes, as in check 6.

Read once by the agent, judged once.

## Bar (on the fresh test only)

1. Real people flagged: at most 20% pooled, at most 30% for any source.
2. Fraud-shaped caught (flagged): at least 80%, and at least 70% of the careful ones.
3. Layout-only control (an Ada model over counts of the plain text, same seed): at most 60% balanced.
4. Per signal, reported: catch of its own planted cases, careless and careful, and false alarms on real people.
5. Memory: each variant found by its own signal at least 90% of the time; at most 5% of controls flagged.
6. Confidence: for each signal with at least 30 decisions in a band, the share right within 10 points of the
   band's middle. If not, the percentage is not shown anywhere; the bands are.
7. Baselines, reported: Claude alone; and a single whole-application Ada model on the same seed (check 6's kind).

## Rules

- Ada only; no other model of any kind, in the product or the analysis.
- Design on seen material only (leave-one-source-out, the strong lines, the body ceiling); frozen and committed;
  then the fresh test once.
- Money: 38.36 US dollars spent before this check; the cap of 80 stands, and the run stops before passing it.
- Other people's resumes stay on one machine and go only to the Claude API for the reading and the writing
  described here.

## Results

Not run yet.
