"""The workbench of check 5 (docs/check-5-protocol.md): builds the sets, has Claude write the fakes and the polished
versions, has Claude read every application into facts, and asks Claude alone for the baseline. Everything it
reads and writes is in a local folder (LAB, default /tmp/sp-lab/data) that is never committed.

    python lab.py sets                 the seen and unseen texts from the local sources -> texts.jsonl
    python lab.py write A|P|B|Q        Claude writes: A fakes like lc, P polished lc, B fakes like gh/up, Q polished gh/up
    python lab.py read seen|unseen     Claude reads each application into facts -> facts.jsonl
    python lab.py alone seen|unseen    Claude alone: real or fake -> alone.jsonl
    python lab.py spent                the ledger's total

The key is read from the file ANTHROPIC_ENV names (a .env with ANTHROPIC_API_KEY) into this process only. Every
batch's tokens and cost are added to ledger.jsonl, and a batch that could take the total past CAP is refused."""

import csv
import gzip
import hashlib
import json
import os
import random
import re
import sys
import time
from pathlib import Path
from typing import Any

sys.path[:0] = [str(Path(__file__).resolve().parent.parent.parent / "skills" / "screen-application" / "scripts")]

import reading  # noqa: E402
from screener import closeness  # noqa: E402

LAB: Path = Path(os.environ.get("LAB", "/tmp/sp-lab/data"))
HUMAN: Path = Path(os.environ.get("HUMAN", "/tmp/sp-human"))
CAP: float = 80.0
PRICE: dict[str, tuple[float, float]] = {  # US dollars per million tokens, in and out; a batch is half
    "claude-haiku-5-5": (0.10, 0.50), "claude-sonnet-5-5": (2.0, 10.0), "claude-opus-5-5": (4.0, 20.0)}  # fmt: skip
READER, SMALL, OTHER = "claude-sonnet-5-5", "claude-haiku-5-5", "claude-opus-5-5"
CUT: int = 6000
SEEN: tuple[str, ...] = ("lc", "gen", "lc-fake", "lc-polished")
LABEL: dict[str, str] = {"lc": "real", "gh": "real", "up": "real", "lrec-real": "real", "lc-polished": "real",
                         "gh-polished": "real", "up-polished": "real", "lrec-enhanced": "real", "gen": "fake",
                         "lc-fake": "fake", "tpl": "fake", "gh-fake": "fake", "up-fake": "fake", "lrec-fake": "fake"}  # fmt: skip


def plain(text: str) -> str:
    """One plain form for every text: flattened lines given back, blank runs closed, cut at CUT characters."""
    lines = [" ".join(ln.split()) for ln in closeness.lines(text).splitlines()]
    return re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip()[:CUT]


def uid(source: str) -> str:
    """A random-looking id for a text: nothing of where it came from can be read off it."""
    return "t" + hashlib.sha256(f"glyphh-check5:{source}".encode()).hexdigest()[:10]


def order(ids: list[str]) -> list[str]:
    return sorted(ids, key=lambda i: hashlib.sha256(f"glyphh-check5-order:{i}".encode()).hexdigest())


def load(name: str) -> list[dict[str, Any]]:
    path = LAB / name
    return [json.loads(line) for line in path.read_text().split("\n") if line.strip()] if path.exists() else []


def save(name: str, rows: list[dict[str, Any]]) -> None:
    LAB.mkdir(parents=True, exist_ok=True)
    (LAB / name).write_text("".join(json.dumps(r) + "\n" for r in rows))


def row(source: str, kind: str, split: str, text: str, **more: Any) -> dict[str, Any]:
    return {"uid": uid(source), "source": source, "set": kind, "label": LABEL[kind], "split": split,
            "text": plain(text)} | more  # fmt: skip


def gen_text(held: dict[str, Any]) -> str:
    """One of the plugin's generated examples as a resume text, from what an earlier version shipped of it."""
    who, history = held["who"]["s"], held.get("history", {}).get("s", {})
    words = held.get("words", {}).get("s", {})
    jobs = zip(history.get("titles") or [], history.get("employers") or [], history.get("spans") or [], strict=False)
    lines = [who["label"].split(" - ")[0], "", "SUMMARY", words.get("summary", ""), "", "EXPERIENCE"]
    lines += [f"{t.title()}, {e.title()} {s}" for t, e, s in jobs]
    lines += [words.get("duties", ""), "", "EDUCATION", history.get("school", "")]
    return "\n".join(lines)


def sets() -> None:
    """The texts that exist before Claude writes any: lc (and what will be polished or shown as form), gen, tpl,
    gh, and up when it is there."""
    out: list[dict[str, Any]] = []
    csv.field_size_limit(10**9)
    with (HUMAN / "public/kaggle-resume-livecareer/raw/Resume.csv").open(newline="", encoding="utf-8", errors="replace") as f:
        lc = {r["ID"]: r for r in csv.DictReader(f) if len(r["Resume_str"]) >= 600}
    ids = order(list(lc))
    cuts = [("seed", 300), ("validation", 80), ("to-polish-seed", 100), ("to-polish-validation", 40), ("form", 400)]
    at = 0
    for split, n in cuts:
        for i in ids[at : at + n]:
            out.append(row(f"lc:{i}", "lc", split, lc[i]["Resume_str"], category=lc[i]["Category"]))
        at += n
    with gzip.open(HUMAN / "local/fakes-held.jsonl.gz", "rt", encoding="utf-8") as lines:
        held = {c["data"]["who"]["s"]["id"]: c["data"] for c in map(json.loads, lines)}
    held = {i: d for i, d in held.items() if d.get("words", {}).get("s", {}).get("duties")}
    gen = order(list(held))
    out += [row(f"gen:{i}", "gen", "seed" if n < 200 else "validation", gen_text(held[i])) for n, i in enumerate(gen[:260])]
    people = json.loads((HUMAN / "local/template-written.json").read_text())["applicants"]
    by_id = {a["id"]: a for a in people}
    out += [row(f"tpl:{i}", "tpl", "test", by_id[i]["resume"]) for i in order(list(by_id))[:100]]
    for path in sorted((HUMAN / "text").glob("*.txt")):
        if "cover" not in path.stem:
            out.append(row(f"gh:{path.stem}", "gh", "test", path.read_text()))
    up = HUMAN / "public/updated-resume/sample.jsonl"
    if up.exists():
        rows = {r["id"]: r for r in (json.loads(line) for line in up.read_text().split("\n") if line.strip())}
        out += [row(f"up:{i}", "up", "test", rows[i]["text"]) for i in order(list(rows))[:150]]
    made = {r["uid"] for r in out}
    out += [t for t in load("texts.jsonl") if t["uid"] not in made]  # what Claude wrote earlier is kept
    save("texts.jsonl", out)
    print({k: sum(r["set"] == k[0] and r["split"] == k[1] for r in out) for k in sorted({(r["set"], r["split"]) for r in out})})


# What Claude is asked to write.

WRITER: str = "You write sample resumes used to test a resume screening system. Output only the resume's text."
A: str = (
    "Below are two resumes from a public collection, to show the FORM only.\n\n<form>\n{one}\n</form>\n\n<form>\n{two}\n"
    "</form>\n\nWrite the resume of a wholly invented person who does not exist, working in this category: {category}. "
    "Follow the form of the examples exactly: the same kinds of sections and headings, the same stand-in words in "
    "place of employers and places (such as 'Company Name' and 'City, State') where the examples use them, and "
    "about {words} words. Invent every fact. Copy no sentence from the examples."
)
B: str = (
    "Below is one real resume, to show the FORM only.\n\n<form>\n{one}\n</form>\n\nWrite the resume of a wholly "
    "invented person who does not exist, in a different line of work or a different speciality from the example, "
    "written so that it would pass as a real person's own resume. A real life is uneven: jobs of very different "
    "lengths, a sideways move or an unrelated early job, study that did not go in a straight line, particular "
    "details only that person would mention, figures that are odd rather than round, wording that is plain in "
    "places and careless in others, and things left in that sell nothing. Follow the example's form (its kinds of "
    "sections, how it writes dates and employers, how long it is: about {words} words). Invent every fact, "
    "including real-sounding employer and place names. Copy no sentence from the example."
)
POLISH: str = (
    "Rewrite this resume so that it reads better: clearer wording, stronger verbs, consistent tense, tidy "
    "formatting. Keep every fact, date, employer, title, number and section exactly as it is; add nothing and "
    "remove nothing.\n\n<resume>\n{one}\n</resume>"
)


def writing(which: str) -> tuple[str, list[tuple[str, str, dict[str, Any]]]]:
    """(the model, [(custom id, the prompt, the row it will become)]) for one kind of writing."""
    texts = load("texts.jsonl")
    rng = random.Random(f"glyphh-check5-{which}")
    out = []
    if which == "A":
        form = [t for t in texts if t["set"] == "lc" and t["split"] == "form"]
        for n in range(260):
            one, two = rng.sample(form, 2)
            words = len(one["text"].split())
            prompt = A.format(one=one["text"], two=two["text"], category=one["category"].replace("-", " ").lower(), words=words)
            out.append((f"A{n}", prompt, row(f"lc-fake:{n}", "lc-fake", "seed" if n < 200 else "validation", "")))
        return SMALL, out
    if which == "P":
        for t in texts:
            if t["split"].startswith("to-polish"):
                split = t["split"].removeprefix("to-polish-")
                out.append((f"P{t['uid']}", POLISH.format(one=t["text"]), row(f"lc-polished:{t['uid']}", "lc-polished", split, "")))
        return SMALL, out
    for kind, n_fake in (("gh", 60), ("up", 120)):
        real = [t for t in texts if t["set"] == kind]
        if not real:
            continue
        if which == "B":
            for n in range(n_fake):
                one = real[n % len(real)]
                prompt = B.format(one=one["text"], words=len(one["text"].split()))
                out.append((f"B{kind}{n}", prompt, row(f"{kind}-fake:{n}", f"{kind}-fake", "test", "")))
        else:
            for t in real[:60]:
                out.append((f"Q{t['uid']}", POLISH.format(one=t["text"]), row(f"{kind}-polished:{t['uid']}", f"{kind}-polished", "test", "")))
    return OTHER, out


# Claude, through the Batches API, with a ledger.


def client() -> Any:
    import anthropic
    from dotenv import dotenv_values

    key = dotenv_values(os.environ.get("ANTHROPIC_ENV", ""))["ANTHROPIC_API_KEY"]
    return anthropic.Anthropic(api_key=key)


def spent() -> float:
    return round(sum(r["cost"] for r in load("ledger.jsonl")), 4)


def batch(stage: str, model: str, asks: list[tuple[str, dict[str, Any]]], most_out: int) -> dict[str, Any]:
    """Run `asks` ([(custom id, the request's parameters without the model)]) as one batch; {custom id: the reply's
    text}. Refused when the ledger's total and this batch's most could pass CAP."""
    pin, pout = PRICE[model]
    chars = sum(len(json.dumps(p)) for _, p in asks)
    most = 0.5 * (chars / 3 * pin + len(asks) * most_out * pout) / 1e6
    if spent() + most > CAP:
        raise SystemExit(f"refused: {stage} could cost {most:.2f} and {spent():.2f} of {CAP:.0f} is spent")
    api = client()
    made = api.messages.batches.create(requests=[
        {"custom_id": cid, "params": {"model": model, "max_tokens": most_out, "output_config": {"effort": "low"}} | p}
        for cid, p in asks])  # fmt: skip
    while api.messages.batches.retrieve(made.id).processing_status != "ended":
        time.sleep(20)
    got, tin, tout, failed = {}, 0, 0, 0
    for result in api.messages.batches.results(made.id):
        if result.result.type != "succeeded":
            failed += 1
            continue
        message = result.result.message
        tin += message.usage.input_tokens
        tout += message.usage.output_tokens
        got[result.custom_id] = next((b.text for b in message.content if b.type == "text"), "")
    cost = round(0.5 * (tin * pin + tout * pout) / 1e6, 4)
    save("ledger.jsonl", load("ledger.jsonl") + [{"stage": stage, "model": model, "asked": len(asks), "failed": failed,
                                                  "tokens_in": tin, "tokens_out": tout, "cost": cost}])  # fmt: skip
    print(f"{stage}: {len(got)} of {len(asks)} answered, {failed} failed, ${cost} (total ${spent()})")
    return got


def write(which: str) -> None:
    model, asks = writing(which)
    made = batch(f"write {which}", model, [(cid, {"system": WRITER, "messages": [{"role": "user", "content": p}]})
                                           for cid, p, _ in asks], 3000)  # fmt: skip
    rows = [r | {"text": plain(made[cid])} for cid, _, r in asks if len(made.get(cid, "")) > 300]
    kept = [t for t in load("texts.jsonl") if t["uid"] not in {r["uid"] for r in rows}]
    save("texts.jsonl", kept + rows)


def chosen(which: str) -> list[dict[str, Any]]:
    seen = which == "seen"
    return [t for t in load("texts.jsonl") if (t["set"] in SEEN) == seen and t["split"] in ("seed", "validation", "test")]


def asked(stage: str, into: str, which: str, system: str, schema: dict[str, Any]) -> None:
    """Claude asked the same thing of every chosen text not asked yet; answers added to `into`, by uid alone."""
    have = {r["uid"] for r in load(into)}
    todo = [t for t in chosen(which) if t["uid"] not in have]
    fmt = {"format": {"type": "json_schema", "schema": schema}, "effort": "low"}
    asks = [(t["uid"], {"system": system, "output_config": fmt, "messages": [{"role": "user", "content": reading.user(t["text"])}]})
            for t in todo]  # fmt: skip
    got = batch(f"{stage} {which}", READER, asks, 1500) if asks else {}
    rows = []
    for t in todo:
        try:
            rows.append({"uid": t["uid"], "answer": json.loads(got[t["uid"]])})
        except (KeyError, ValueError):
            continue
    save(into, load(into) + rows)
    print(f"{into}: {len(rows)} added, {len(todo) - len(rows)} missing")


if __name__ == "__main__":
    what, *rest = sys.argv[1:]
    if what == "sets":
        sets()
    elif what == "write":
        write(rest[0])
    elif what == "read":
        asked("read", "facts.jsonl", rest[0], reading.SYSTEM, reading.SCHEMA)
    elif what == "alone":
        asked("alone", "alone.jsonl", rest[0], reading.ALONE_SYSTEM, reading.ALONE_SCHEMA)
    elif what == "spent":
        print(spent())
