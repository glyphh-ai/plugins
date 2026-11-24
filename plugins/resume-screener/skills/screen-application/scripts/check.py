"""The simple check: a resume and a cover letter in (either may be missing), how close they are to real people's
and to fakes out. It asks your `closeness` Ada model through the Glyphh SDK (pip install glyphh pypdf;
`glyphh login`, or GLYPHH_API_KEY).

    python check.py --resume resume.pdf --letter cover_letter.docx
    python check.py resume.pdf cover_letter.pdf        which is which is told from the files

It prints, for the resume and for the cover letter apart: `fake` and `real`, each the closeness of the nearest
one (0 to 1) and the nearest few; `reads` (like the fakes, like real people, between the two); and `decision`:
Ada's own answer with its confidence and its fact tree, as Ada gave it. Nothing is recorded anywhere.

`--stdin` reads one JSON request instead ({resume: {name, base64}, letter: {name, base64}}, either missing; or
{files: [...]} when which is which is not known) and never touches the disk: it is how a web page runs this same
code on files held in memory."""

import argparse
import base64
import json
import sys
from pathlib import Path
from typing import Any

from screener import attachments, closeness, mail, resumes, steps

File = tuple[str, bytes]


def texts(files: list[File], resume: File | None = None, letter: File | None = None) -> tuple[str, str, list[str]]:
    """(the resume's text, the cover letter's text, what could not be read). Files given without saying which is
    which are told apart by their names, else their words (screener/attachments.py)."""
    problems: list[str] = []

    def read(file: File) -> tuple[str, str, str] | None:
        kind = mail.kind_of(*file)
        try:
            return (file[0], kind, resumes.text(kind, file[1])) if kind else problems.append(f"{file[0]}: not PDF, DOCX or text")
        except ValueError as err:
            return problems.append(f"{file[0]}: {err}")

    told = [read(resume) if resume else None, read(letter) if letter else None]
    loose = [r for r in map(read, files) if r]
    picked = attachments.split(loose) if loose else ("", "none", "")
    return (told[0][2] if told[0] else picked[0]), (told[1][2] if told[1] else picked[2]), problems


def check(ada: Any, resume: str, letter: str, prefix: str = steps.PREFIX) -> dict[str, Any]:
    """`ada` is the SDK's client (glyphh.Ada)."""
    asked = closeness.case(closeness.parts(resume, letter), "asked")
    model = ada.model(prefix + "closeness")
    facts = {a["key"]: model.facts(a["data"], top=a["top"]).data for a in closeness.asks(asked)}
    out = closeness.result(asked, facts)
    part = next((p for p in ("resume", "letter") if p in asked), None)
    if part:
        said = model.decide({part: asked[part]}, include=["facts"])
        answer = {"outcome": said.outcome, "probabilities": dict(said.probabilities or {}), "ask": said.ask,
                  "facts": said.facts}  # fmt: skip
        out["decision"] = closeness.decision(answer) | {"on": part}
    if resume.strip() and "resume" not in asked:
        out["note"] = "no experience section could be read in the resume, so it was not compared"
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("files", nargs="*", help="the resume and the cover letter, in any order")
    parser.add_argument("--resume")
    parser.add_argument("--letter")
    parser.add_argument("--prefix", default=steps.PREFIX, help="what your models' names begin with")
    parser.add_argument("--stdin", action="store_true")
    args = parser.parse_args()
    from glyphh import Ada

    def named(path: str | None) -> File | None:
        return (Path(path).name, Path(path).read_bytes()) if path else None

    if args.stdin:
        asked = json.loads(sys.stdin.read())

        def sent(f: Any) -> File | None:
            return (str(f["name"]), base64.b64decode(f["base64"])) if f else None

        loose = [f for f in map(sent, asked.get("files") or []) if f]
        resume, letter, problems = texts(loose, sent(asked.get("resume")), sent(asked.get("letter")))
    else:
        loose = [f for f in map(named, args.files) if f]
        resume, letter, problems = texts(loose, named(args.resume), named(args.letter))
    out = check(Ada(), resume, letter, args.prefix)
    print(json.dumps(out | ({"could not read": problems} if problems else {}), indent=1))


if __name__ == "__main__":
    main()
