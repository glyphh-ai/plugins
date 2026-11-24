"""Set the Resume Screener up in your own Ada account, through the Glyphh SDK (pip install glyphh pypdf;
`glyphh login`, or GLYPHH_API_KEY).

    python seed.py                       make the models and load the fakes that ship with the plugin
    python seed.py --real FOLDER         also load your own past real applicants' resumes as the real side

It can be run again at any time: a model that is there is left as it is, an example already held is replaced by
itself (each has its own id), and learning is run again.

What is loaded where:
- closeness: the 1,980 generated examples, recorded as `fake`. With `--real FOLDER`, every resume in the folder
  (PDF, DOCX or text; a file named like a cover letter is read as one) is read by the same code and recorded as
  `real`. They are your own data and go to your own Ada account, nowhere else. Until you load real ones the model
  can only say how close an application is to fakes.
- fit: the same 1,980 examples with their fit (strong, borderline, poor); then Ada's own learning is run.
- made: the same 1,980 with how much of each was generated (some, mostly, fully); then learning.
- others: nothing. It holds only the applications you screen.
- files, timing, greenhouse: nothing. They start empty and learn from your answers alone.

Every example that ships is a generated, fictional application: a program wrote it, and no real person is in it."""

import argparse
import gzip
import hashlib
import json
from pathlib import Path
from typing import Any

from screener import attachments, closeness, mail, resumes, steps

CHUNK: int = 500
EXAMPLES = steps.MODELS / "examples"


def examples(name: str) -> list[dict[str, Any]]:
    """The model's shipped examples, each {data, outcome}; none for a model that starts empty."""
    path = EXAMPLES / f"{name}.jsonl.gz"
    if not path.exists():
        return []
    with gzip.open(path, "rt", encoding="utf-8") as lines:
        return [json.loads(line) for line in lines if line.strip()]


def real(folder: Path, source: str = "your own applicants") -> list[dict[str, Any]]:
    """Every resume in the folder as a `real` case of the closeness model. Each is named by a hash of its file's
    name, never by the person: nothing of who they are is kept, only the words of their resume's sections."""
    out = []
    for path in sorted(p for p in folder.rglob("*") if p.is_file()):
        data = path.read_bytes()
        kind = mail.kind_of(path.name, data)
        if kind is None or attachments.LETTER_NAME.search(path.name):
            continue
        try:
            found = closeness.parts(resumes.text(kind, data))
        except ValueError:
            continue
        mid = "real-" + hashlib.sha256(path.name.encode()).hexdigest()[:12]
        case = closeness.case(found, mid, "real", source, source)
        if "resume" in case:
            out.append({"data": case, "outcome": "real"})
    return out


def load(ada: Any, name: str, cases: list[dict[str, Any]]) -> None:
    for at in range(0, len(cases), CHUNK):
        ada.model(name).record_many(cases[at : at + CHUNK])


def setup(ada: Any, prefix: str = steps.PREFIX, say: Any = print, real_from: Path | None = None,
          source: str = "your own applicants") -> None:  # fmt: skip
    """`ada` is the SDK's client (glyphh.Ada)."""
    have = {m.name for m in ada.models()}
    for name, model in steps.models().items():
        full = prefix + name
        if full in have:
            say(f"{full}: already there")
        else:
            ada.create_model(full, model["spec"] | {"name": full})
            say(f"{full}: made")
        cases = examples(name)
        load(ada, full, cases)
        if cases:
            say(f"{full}: {len(cases)} examples loaded")
        if cases and model["learn"]:
            ada.model(full).learn()
            say(f"{full}: learned")
    if real_from is not None:
        cases = real(real_from, source)
        load(ada, prefix + "closeness", cases)
        say(f"{prefix}closeness: {len(cases)} real resumes loaded from {real_from}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--prefix", default=steps.PREFIX, help="what your models' names begin with")
    parser.add_argument("--real", help="a folder of your own past real applicants' resumes (PDF, DOCX or text)")
    parser.add_argument("--source", default="your own applicants", help="what a real one is shown as: never a name")
    args = parser.parse_args()
    from glyphh import Ada

    setup(Ada(), args.prefix, real_from=Path(args.real) if args.real else None, source=args.source)


if __name__ == "__main__":
    main()
