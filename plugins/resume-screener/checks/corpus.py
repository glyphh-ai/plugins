"""The applicant corpus as the checks and the examples' build read it: a folder with `manifest.jsonl` (one
generated applicant a line: id, split, fit, generated) and `files/<id>/email.eml` (the application as an email with
its cover letter and resume attached). The corpus itself is not in this repository; what ships is the train split
as the models' cases (models/examples, built by build_examples.py). Each row is read by the same code a screening
uses, so a precedent and a new application are read alike.

    python corpus.py DIR      build models/examples from the corpus's train split"""

import gzip
import json
import sys
from pathlib import Path
from typing import Any

HERE: Path = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / "skills" / "screen-application" / "scripts")]

from screener import closeness, mail, steps  # noqa: E402

EXAMPLES: Path = steps.MODELS / "examples"


def rows(corpus: Path, split: str = "train") -> list[dict[str, Any]]:
    lines = (corpus / "manifest.jsonl").read_text().splitlines()
    return [row for row in map(json.loads, lines) if row["split"] == split]


def precedents(corpus: Path, row: dict[str, Any]) -> dict[str, dict[str, Any]] | None:
    """One row as each seeded model's precedent ({model: {data, outcome}}); None when the sender checks refuse it.
    The `others` model holds it without its arrival time: the corpus's emails were all written by one program in
    one sitting and say nothing true about timing."""
    made = steps.read(mail.read((corpus / "files" / row["id"] / "email.eml").read_bytes(), row["id"]))
    if "refused" in made:
        return None
    cases = steps.cases(steps.compare(made, {}))
    text = made["raw"]["text"]
    fake = closeness.case(closeness.parts(text["resume"], text["letter"]), row["id"], "fake", "generated examples",
                          made["raw"]["label"])  # fmt: skip
    return {
        "fit": {"data": cases["fit"], "outcome": row["fit"]},
        "made": {"data": cases["made"], "outcome": row["generated"]},
        "closeness": {"data": fake, "outcome": "fake"},
    }


def _write(made: dict[str, list[dict[str, Any]]]) -> dict[str, int]:
    """Each model's examples written one case a line, gzipped, the same bytes every time."""
    EXAMPLES.mkdir(exist_ok=True)
    for name, cases in made.items():
        lines = [json.dumps(case, sort_keys=True, separators=(",", ":")) for case in cases]
        with gzip.GzipFile(EXAMPLES / f"{name}.jsonl.gz", "wb", mtime=0) as out:
            out.write(("\n".join(lines) + "\n").encode())
    return {name: len(cases) for name, cases in made.items()}


def build(corpus: Path) -> dict[str, int]:
    """The train split written as each model's examples."""
    made: dict[str, list[dict[str, Any]]] = {"fit": [], "made": [], "closeness": []}
    for row in sorted(rows(corpus, "train"), key=lambda r: r["id"]):
        for name, case in (precedents(corpus, row) or {}).items():
            made[name].append(case)
    return _write(made)


def from_earlier(held: Path) -> dict[str, int]:
    """The closeness model's fakes made without the corpus, from two files an earlier version shipped: `held`
    (each example's summary, duties, cover letter, titles and education line, as the `others` model held it) and the
    `fit` file (the skills each lists). Each section goes through the same neutralising a new resume's does."""

    def load(path: Path) -> list[dict[str, Any]]:
        with gzip.open(path, "rt", encoding="utf-8") as lines:
            return [json.loads(line) for line in lines if line.strip()]

    skills = {c["data"]["key"]["s"]["id"]: c["data"]["resume"].get("skills", {}).get("terms") or []
              for c in load(EXAMPLES / "fit.jsonl.gz")}  # fmt: skip
    cases = []
    for c in load(held):
        d, who = c["data"], c["data"]["who"]["s"]
        words, history = d.get("words", {}).get("s", {}), d.get("history", {}).get("s", {})
        read = {"summary": words.get("summary"), "titles": history.get("titles"), "duties": words.get("duties"),
                "school": history.get("school"), "skills": skills[who["id"]], "letter": words.get("letter")}  # fmt: skip
        found = {k: w for k, v in read.items() if (w := closeness.neutral(v, closeness.KEPT[k]))}
        fake = closeness.case(found, who["id"], "fake", "generated examples", who["label"])
        cases.append({"data": fake, "outcome": "fake"})
    return _write({"closeness": cases})


if __name__ == "__main__":
    print(from_earlier(Path(sys.argv[2])) if sys.argv[1] == "--from-earlier" else build(Path(sys.argv[1])))
