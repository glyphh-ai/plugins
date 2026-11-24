"""Make the Resume Screener's Ada models in your own account and load examples into them, through the Glyphh SDK
(pip install glyphh pypdf; `glyphh login`, or GLYPHH_API_KEY).

    python seed.py                      make the six models, empty
    python seed.py --corpus DIR         and load the corpus's train split into fit, made and others

The corpus is a folder with `manifest.jsonl` (one applicant a line: id, split, fit, generated) and
`files/<id>/email.eml` (the application as an email with its resume and cover letter attached). Each train row is
read by the same code a screening uses, so a precedent and a new application are read alike. Only the train split
is loaded; the test split is never read.

What is loaded where:
- fit: every train row with its fit label (strong, borderline, poor); then Ada's own learning is run.
- made: every train row with how much of it was generated (some, mostly, fully); then learning.
- others: every train row, held so new applications are compared with it. Its arrival time is left out: the
  corpus's emails were all written by one program in one sitting and say nothing true about timing.
- files, timing, greenhouse: nothing. They start empty and learn from your answers alone."""

import argparse
import json
from pathlib import Path
from typing import Any

from screener import mail, steps

CHUNK: int = 500


def rows(corpus: Path, split: str = "train") -> list[dict[str, Any]]:
    lines = (corpus / "manifest.jsonl").read_text().splitlines()
    return [row for row in map(json.loads, lines) if row["split"] == split]


def precedents(corpus: Path, row: dict[str, Any]) -> dict[str, dict[str, Any]] | None:
    """One row as each seeded model's precedent ({model: {data, outcome}}); None when the sender checks refuse it."""
    made = steps.read(mail.read((corpus / "files" / row["id"] / "email.eml").read_bytes(), row["id"]))
    if "refused" in made:
        return None
    held = {part: case for part, case in made["others"].items() if part != "when"}
    cases = steps.cases(steps.compare(made, {}))
    return {
        "fit": {"data": cases["fit"], "outcome": row["fit"]},
        "made": {"data": cases["made"], "outcome": row["generated"]},
        "others": {"data": held, "outcome": "alone"},
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--corpus", help="the corpus folder; without it the models are made and left empty")
    parser.add_argument("--prefix", default=steps.PREFIX, help="what your models' names begin with")
    args = parser.parse_args()
    from glyphh import Ada

    ada, specs = Ada(), steps.models()
    have = {m["name"] if isinstance(m, dict) else getattr(m, "name", str(m)) for m in ada.models()}
    for name, model in specs.items():
        if args.prefix + name in have:
            print(f"{args.prefix + name}: already there, left as it is")
        else:
            ada.create_model(args.prefix + name, model["spec"] | {"name": args.prefix + name})
            print(f"{args.prefix + name}: made")
    if not args.corpus:
        return
    corpus = Path(args.corpus)
    loaded: dict[str, list[dict[str, Any]]] = {"fit": [], "made": [], "others": []}
    for row in rows(corpus):
        for name, case in (precedents(corpus, row) or {}).items():
            loaded[name].append(case)
    for name, cases in loaded.items():
        model = ada.model(args.prefix + name)
        for at in range(0, len(cases), CHUNK):
            model.record_many(cases[at : at + CHUNK])
        print(f"{args.prefix + name}: {len(cases)} precedents loaded")
        if specs[name]["learn"]:
            model.learn()
            print(f"{args.prefix + name}: learned")


if __name__ == "__main__":
    main()
