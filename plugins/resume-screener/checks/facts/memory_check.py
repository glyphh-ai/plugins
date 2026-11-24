"""The memory signals on real Ada (docs/check-6-protocol.md, check-7-protocol.md): `pattern` (the same body under
a new name), `shared` (the same email and phone under a new name) and `name` (the same name with other contact
details), which need applications held from before. Real resumes' bodies, each given a contact block made by code
so that every person has a name, a phone and an email of their own: 60 are held as screened; code makes the three
variants from them; 60 others are the controls. `design`: check 6's unseen sources (now seen); `test`: the fresh
ones."""

import re
from collections import Counter
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import Any

import facts_check as base
import lab2
from screener import applicants, others, steps

Ada = Callable[..., Awaitable[Any]]
EACH: int = 60
MODEL: str = "memory"


def own(k: int) -> list[str]:
    """Person k's contact block: a name no one else here has, a phone and an email address of their own."""
    first, last = lab2.FIRST[k % 16], lab2.LAST[(k // 16 + k) % 16]
    city, state, code, zipc = lab2.HOMES[k % len(lab2.HOMES)]
    return [f"{first} {last}", f"{city}, {state} | ({code}) 555-{1000 + k:04d} | {first.lower()}.{last.lower()}{k}@mailbox.example",
            f"{100 + k} Cedar St, {city}, {state} {zipc}"]  # fmt: skip


def case(uid: str, text: str) -> dict[str, Any]:
    raw, _ = applicants.of_given(uid, {"resume": text}, raw=True)
    assert raw is not None
    return others.prints(raw)


async def asked(ada: Ada, held: dict[str, Any]) -> dict[str, Any]:
    near = {}
    for part in others.PARTS:
        if part in held:
            got = await ada("POST", f"/v1/models/{MODEL}/facts", {"data": {part: held[part]}, "top": others.TOP})
            near[part] = others.nearest(got)
    return others.compared(lambda q: near[next(iter(q))], held)


def bodies(lab: Path, mode: str) -> list[str]:
    """The real resumes' bodies, without any contact block."""
    texts = sorted(base.rows(lab, "texts.jsonl"), key=lambda t: t["uid"])
    if mode == "design":
        mine = [t for t in texts if t["split"] == "test" and t.get("contact") == "added" and t["set"] in ("up", "lrec-real")]
        return [t["text"].partition("\n\n")[2] for t in mine]
    return [t["text"] for t in texts if t["split"] == "fresh" and t["label"] == "real" and t["set"] != "gh2"]


async def run(ada: Ada, lab: Path, mode: str) -> dict[str, Any]:
    found = bodies(lab, mode)
    screened, controls, donors = found[:EACH], found[EACH : 2 * EACH], found[2 * EACH : 3 * EACH] or found[EACH : 2 * EACH]

    def person(k: int, body: str) -> str:
        return "\n".join(own(k)) + "\n\n" + body

    await ada("POST", "/v1/models", {"name": MODEL, "spec": steps.models()["others"]["spec"] | {"name": MODEL}})
    known = [{"data": case(f"s{k}", person(k, body)), "outcome": "alone"} for k, body in enumerate(screened)]
    await ada("POST", f"/v1/models/{MODEL}/record_many", {"cases": known})
    kinds = ("same body, new name", "same email and phone, new name", "same name, new contacts", "control")
    flags: dict[str, Counter[str]] = {k: Counter() for k in kinds}
    body_sims: dict[str, list[float]] = {"same body, new name": [], "control": []}
    for n, body in enumerate(screened):
        name, line, _street = own(n)
        fresh = own(2 * EACH + n)
        other = donors[n % len(donors)]
        phone_email = re.sub(r"^[^|]*\|", "Elsewhere, ZZ |", line)  # the held one's phone and email, another home
        made = {
            "same body, new name": "\n".join(fresh) + "\n\n" + body,
            "same email and phone, new name": "\n".join([fresh[0], phone_email, fresh[2]]) + "\n\n" + other,
            "same name, new contacts": "\n".join([name, fresh[1], fresh[2]]) + "\n\n" + other,
        }
        for kind, text in made.items():
            got = await asked(ada, case(f"v{n}-{kind}", text))
            flags[kind].update(got["flags"])
            flags[kind]["n"] += 1
            if kind in body_sims and "body" in got["near"]:
                body_sims[kind].append(got["near"]["body"]["sim"])
    for k, body in enumerate(controls):
        got = await asked(ada, case(f"c{k}", person(EACH + k, body)))
        flags["control"].update(got["flags"])
        flags["control"]["n"] += 1
        if "body" in got["near"]:
            body_sims["control"].append(got["near"]["body"]["sim"])
    spread = {k: {"n": len(v), "min": min(v), "max": max(v)} for k, v in body_sims.items() if v}
    return {"mode": mode, "held": len(screened), "controls": len(controls), "ceilings": others.CEILING,
            "flags": {k: dict(v) for k, v in flags.items()}, "nearest body, how alike": spread}  # fmt: skip
