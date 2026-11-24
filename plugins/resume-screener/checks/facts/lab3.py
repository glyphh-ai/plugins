"""The workbench of check 7 (docs/check-7-protocol.md): the fresh unseen material. Real resumes gathered anew
(left as they are: no contact block is added), and fraud-shaped applications written by a builder and prompt not
used before (Claude Sonnet 5.5, prompt F3) in those sources' forms.

    python lab3.py sets               the fresh real texts -> texts.jsonl (split `fresh`)
    python lab3.py write              Claude Sonnet writes the fresh fraud-shaped applications
    python lab3.py read               Claude reads every fresh text into fraud facts -> facts2.jsonl
    python lab3.py alone              Claude alone on every fresh text -> alone2.jsonl"""

import json
import random
import sys
from typing import Any

import lab
import lab2
import reading2

FRESH = lab.HUMAN / "fresh"
F3: str = (
    "A hiring-fraud ring is preparing an application. Its operator works from a real resume it has collected "
    "(below, for layout and length only) and fabricates a new applicant around it.\n\n<collected>\n{one}\n"
    "</collected>\n\nWrite the fabricated applicant's resume as the operator would send it: the same layout "
    "conventions and roughly {words} words, for work in a different field from the collected one, opening with "
    "the applicant's name, town, telephone, email and postal address. The operator's fabrication has this "
    "weakness: {plant}. {care} The resume must not hint that it is fabricated. All names, employers, schools and "
    "details are made up; no sentence is taken from the collected resume."
)
CARE: dict[str, str] = {
    "careless": "The operator is sloppy here, and the weakness is plain to anyone who reads with attention.",
    "careful": "The operator is skilled: the rest is coherent and persuasive, and the weakness is slight, found only by checking.",
}


def sets() -> None:
    lab.LABEL |= {"gh2": "real"}
    out = []
    for path in sorted((FRESH / "gh2" / "text").glob("*.txt")):
        out.append(lab.row(f"gh2:{path.stem}", "gh2", "fresh", path.read_text()))
    for sample in sorted(FRESH.glob("*/sample.jsonl")):
        slug = sample.parent.name
        lab.LABEL[slug] = "real"
        rows = [json.loads(line) for line in sample.read_text().split("\n") if line.strip()]
        out += [lab.row(f"{slug}:{r['id']}", slug, "fresh", r["text"]) for r in rows]
    made = {r["uid"] for r in out}
    lab.save("texts.jsonl", out + [t for t in lab.load("texts.jsonl") if t["uid"] not in made])
    print({s: sum(r["set"] == s for r in out) for s in sorted({r["set"] for r in out})})


def write() -> None:
    lab.LABEL |= {"fraud-fresh": "fake"}
    real = [t for t in lab.load("texts.jsonl") if t["split"] == "fresh" and t["label"] == "real"]
    rng = random.Random("glyphh-check7-F3")
    asks = []
    for kind in lab2.KINDS:
        for care in CARE:
            for n in range(12):
                one = rng.choice(real)
                plant = "; and ".join(lab2.PLANTS[k] for k in kind.split("+"))
                prompt = F3.format(one=one["text"], words=len(one["text"].split()), plant=plant, care=CARE[care])
                made = lab.row(f"fraud-fresh:{kind}:{care}:{n}", "fraud-fresh", "fresh", "")
                asks.append((f"F3{len(asks)}", prompt, made | {"kind": kind, "care": care, "form": one["set"]}))
    got = lab.batch("write F3", lab.READER, [(cid, {"system": lab.WRITER, "messages": [{"role": "user", "content": p}]})
                                             for cid, p, _ in asks], 3500)  # fmt: skip
    rows = [r | {"text": lab.plain(got[cid])} for cid, _, r in asks if len(got.get(cid, "")) > 300]
    kept = [t for t in lab.load("texts.jsonl") if t["uid"] not in {r["uid"] for r in rows}]
    lab.save("texts.jsonl", kept + rows)


def asked(stage: str, into: str, system: str, schema: dict[str, Any]) -> None:
    have = {r["uid"] for r in lab.load(into)}
    todo = [t for t in lab.load("texts.jsonl") if t["split"] == "fresh" and t["uid"] not in have]
    fmt = {"format": {"type": "json_schema", "schema": schema}, "effort": "low"}
    asks = [(t["uid"], {"system": system, "output_config": fmt, "messages": [{"role": "user", "content": reading2.user(t["text"])}]})
            for t in todo]  # fmt: skip
    got = lab.batch(f"{stage}2 fresh", lab.READER, asks, 2500) if asks else {}
    rows = []
    for t in todo:
        try:
            rows.append({"uid": t["uid"], "answer": json.loads(got[t["uid"]])})
        except (KeyError, ValueError):
            continue
    lab.save(into, lab.load(into) + rows)
    print(f"{into}: {len(rows)} added, {len(todo) - len(rows)} missing")


if __name__ == "__main__":
    what = sys.argv[1]
    if what == "sets":
        sets()
    elif what == "write":
        write()
    elif what == "read":
        asked("read", "facts2.jsonl", reading2.SYSTEM, reading2.SCHEMA)
    elif what == "alone":
        asked("alone", "alone2.jsonl", reading2.ALONE_SYSTEM, reading2.ALONE_SCHEMA)
