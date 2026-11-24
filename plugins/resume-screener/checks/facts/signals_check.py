"""Check 7 on real Ada (docs/check-7-protocol.md): each named fraud signal its own small Ada model over the agent's
reading, seeded from several sources. `design`: leave one real source out at a time, and one fraud builder at a
time; from that, each signal's strong line. `test`: seeded with everything seen, asked about the fresh unseen
material, once. `ada` is the async caller the other checks use. No model but Ada is fitted anywhere."""

from collections import Counter
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import Any

import facts_check as base
import fraud_check
import reading2

Ada = Callable[..., Awaitable[Any]]
SIGNALS: dict[str, tuple[str, ...]] = {
    "location": ("places", "phone", "email_time"),
    "name": ("name_and_email",),
    "address": ("postal_address",),
    "built": ("employers", "schools", "checkable_claims", "one_off_details", "generic_body", "mirrors_a_posting", "breadth_of_skills"),
    "aligned": ("dates", "study_and_work", "existed_then", "existed_then_sure", "seniority", "role_at_employer"),
}  # fmt: skip
PLANTED: dict[str, str] = {"location": "location", "name": "name", "address": "address", "dates": "aligned", "built": "built"}
SOURCE: dict[str, str] = {"lc": "lc", "lc-polished": "lc", "gh": "gh", "gh-polished": "gh", "up": "up", "up-polished": "up",
                          "lrec-real": "lrec"}  # fmt: skip
BUILDERS: tuple[str, ...] = ("fraud-seen", "fraud-unseen")
STEPS: tuple[float, ...] = (0.6, 0.7, 0.8, 0.9)
# Each signal's strong line, set by the design run's rule and frozen; None: it can only fire weakly.
LINES: dict[str, float | None] = {"location": None, "name": None, "address": None, "built": None, "aligned": None}
SCALES: frozenset[str] = frozenset(name for name, schema, _ in reading2.FACTS if schema.get("type") == "integer")


def neutral(t: dict[str, Any], a: dict[str, Any]) -> dict[str, Any]:
    """The reading with what a source rewrites taken out (docs/check-7-protocol.md, 3)."""
    out = dict(a)
    for fact in ("employers", "schools"):
        if out.get(fact) == "withheld_by_the_source":
            out.pop(fact)
        elif out.get(fact) in ("named_and_checkable", "named_but_unknown"):
            out[fact] = "named"
    if t.get("contact") == "added":  # a contact block made by code was never part of this body
        out.pop("places", None)
        if out.get("postal_address") == "does_not_fit_the_location":
            out["postal_address"] = "full"
    return out


def spec(signal: str) -> dict[str, Any]:
    roles: list[dict[str, Any]] = []
    for fact in SIGNALS[signal]:
        role: dict[str, Any] = {"name": fact}
        if fact in SCALES:
            role["numeric_config"] = {"min_value": 0, "max_value": 3, "bin_width": 1}
        roles.append(role)
    roles.append({"name": "id", "key_part": True, "similarity_weight": 0})
    return {"name": signal, "layers": [{"name": signal, "segments": [{"name": "s", "roles": roles}]}], "output": {"ask_below": 0.7}}


def case(signal: str, t: dict[str, Any], a: dict[str, Any]) -> dict[str, Any]:
    read = neutral(t, a)
    return {signal: {"s": {f: read[f] for f in SIGNALS[signal] if f in read} | {"id": t["uid"]}}}


def planted(t: dict[str, Any]) -> set[str]:
    return {PLANTED[k] for k in str(t.get("kind") or "").split("+") if k in PLANTED}


def flagged(fires: dict[str, float], lines: dict[str, float | None]) -> str:
    """The band: `strongly`, `weakly` (two or more weak signals; flags too), `one weak signal` or `nothing`."""
    strong = [s for s, p in fires.items() if s != "aligned" and lines.get(s) is not None and p >= lines[s]]  # type: ignore[operator]
    if strong:
        return "strongly"
    return "weakly" if len(fires) >= 2 else "one weak signal" if fires else "nothing"


async def answers(ada: Ada, tag: str, seed: list[dict[str, Any]], asked: list[dict[str, Any]],
                  facts: dict[str, dict[str, Any]]) -> dict[str, dict[str, float]]:  # fmt: skip
    """{uid: {signal: Ada's confidence that it fires}} for the asked texts, each signal model seeded with `seed`."""
    out: dict[str, dict[str, float]] = {t["uid"]: {} for t in asked}
    for signal in SIGNALS:
        name = f"{signal}-{tag}"
        known = [{"data": case(signal, t, facts[t["uid"]]), "outcome": "fires" if signal in planted(t) else "quiet"} for t in seed]
        await base.model(ada, name, spec(signal), known)
        for t in asked:
            said = await base.decided(ada, name, case(signal, t, facts[t["uid"]]))
            if said["outcome"] == "fires":
                out[t["uid"]][signal] = round(said["p"], 3)
    return out


def table(rows: list[tuple[dict[str, Any], dict[str, float]]], lines: dict[str, float | None]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    groups: dict[str, list[tuple[dict[str, Any], dict[str, float]]]] = {}
    for t, fires in rows:
        groups.setdefault(t["set"], []).append((t, fires))
        if "care" in t:
            groups.setdefault(f"{t['set']} {t['care']}", []).append((t, fires))
        if t["label"] == "real":
            groups.setdefault("all real", []).append((t, fires))
    for name, group in sorted(groups.items()):
        bands = Counter(flagged(f, lines) for _, f in group)
        hit = bands["strongly"] + bands["weakly"]
        out[name] = {"n": len(group), "flagged": hit, "share": round(hit / len(group), 3), "bands": dict(bands),
                     "which fired": dict(Counter(s for _, f in group for s in f))}  # fmt: skip
    return out


def per_signal(rows: list[tuple[dict[str, Any], dict[str, float]]]) -> dict[str, Any]:
    real = [f for t, f in rows if t["label"] == "real"]
    out: dict[str, Any] = {}
    for kind, signal in PLANTED.items():
        line: dict[str, Any] = {}
        for care in ("careless", "careful"):
            mine = [f for t, f in rows if t.get("kind") == kind and t.get("care") == care]
            line[care] = {"n": len(mine), "its model fired": sum(signal in f for f in mine)}
        line["fired on real"] = {"n": len(real), "fired": sum(signal in f for f in real),
                                 "by confidence": {str(s): sum(f.get(signal, 0) >= s for f in real) for s in STEPS}}  # fmt: skip
        out[kind] = line
    return out


def calibration(rows: list[tuple[dict[str, Any], dict[str, float]]]) -> dict[str, Any]:
    """For each signal's `fires` decisions: by band of confidence, how often the signal really was planted."""
    out: dict[str, Any] = {}
    for signal in SIGNALS:
        bands = []
        for low, high in ((0.5, 0.7), (0.7, 0.8), (0.8, 0.9), (0.9, 1.01)):
            inside = [t for t, f in rows if low <= f.get(signal, 0) < high]
            right = sum(signal in planted(t) for t in inside)
            bands.append({"confidence": f"{low} to {min(high, 1.0)}", "n": len(inside), "right": round(right / len(inside), 3) if inside else None})
        out[signal] = bands
    return out


def material(lab: Path) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
    facts = {r["uid"]: r["answer"] for r in base.rows(lab, "facts2.jsonl")}
    texts = [t for t in base.rows(lab, "texts.jsonl") if t["uid"] in facts]
    return texts, facts


async def design(ada: Ada, lab: Path) -> dict[str, Any]:
    texts, facts = material(lab)
    seen = [t for t in texts if t["split"] != "fresh" and (t["set"] in SOURCE or t["set"] in BUILDERS)]
    out: dict[str, Any] = {"seen": dict(Counter(t["set"] for t in seen))}
    held_real: list[tuple[dict[str, Any], dict[str, float]]] = []
    for source in sorted(set(SOURCE.values())):
        mine = [t for t in seen if SOURCE.get(t["set"]) == source]
        rest = [t for t in seen if SOURCE.get(t["set"]) != source]
        got = await answers(ada, f"out-{source}", rest, mine, facts)
        held_real += [(t, got[t["uid"]]) for t in mine]
    held_fraud: list[tuple[dict[str, Any], dict[str, float]]] = []
    for builder in BUILDERS:
        mine = [t for t in seen if t["set"] == builder]
        got = await answers(ada, f"out-{builder}", [t for t in seen if t["set"] != builder], mine, facts)
        held_fraud += [(t, got[t["uid"]]) for t in mine]
    # The strong line of each signal: the lowest step at which it fires strongly on at most 5% of every held-out source.
    lines: dict[str, float | None] = {}
    report: dict[str, Any] = {}
    for signal in SIGNALS:
        by_source: dict[str, dict[str, Any]] = {}
        for source in sorted(set(SOURCE.values())):
            mine = [f for t, f in held_real if SOURCE[t["set"]] == source]
            by_source[source] = {"n": len(mine)} | {str(s): sum(f.get(signal, 0) >= s for f in mine) for s in STEPS}
        ok = [s for s in STEPS if all(v[str(s)] <= 0.05 * v["n"] for v in by_source.values())]
        lines[signal] = None if signal == "aligned" or not ok else ok[0]
        report[signal] = {"fired strongly on held-out real, by line": by_source, "line": lines[signal]}
    out["strong lines"] = lines
    out["by signal"] = report
    out["each real source held out"] = table(held_real, lines)
    out["each fraud builder held out"] = table(held_fraud, lines)
    out["per signal, builders held out"] = per_signal(held_fraud + held_real)
    return out


async def test(ada: Ada, lab: Path) -> dict[str, Any]:
    texts, facts = material(lab)
    seen = [t for t in texts if t["split"] != "fresh" and (t["set"] in SOURCE or t["set"] in BUILDERS)]
    fresh = [t for t in texts if t["split"] == "fresh"]
    alone = {r["uid"]: r["answer"] for r in base.rows(lab, "alone2.jsonl")}
    got = await answers(ada, "all", seen, fresh, facts)
    rows = [(t, got[t["uid"]]) for t in fresh]
    out: dict[str, Any] = {"seeded": dict(Counter(t["set"] for t in seen)), "asked": dict(Counter(t["set"] for t in fresh)),
                           "strong lines": LINES, "signals": table(rows, LINES), "per signal": per_signal(rows),
                           "confidence": calibration(rows)}  # fmt: skip
    for t in seen + fresh:
        t["label"] = "fake" if t["set"].startswith("fraud") else "real"
    await base.model(ada, "layout", base.layout_spec("layout"), [{"data": base.layout(t["uid"], t["text"]), "outcome": t["label"]} for t in seen])
    out["layout only"] = base.score([(t, await base.decided(ada, "layout", base.layout(t["uid"], t["text"]))) for t in fresh])
    whole = [{"data": fraud_check.case(t["uid"], neutral(t, facts[t["uid"]])), "outcome": t["label"]} for t in seen]
    await base.model(ada, "whole", fraud_check.spec("whole"), whole)
    out["one whole-application ada model"] = base.score(
        [(t, await base.decided(ada, "whole", fraud_check.case(t["uid"], neutral(t, facts[t["uid"]])))) for t in fresh])
    out["claude alone"] = base.score([(t, {"outcome": alone[t["uid"]]["answer"], "ask": False} if t["uid"] in alone else None) for t in fresh])
    return out
