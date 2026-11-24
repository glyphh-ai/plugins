"""Check 4 of docs/checks.md: the closeness model on held-out rows of each side, the format control, and the
texts from other sources, on real Ada. `ada` is the async caller the other checks use.

The real side and the other sources are read from a local folder that is never committed, never uploaded and
never part of what the plugin ships:
    public/kaggle-resume-livecareer/raw/Resume.csv   the real side (ID, Resume_str, Category)
    public/d4rk3r-resumes-raw-pdf/sample.jsonl       another source of resumes, authorship unknown
    text/*.txt                                       resumes their authors published under an open licence
    local/template-written.json                      applications another program wrote from sentence templates
    local/fakes-held.jsonl.gz                        the fakes' section texts as an earlier version shipped them"""

import csv
import gzip
import hashlib
import json
import math
import re
from collections import Counter
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import Any

from screener import closeness, resumes, sections, steps

Ada = Callable[..., Awaitable[Any]]
MODEL, FORMAT = "check4-closeness", "check4-format"
HELD_OUT, SEEDED = 300, 1560  # of each side: never recorded, and recorded
REAL: str = "livecareer examples (Kaggle Resume Dataset)"
CUT: dict[str, int] = {"summary": 800, "duties": 2000, "school": 300}  # characters, as the fakes' texts were kept
MATCHED: frozenset[str] = frozenset(("INFORMATION-TECHNOLOGY", "FINANCE", "DESIGNER", "SALES", "ACCOUNTANT",
                                     "BUSINESS-DEVELOPMENT", "ENGINEERING", "HR", "DIGITAL-MEDIA"))  # fmt: skip
SENTENCE: re.Pattern[str] = re.compile(r"[.!?]+")


def _order(ids: list[str]) -> list[str]:
    return sorted(ids, key=lambda i: hashlib.sha256(f"glyphh-closeness-1:{i}".encode()).hexdigest())


def _gz(path: Path) -> list[dict[str, Any]]:
    with gzip.open(path, "rt", encoding="utf-8") as lines:
        return [json.loads(line) for line in lines if line.strip()]


def raw_sections(resume: str) -> dict[str, str]:
    """A resume's summary, duties and education line as plain text, cut as the fakes' were kept."""
    cut = sections.split(closeness.lines(resume))
    duties = " ".join(ln for ln in cut["experience"].splitlines() if not resumes.SPAN.search(ln))
    read = {"summary": cut["summary"], "duties": duties, "school": cut["education"]}
    return {name: " ".join(said.split())[: CUT[name]] for name, said in read.items()}


def shape(texts: dict[str, str]) -> dict[str, Any]:
    """Format alone: nothing of what the words are, only how the summary and the duties are laid out."""
    out: dict[str, Any] = {}
    for name in ("summary", "duties"):
        said = texts.get(name) or ""
        words = said.split()
        sentences = [s for s in SENTENCE.split(said) if s.strip()]
        per = max(len(said), 1) / 1000
        out |= {
            f"{name}_words": min(400, len(words)),
            f"{name}_word_length": min(120, round(10 * sum(map(len, words)) / max(len(words), 1))),
            f"{name}_sentence_words": min(80, round(len(words) / max(len(sentences), 1))),
            f"{name}_digits": min(100, round(sum(c.isdigit() for c in said) / per)),
            f"{name}_capitals": min(200, round(sum(c.isupper() for c in said) / per)),
            f"{name}_commas": min(60, round(said.count(",") / per)),
        }
    return out | {"school_words": min(60, len((texts.get("school") or "").split()))}


def format_spec() -> dict[str, Any]:
    tops = {"words": 400, "word_length": 120, "sentence_words": 80, "digits": 100, "capitals": 200, "commas": 60}
    roles = [{"name": f"{part}_{name}", "numeric_config": {"min_value": 0, "max_value": top, "bin_width": top // 20}}
             for part in ("summary", "duties") for name, top in tops.items()]  # fmt: skip
    roles.append({"name": "school_words", "numeric_config": {"min_value": 0, "max_value": 60, "bin_width": 3}})
    roles.append({"name": "id", "key_part": True, "similarity_weight": 0})
    return {"name": FORMAT, "layers": [{"name": "f", "segments": [{"name": "s", "roles": roles}]}]}


def fakes(folder: Path) -> dict[str, dict[str, Any]]:
    """{id: {case, texts}}: the shipped fakes, and each one's section texts for the format control."""
    held = {c["data"]["who"]["s"]["id"]: c["data"] for c in _gz(folder / "local" / "fakes-held.jsonl.gz")}
    out = {}
    for c in _gz(steps.MODELS / "examples" / "closeness.jsonl.gz"):
        mid = c["data"]["who"]["s"]["id"]
        words, history = held[mid].get("words", {}).get("s", {}), held[mid].get("history", {}).get("s", {})
        texts = {"summary": words.get("summary", ""), "duties": words.get("duties", ""), "school": history.get("school", "")}
        out[mid] = {"case": c["data"], "texts": texts}
    return out


def one(mid: str, side: str, source: str, label: str, resume: str, letter: str = "") -> dict[str, Any]:
    case = closeness.case(closeness.parts(resume, letter), mid, side, source, label)
    return {"case": case, "texts": raw_sections(resume), "label": label}


def reals(folder: Path) -> dict[str, dict[str, Any]]:
    csv.field_size_limit(10**9)
    path = folder / "public" / "kaggle-resume-livecareer" / "raw" / "Resume.csv"
    with path.open(newline="", encoding="utf-8", errors="replace") as f:
        rows = list(csv.DictReader(f))
    return {f"lc-{r['ID']}": one(f"lc-{r['ID']}", "real", REAL, r["Category"], r["Resume_str"]) for r in rows}


def others_sources(folder: Path) -> dict[str, list[dict[str, Any]]]:
    """Texts from sources the model holds nothing of, each read as a resume asked about (no side)."""
    out: dict[str, list[dict[str, Any]]] = {}
    pdfs = folder / "public" / "d4rk3r-resumes-raw-pdf" / "sample.jsonl"
    if pdfs.exists():
        rows = [json.loads(line) for line in pdfs.read_text().split("\n") if line.strip()]
        english = [r for r in rows if sum(c.isascii() for c in r["text"]) / len(r["text"]) > 0.97]
        out["other resumes, authorship unknown (d4rk3r PDFs, English)"] = [one(r["id"], "", "", "", r["text"]) for r in english]
    texts = sorted((folder / "text").glob("*.txt")) if (folder / "text").exists() else []
    own = [p for p in texts if "cover" not in p.stem]
    if own:
        out["resumes their authors published (GitHub, open licence)"] = [one(p.stem, "", "", "", p.read_text()) for p in own]
    written = folder / "local" / "template-written.json"
    if written.exists():
        people = json.loads(written.read_text())["applicants"]
        out["another program's applications (sentence templates)"] = [
            one(a["id"], "", "", "", a["resume"], a.get("body", "")) for a in people]  # fmt: skip
    return out


async def hold(ada: Ada, model: str, cases: list[dict[str, Any]]) -> None:
    for at in range(0, len(cases), 250):
        await ada("POST", f"/v1/models/{model}/record_many", {"cases": cases[at : at + 250]})


async def asked(ada: Ada, case: dict[str, Any]) -> dict[str, Any]:
    """The closeness answer for one case, with Ada asked as the plugin asks it."""
    plain = {k: v for k, v in case.items() if k != "side"}
    facts = {a["key"]: await ada("POST", f"/v1/models/{MODEL}/facts", {"data": a["data"], "top": a["top"]})
             for a in closeness.asks(plain)}  # fmt: skip
    out = closeness.result(plain, facts)
    part = "resume" if "resume" in plain else "letter" if "letter" in plain else None
    if part:
        body = {"data": {part: plain[part]}, "include": ["facts"]}
        out["decision"] = closeness.decision(await ada("POST", f"/v1/models/{MODEL}/decide", body))
    return out


def spread(values: list[float]) -> dict[str, Any]:
    ranked = sorted(values)
    if not ranked:
        return {"n": 0}
    cut = {f"p{p}": ranked[max(0, math.ceil(p / 100 * len(ranked)) - 1)] for p in (5, 25, 50, 75, 95)}
    return cut | {"n": len(ranked), "min": ranked[0], "max": ranked[-1]}


def tally(answers: list[dict[str, Any]]) -> dict[str, Any]:
    resumes_ = [a["resume"] for a in answers if "resume" in a]
    decided = [a["decision"] for a in answers if "decision" in a]
    both = [r for r in resumes_ if r["fake"]["closeness"] is not None and r["real"]["closeness"] is not None]
    return {
        "n": len(answers), "with a resume read": len(resumes_),
        "reads": dict(Counter(r["reads"] for r in resumes_)),
        "ada decided": dict(Counter(d["outcome"] or "no answer" for d in decided)),
        "ada unsure": sum(bool(d["ask"]) for d in decided),
        "closest fake": spread([r["fake"]["closeness"] for r in both]),
        "closest real": spread([r["real"]["closeness"] for r in both]),
        "fake minus real": spread([round(r["fake"]["closeness"] - r["real"]["closeness"], 2) for r in both]),
    }  # fmt: skip


async def run(ada: Ada, folder: Path, peek: bool = False) -> dict[str, Any]:
    """`peek`: 60 seeded a side and 3 asked, to see the plumbing work; nothing of it is a result."""
    fake, real = fakes(folder), reals(folder)
    real = {i: r for i, r in real.items() if "resume" in r["case"]}  # a resume is compared on its experience section
    fake = {i: r for i, r in fake.items() if "resume" in r["case"]}
    out_of = {"fakes with an experience section read": len(fake), "real with one": len(real)}
    f_order, r_order = _order(list(fake)), _order(list(real))
    held, seeded = (3, 60) if peek else (HELD_OUT, SEEDED)
    f_held, f_seed = f_order[:held], f_order[HELD_OUT : HELD_OUT + seeded]
    r_held, r_seed = r_order[:held], r_order[HELD_OUT : HELD_OUT + seeded]
    spec = steps.models()["closeness"]["spec"] | {"name": MODEL}
    await ada("POST", "/v1/models", {"name": MODEL, "spec": spec})
    await hold(ada, MODEL, [{"data": fake[i]["case"], "outcome": "fake"} for i in f_seed])
    await hold(ada, MODEL, [{"data": real[i]["case"], "outcome": "real"} for i in r_seed])
    out: dict[str, Any] = {"seeded": {"fake": len(f_seed), "real": len(r_seed)}} | out_of
    fake_answers = [await asked(ada, fake[i]["case"]) for i in f_held]
    real_answers = [await asked(ada, real[i]["case"]) for i in r_held]
    out["held-out fakes"], out["held-out real"] = tally(fake_answers), tally(real_answers)
    matched = [a for i, a in zip(r_held, real_answers, strict=True) if real[i]["label"] in MATCHED]
    out["held-out real, categories like the fakes' roles"] = tally(matched)
    out["shown for a held-out fake"], out["shown for a held-out real"] = fake_answers[0], real_answers[0]
    if peek:
        return out
    for name, rows in others_sources(folder).items():
        out[name] = tally([await asked(ada, r["case"]) for r in rows])
    # The format control: a model that reads only how the summary and the duties are laid out.
    await ada("POST", "/v1/models", {"name": FORMAT, "spec": format_spec()})

    def laid(i: str, row: dict[str, Any]) -> dict[str, Any]:
        return {"f": {"s": shape(row["texts"]) | {"id": i}}}

    known = [{"data": laid(i, fake[i]), "outcome": "fake"} for i in f_seed]
    known += [{"data": laid(i, real[i]), "outcome": "real"} for i in r_seed]
    await hold(ada, FORMAT, known)
    job = await ada("POST", f"/v1/models/{FORMAT}/learn", {})
    while job.get("state") not in ("done", "failed"):
        job = await ada("GET", f"/v1/jobs/{job['id']}")
    table: Counter[str] = Counter()
    for side, ids, rows in (("fake", f_held, fake), ("real", r_held, real)):
        for i in ids:
            said = await ada("POST", f"/v1/models/{FORMAT}/decide", {"data": laid(i, rows[i])})
            table[f"{side}>{said.get('outcome') or 'no answer'}"] += 1
    right = table["fake>fake"] + table["real>real"]
    out["format control"] = {"learned": job.get("state"), "answers": dict(sorted(table.items())),
                             "right": right, "of": len(f_held) + len(r_held)}  # fmt: skip
    return out
