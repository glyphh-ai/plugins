"""Check 5 on real Ada (docs/check-5-protocol.md): the model over the agent's facts, seeded and learned on the seen
sets' seed split, asked about the validation split (design) or the unseen test; beside it the controls and the
baselines, each an Ada model seeded on the same seed: layout only, the words (check 4's closeness model), and what
the facts still carry of the source. Claude alone is read from the workbench's file. `ada` is the async caller the
other checks use. Counting is all the analysis does: no model but Ada is fitted anywhere."""

import json
from collections import Counter
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import Any

import reading
from screener import closeness, steps

Ada = Callable[..., Awaitable[Any]]
# Facts of the reading the model does not use, decided on the seen sets' seed (design run 1). A fact is kept only
# if it is about the person and not about how the text was produced: it must tell real from fake on the seed, and it
# must survive polishing (the same people's resumes before and after an AI rewrite, `lc` against `lc-polished`,
# must answer it much alike).
# - dates, jobs: how a source writes things down (our generator's examples carry years and one or two jobs).
# - letter: the same for every text here (no real cover letters).
# - numbers, round_numbers, stock_phrases: told nothing apart (Ada's learning gave each under 0.05).
# - slips, evenness_of_writing: the strongest on the seed, and thrown out: they flip when a real person's resume
#   is polished (slips of 2 or 3: 82% of lc, 23% of lc-polished), so they measure the surface, not the person.
DROPPED: frozenset[str] = frozenset(("dates", "jobs", "letter", "numbers", "round_numbers", "stock_phrases", "slips",
                                     "evenness_of_writing"))  # fmt: skip
LAYERS: dict[str, tuple[str, ...]] = {
    "timeline": ("jobs", "dates", "overlaps", "gaps", "tenures", "short_stints", "path"),
    "unevenness": ("unrelated_work", "loose_ends", "education_path"),
    "specifics": ("named_things", "numbers", "round_numbers", "one_off_details"),
    "writing": ("stock_phrases", "evenness_of_writing", "slips", "every_line_sells"),
    "whole": ("fits_one_role", "duties_match_titles", "contradictions", "skills_shown", "letter"),
}
WEIGHT: dict[str, float] = {}  # written weights that are not 1.0, each with its reason in docs/person-model.md
ASK_BELOW: float = 0.7
BANDS: tuple[tuple[float, float], ...] = ((0.0, 0.6), (0.6, 0.7), (0.7, 0.8), (0.8, 0.9), (0.9, 1.01))


def spec(name: str, dropped: frozenset[str] = DROPPED) -> dict[str, Any]:
    """The model over the facts: a layer for each kind of observation; a count or a scale is a number, a kind is a
    category."""
    shape = {fact: schema for fact, schema, _ in reading.FACTS}
    layers = []
    for layer, facts in LAYERS.items():
        roles = []
        for fact in facts:
            if fact in dropped:
                continue
            role: dict[str, Any] = {"name": fact, "similarity_weight": WEIGHT.get(fact, 1.0)}
            if shape[fact]["type"] == "integer":
                top = 12 if fact == "jobs" else 3
                role["numeric_config"] = {"min_value": 0, "max_value": top, "bin_width": 1}
            roles.append(role)
        if roles:
            layers.append({"name": layer, "similarity_weight": 1.0, "segments": [{"name": "s", "roles": roles}]})
    key = {"name": "key", "similarity_weight": 0, "segments": [{"name": "s", "roles": [
        {"name": "id", "key_part": True, "similarity_weight": 0}]}]}  # fmt: skip
    return {"name": name, "layers": [*layers, key], "output": {"ask_below": ASK_BELOW}}


def case(uid: str, answer: dict[str, Any], dropped: frozenset[str] = DROPPED) -> dict[str, Any]:
    out: dict[str, Any] = {"key": {"s": {"id": uid}}}
    for layer, facts in LAYERS.items():
        roles = {f: (min(12, max(0, answer[f])) if f == "jobs" else answer[f]) for f in facts if f not in dropped and f in answer}
        if roles:
            out[layer] = {"s": roles}
    return out


def layout(uid: str, text: str) -> dict[str, Any]:
    """Format alone: counts of the plain text, nothing of what it says."""
    lines = [ln for ln in text.splitlines() if ln.strip()]
    words = text.split()
    per = max(len(text), 1) / 1000

    def cap(n: float, top: int) -> int:
        return int(min(top, max(0, round(n))))

    return {"l": {"s": {
        "words": cap(len(words) / 25, 40), "lines": cap(len(lines) / 5, 40),
        "word_length": cap(10 * sum(map(len, words)) / max(len(words), 1), 120),
        "line_words": cap(len(words) / max(len(lines), 1), 60),
        "digits": cap(sum(c.isdigit() for c in text) / per, 100), "capitals": cap(sum(c.isupper() for c in text) / per, 200),
        "commas": cap(text.count(",") / per, 60), "colons": cap(text.count(":") / per, 40),
        "bullets": cap(100 * sum(ln.lstrip()[:1] in "-•*·" for ln in lines) / max(len(lines), 1), 100),
        "id": uid}}}  # fmt: skip


def layout_spec(name: str) -> dict[str, Any]:
    tops = {"words": 40, "lines": 40, "word_length": 120, "line_words": 60, "digits": 100, "capitals": 200,
            "commas": 60, "colons": 40, "bullets": 100}  # fmt: skip
    roles: list[dict[str, Any]] = [{"name": n, "numeric_config": {"min_value": 0, "max_value": t, "bin_width": max(1, t // 20)}}
                                   for n, t in tops.items()]  # fmt: skip
    roles.append({"name": "id", "key_part": True, "similarity_weight": 0})
    return {"name": name, "layers": [{"name": "l", "segments": [{"name": "s", "roles": roles}]}]}


def words_case(uid: str, text: str) -> dict[str, Any] | None:
    made = closeness.case(closeness.parts(text), uid)
    return {"resume": made["resume"], "who": made["who"]} if "resume" in made else None


def rows(lab: Path, name: str) -> list[dict[str, Any]]:
    path = lab / name
    return [json.loads(line) for line in path.read_text().split("\n") if line.strip()]


async def model(ada: Ada, name: str, made: dict[str, Any], known: list[dict[str, Any]], learn: bool = True) -> Any:
    await ada("POST", "/v1/models", {"name": name, "spec": made | {"name": name}})
    for at in range(0, len(known), 250):
        await ada("POST", f"/v1/models/{name}/record_many", {"cases": known[at : at + 250]})
    if not learn:
        return None
    job = await ada("POST", f"/v1/models/{name}/learn", {})
    while job.get("state") not in ("done", "failed"):
        job = await ada("GET", f"/v1/jobs/{job['id']}")
    return job.get("result") if job.get("state") == "done" else {"failed": job.get("error")}


async def decided(ada: Ada, name: str, data: dict[str, Any]) -> dict[str, Any]:
    said = await ada("POST", f"/v1/models/{name}/decide", {"data": data})
    outcome = said.get("outcome")
    return {"outcome": outcome, "p": float((said.get("probabilities") or {}).get(outcome or "", 0.0)), "ask": bool(said.get("ask"))}


def score(answers: list[tuple[dict[str, Any], dict[str, Any] | None]], truth: str = "label") -> dict[str, Any]:
    """By set: how many were given their label. A text with no answer counts as wrong."""
    by: dict[str, Counter[str]] = {}
    for text, said in answers:
        got = (said or {}).get("outcome")
        tally = by.setdefault(text["set"], Counter())
        tally["n"] += 1
        tally["right"] += got == text[truth]
        tally["asked"] += bool((said or {}).get("ask"))
    out: dict[str, Any] = {k: dict(v) | {"share": round(v["right"] / v["n"], 3)} for k, v in sorted(by.items())}
    for label in ("real", "fake"):
        sets = [k for k in by if steps_label(k) == label and "polished" not in k and "enhanced" not in k]
        n, right = sum(by[k]["n"] for k in sets), sum(by[k]["right"] for k in sets)
        out[f"all {label}"] = {"n": n, "right": right, "share": round(right / n, 3) if n else None}
    return out


def steps_label(kind: str) -> str:
    return "fake" if kind in ("gen", "tpl") or kind.endswith("-fake") or kind.startswith("fraud") else "real"


def bands(answers: list[tuple[dict[str, Any], dict[str, Any] | None]]) -> list[dict[str, Any]]:
    out = []
    for low, high in BANDS:
        inside = [(t, s) for t, s in answers if s and low <= s["p"] < high]
        right = sum(s["outcome"] == t["label"] for t, s in inside)
        out.append({"confidence": f"{low:.1f} to {min(high, 1.0):.1f}", "n": len(inside),
                    "right": round(right / len(inside), 3) if inside else None})  # fmt: skip
    return out


def spread_by_label(seed: list[dict[str, Any]], facts: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """Each fact's values on the seed, counted by set: what the design reads to keep or drop a fact."""
    out: dict[str, Any] = {}
    for fact, _, _ in reading.FACTS:
        table: dict[str, Counter[str]] = {}
        for t in seed:
            if t["uid"] in facts:
                table.setdefault(t["set"], Counter())[str(facts[t["uid"]].get(fact))] += 1
        out[fact] = {k: dict(sorted(v.items())) for k, v in sorted(table.items())}
    return out


async def run(ada: Ada, lab: Path, mode: str) -> dict[str, Any]:
    """`mode` design: asked about the validation split; test: asked about the unseen test."""
    texts = rows(lab, "texts.jsonl")
    facts = {r["uid"]: r["answer"] for r in rows(lab, "facts.jsonl")}
    alone = {r["uid"]: r["answer"] for r in rows(lab, "alone.jsonl")} if (lab / "alone.jsonl").exists() else {}
    seed = [t for t in texts if t["split"] == "seed" and t["uid"] in facts]
    asked = [t for t in texts if t["split"] == ("validation" if mode == "design" else "test")]
    out: dict[str, Any] = {"mode": mode, "seeded": dict(Counter(t["set"] for t in seed)), "asked": dict(Counter(t["set"] for t in asked)),
                           "no reading": sum(t["uid"] not in facts for t in asked), "dropped facts": sorted(DROPPED)}  # fmt: skip
    # The model over the agent's facts.
    learned = await model(ada, "person", spec("person"), [{"data": case(t["uid"], facts[t["uid"]]), "outcome": t["label"]} for t in seed])
    out["learned"] = learned
    person = [(t, await decided(ada, "person", case(t["uid"], facts[t["uid"]])) if t["uid"] in facts else None) for t in asked]
    out["facts model"] = score(person)
    out["facts model, confidence"] = bands(person)
    # The layout-only control.
    await model(ada, "layout", layout_spec("layout"), [{"data": layout(t["uid"], t["text"]), "outcome": t["label"]} for t in seed])
    out["layout only"] = score([(t, await decided(ada, "layout", layout(t["uid"], t["text"]))) for t in asked])
    # The words (check 4's model), seeded on the same seed.
    known = [{"data": c | {"side": {"s": {"is": t["label"]}}}, "outcome": t["label"]} for t in seed if (c := words_case(t["uid"], t["text"]))]
    await model(ada, "words", steps.models()["closeness"]["spec"], known, learn=False)
    worded = []
    for t in asked:
        c = words_case(t["uid"], t["text"])
        worded.append((t, await decided(ada, "words", {"resume": c["resume"]}) if c else None))
    out["words only"] = score(worded)
    # Claude alone.
    out["claude alone"] = score([(t, {"outcome": alone[t["uid"]]["answer"], "ask": False} if t["uid"] in alone else None) for t in asked])
    if mode == "design":
        out["facts on the seed, by set"] = spread_by_label(seed, facts)
        # What the facts still carry of the source: told apart within one label.
        for name, pair in (("source: gen or lc-fake", ("gen", "lc-fake")), ("source: lc or lc-polished", ("lc", "lc-polished"))):
            known = [{"data": case(t["uid"], facts[t["uid"]]), "outcome": t["set"]} for t in seed if t["set"] in pair]
            await model(ada, name.split(":")[0] + "-" + pair[0], spec("x"), known)
            said = [(t, await decided(ada, name.split(":")[0] + "-" + pair[0], case(t["uid"], facts[t["uid"]])))
                    for t in asked if t["set"] in pair and t["uid"] in facts]  # fmt: skip
            right = sum(s["outcome"] == t["set"] for t, s in said)
            out[name] = {"n": len(said), "right": right}
    return out
