"""Check 6's memory signals on real Ada (docs/check-6-protocol.md): `pattern` (the same body under a new name),
`shared` (the same email and phone under a new name) and `name` (the same name with other contact details), which
need applications held from before. On unseen real resumes that carry a contact block made by code: 60 are held as
screened; code makes the three variants from them; 60 others, each with its own block, are the controls."""

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


def split(text: str) -> tuple[list[str], str]:
    """A text with a code-made contact block: the block's three lines, and the body."""
    head, _, body = text.partition("\n\n")
    return head.splitlines(), body


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


async def run(ada: Ada, lab: Path) -> dict[str, Any]:
    texts = [t for t in base.rows(lab, "texts.jsonl") if t["split"] == "test" and t.get("contact") == "added"
             and t["set"] in ("up", "lrec-real")]  # fmt: skip
    texts = sorted(texts, key=lambda t: t["uid"])
    screened, controls, donors = texts[:EACH], texts[EACH : 2 * EACH], texts[2 * EACH : 3 * EACH]
    donors = donors or controls
    # Every person here gets a name of their own (the contact blocks' small name lists repeat names, which would
    # make namesakes of strangers): person k is the k-th of the 256 first and last name pairs.
    for k, t in enumerate([*screened, *controls]):
        t["text"] = "\n".join(own(k)) + "\n\n" + split(t["text"])[1]
    await ada("POST", "/v1/models", {"name": MODEL, "spec": steps.models()["others"]["spec"] | {"name": MODEL}})
    known = [{"data": case(t["uid"], t["text"]), "outcome": "alone"} for t in screened]
    for at in range(0, len(known), 250):
        await ada("POST", f"/v1/models/{MODEL}/record_many", {"cases": known[at : at + 250]})
    flags: dict[str, Counter[str]] = {k: Counter() for k in ("same body, new name", "same email and phone, new name",
                                                              "same name, new contacts", "control")}  # fmt: skip
    for n, t in enumerate(screened):
        (name, line, _street), body = split(t["text"])
        fresh = own(2 * EACH + n)
        other_body = split(donors[n % len(donors)]["text"])[1]
        phone_email = re.sub(r"^[^|]*\|", "Elsewhere, ZZ |", line)  # the held one's phone and email, another home
        made = {
            "same body, new name": "\n".join(fresh) + "\n\n" + body,
            "same email and phone, new name": "\n".join([fresh[0], phone_email, fresh[2]]) + "\n\n" + other_body,
            "same name, new contacts": "\n".join([name, fresh[1], fresh[2]]) + "\n\n" + other_body,
        }
        for kind, text in made.items():
            flags[kind].update((await asked(ada, case(f"{t['uid']}-{kind}", text)))["flags"])
            flags[kind]["n"] += 1
    for t in controls:
        flags["control"].update((await asked(ada, case(t["uid"], t["text"])))["flags"])
        flags["control"]["n"] += 1
    return {"held": len(screened), "controls": len(controls), "flags": {k: dict(v) for k, v in flags.items()}}
