"""Check 6 on real Ada (docs/check-6-protocol.md): the fraud model over the agent's reading, seeded and learned on
the seen sets' seed split, asked about the validation split (design) or the unseen test; which signals fired; and
beside it the layout-only control and the baselines on the same texts. `ada` is the async caller the other checks
use. Counting is all the analysis does: no model but Ada is fitted anywhere."""

from collections import Counter
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import Any

import facts_check as base
import reading2
from screener import steps

Ada = Callable[..., Awaitable[Any]]
# The model's named parts and the facts of the reading in each. `pattern`, `timestamps` and `shared` are parts of the
# product's model too; they come from Ada's memory of other applications and from the email, not from the reading,
# and a text read alone has none of them (a part with nothing in it is left out of the case).
PARTS: dict[str, tuple[str, ...]] = {
    "location": ("places", "phone", "email_time"),
    "name": ("name_and_email",),
    "address": ("postal_address",),
    "aligned": ("dates", "study_and_work", "existed_then", "seniority", "role_at_employer", "letter_and_resume"),
    "built": ("employers", "schools", "one_off_details", "checkable_claims", "generic_body", "mirrors_a_posting",
              "breadth_of_skills", "path", "gaps", "overlaps", "short_stints", "unrelated_work", "loose_ends",
              "education_path", "fits_one_role"),
}  # fmt: skip
DROPPED: frozenset[str] = frozenset()  # decided on the seen sets
ASK_BELOW: float = 0.7
PLANTED: dict[str, str] = {"location": "location", "name": "name", "address": "address", "dates": "aligned", "built": "built"}
SCALES: frozenset[str] = frozenset(name for name, schema, _ in reading2.FACTS if schema.get("type") == "integer")


def fired(a: dict[str, Any]) -> list[str]:
    """Which signals fire on a reading, each on its own: one is enough to flag. Set on the seen sets' seed (design
    run 1), where a first, wider version flagged 60% of real people:
    - location: the phone or the email's time does not fit the stated home. Not `places` alone: on the seed it fired
      on 7% of real resumes, most of them an artefact of the contact blocks code gave them.
    - name: the email address is named for someone else (2 of 300 real, 62 of 176 fraud-shaped).
    - address: a mail drop or virtual office, or an address in another place than the home (2 real, 32 fraud).
    - aligned: only that something named did not exist when the resume says it did, and the agent is not unsure of
      it. NOT dates or study against work: on the seed, dates that do not line up were found in 46% of real
      resumes and 30% of the fraud-shaped ones. Real people's dates are messier than built ones. Those facts stay
      in Ada's model, to be weighed with the rest, and never flag alone.
    - built: employers described vaguely with at most one checkable claim (vague employers: 1 of 300 real, 47 of 176
      fraud). Not 'mirrors a posting' or 'generic': real resumes scored as high."""
    wrong = "does_not_line_up"
    found = {
        "location": a["phone"] == "does_not_fit_the_location" or a["email_time"] == "does_not_fit_the_location",
        "name": a["name_and_email"] == "another_name",
        "address": a["postal_address"] in ("mail_drop_or_virtual", "does_not_fit_the_location"),
        "aligned": a["existed_then"] == wrong and a.get("existed_then_sure") in ("fairly_sure", "sure"),
        "built": a["employers"] == "vague" and a["checkable_claims"] <= 1,
    }
    return [part for part, there in found.items() if there]


def spec(name: str) -> dict[str, Any]:
    layers = []
    for part, facts in PARTS.items():
        roles = []
        for fact in facts:
            if fact in DROPPED:
                continue
            role: dict[str, Any] = {"name": fact}
            if fact in SCALES:
                role["numeric_config"] = {"min_value": 0, "max_value": 3, "bin_width": 1}
            roles.append(role)
        if roles:
            layers.append({"name": part, "similarity_weight": 1.0, "segments": [{"name": "s", "roles": roles}]})
    key = {"name": "key", "similarity_weight": 0, "segments": [{"name": "s", "roles": [
        {"name": "id", "key_part": True, "similarity_weight": 0}]}]}  # fmt: skip
    return {"name": name, "layers": [*layers, key], "output": {"ask_below": ASK_BELOW}}


def case(uid: str, a: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {"key": {"s": {"id": uid}}}
    for part, facts in PARTS.items():
        roles = {f: a[f] for f in facts if f not in DROPPED and f in a}
        if roles:
            out[part] = {"s": roles}
    return out


def flags(rows: list[tuple[dict[str, Any], dict[str, Any] | None, list[str]]]) -> dict[str, Any]:
    """By set: decided fake by Ada, a signal fired, flagged (either), and how many Ada would ask about."""
    out: dict[str, Any] = {}
    groups: dict[str, list[tuple[dict[str, Any], dict[str, Any] | None, list[str]]]] = {}
    for row in rows:
        t = row[0]
        groups.setdefault(t["set"], []).append(row)
        if "kind" in t:
            groups.setdefault(f"{t['set']} {t['care']}", []).append(row)
        if t.get("form"):
            groups.setdefault(f"{t['set']} in the form of {t['form']}", []).append(row)
        if t["label"] == "real" and "polished" not in t["set"]:
            groups.setdefault("real, contact block made by code" if t.get("contact") else "real, as the source gave it", []).append(row)
            groups.setdefault("all real", []).append(row)
    for name, group in sorted(groups.items()):
        ada_fake = sum((s or {}).get("outcome") == "fake" for _, s, _ in group)
        any_fired = sum(bool(f) for _, _, f in group)
        either = sum((s or {}).get("outcome") == "fake" or bool(f) for _, s, f in group)
        out[name] = {"n": len(group), "ada says fake": ada_fake, "a signal fired": any_fired, "flagged": either,
                     "flagged share": round(either / len(group), 3), "ada would ask": sum(bool((s or {}).get("ask")) for _, s, _ in group),
                     "which fired": dict(Counter(p for _, _, f in group for p in f))}  # fmt: skip
    return out


def per_signal(rows: list[tuple[dict[str, Any], dict[str, Any] | None, list[str]]]) -> dict[str, Any]:
    """For each planted signal alone: how often its own part fired, careless and careful; and how often that part
    fired on real texts."""
    out: dict[str, Any] = {}
    real = [f for t, _, f in rows if t["label"] == "real" and "polished" not in t["set"]]
    for planted, part in PLANTED.items():
        line: dict[str, Any] = {}
        for care in ("careless", "careful"):
            mine = [f for t, _, f in rows if t.get("kind") == planted and t.get("care") == care]
            line[care] = {"n": len(mine), "its part fired": sum(part in f for f in mine)}
        line["false alarms on real"] = {"n": len(real), "fired": sum(part in f for f in real)}
        out[planted] = line
    return out


def spread(seed: list[dict[str, Any]], facts: dict[str, dict[str, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for fact, _, _ in reading2.FACTS:
        table: dict[str, Counter[str]] = {}
        for t in seed:
            if t["uid"] in facts:
                table.setdefault(t["set"], Counter())[str(facts[t["uid"]].get(fact))] += 1
        out[fact] = {k: dict(sorted(v.items())) for k, v in sorted(table.items())}
    return out


async def run(ada: Ada, lab: Path, mode: str) -> dict[str, Any]:
    texts = [t for t in base.rows(lab, "texts.jsonl") if t["set"] != "lrec-enhanced"]
    facts = {r["uid"]: r["answer"] for r in base.rows(lab, "facts2.jsonl")}
    alone = {r["uid"]: r["answer"] for r in base.rows(lab, "alone2.jsonl")} if (lab / "alone2.jsonl").exists() else {}
    seed = [t for t in texts if t["split"] == "seed" and t["uid"] in facts]
    asked = [t for t in texts if t["split"] == ("validation" if mode == "design" else "test")]
    out: dict[str, Any] = {"mode": mode, "seeded": dict(Counter(t["set"] for t in seed)), "asked": dict(Counter(t["set"] for t in asked)),
                           "no reading": sum(t["uid"] not in facts for t in asked), "dropped facts": sorted(DROPPED)}  # fmt: skip
    learned = await base.model(ada, "fraud", spec("fraud"), [{"data": case(t["uid"], facts[t["uid"]]), "outcome": t["label"]} for t in seed])
    out["learned"] = learned
    rows = []
    for t in asked:
        if t["uid"] in facts:
            rows.append((t, await base.decided(ada, "fraud", case(t["uid"], facts[t["uid"]])), fired(facts[t["uid"]])))
        else:
            rows.append((t, None, []))
    out["fraud model"] = flags(rows)
    out["per signal"] = per_signal(rows)
    out["confidence"] = base.bands([(t, s) for t, s, _ in rows])
    # The controls and baselines: each right when it says `fake` of a fake and `real` of a real.
    await base.model(ada, "layout", base.layout_spec("layout"), [{"data": base.layout(t["uid"], t["text"]), "outcome": t["label"]} for t in seed])
    out["layout only"] = base.score([(t, await base.decided(ada, "layout", base.layout(t["uid"], t["text"]))) for t in asked])
    known = [{"data": c | {"side": {"s": {"is": t["label"]}}}, "outcome": t["label"]} for t in seed if (c := base.words_case(t["uid"], t["text"]))]
    await base.model(ada, "words", steps.models()["closeness"]["spec"], known, learn=False)
    worded = []
    for t in asked:
        c = base.words_case(t["uid"], t["text"])
        worded.append((t, await base.decided(ada, "words", {"resume": c["resume"]}) if c else None))
    out["words only"] = base.score(worded)
    out["claude alone"] = base.score([(t, {"outcome": alone[t["uid"]]["answer"], "ask": False} if t["uid"] in alone else None) for t in asked])
    out["ada alone (no fired rule)"] = base.score([(t, s) for t, s, _ in rows])
    if mode == "design":
        out["facts on the seed, by set"] = spread(seed, facts)
    return out
