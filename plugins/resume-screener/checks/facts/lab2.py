"""The workbench of check 6 (docs/check-6-protocol.md): fraud. It adds to check 5's texts (lab.py): contact
blocks on half of the real resumes that have none (made by code, consistent, so that having one is not a mark of a
fake), and fraud-shaped fakes: invented people with the defects the documented schemes leave (docs/
fraud-indicators.md), one signal at a time and in combination, careless and careful. Then Claude reads every
text with the fraud reading (reading2.py).

    python lab2.py contacts            add consistent contact blocks to half of the real texts without one
    python lab2.py write F1|F2         Claude writes the fraud-shaped fakes: F1 seen (Haiku), F2 unseen (Opus)
    python lab2.py read seen|unseen    Claude reads each text into fraud facts -> facts2.jsonl
    python lab2.py alone seen|unseen   Claude alone: real or fake -> alone2.jsonl"""

import hashlib
import json
import random
import sys
from typing import Any

import lab
import reading2

HOMES: tuple[tuple[str, str, str, str], ...] = (
    ("Austin", "TX", "512", "78704"), ("Columbus", "OH", "614", "43215"), ("Denver", "CO", "303", "80205"),
    ("Tampa", "FL", "813", "33606"), ("Portland", "OR", "503", "97214"), ("Raleigh", "NC", "919", "27603"),
    ("Phoenix", "AZ", "602", "85004"), ("Boston", "MA", "617", "02118"), ("Omaha", "NE", "402", "68102"),
    ("Sacramento", "CA", "916", "95814"), ("Louisville", "KY", "502", "40202"), ("Madison", "WI", "608", "53703"))  # fmt: skip
FIRST: tuple[str, ...] = ("Dana", "Marcus", "Priya", "Elena", "Tyrone", "Hannah", "Luis", "Mei", "Andre", "Sofia",
                          "Caleb", "Nadia", "Owen", "Grace", "Hector", "Yuki")  # fmt: skip
LAST: tuple[str, ...] = ("Whitfield", "Okafor", "Brennan", "Castillo", "Lindgren", "Mbeki", "Havel", "Sato",
                         "Delgado", "Novak", "Ferris", "Osei", "Kowalski", "Barros", "Hale", "Iyer")  # fmt: skip
STREETS: tuple[str, ...] = ("Maple Ave", "Cedar St", "Juniper Ln", "Harlow Rd", "Bishop St", "Tanager Way")
NEEDS_CONTACT: tuple[str, ...] = ("lc", "lc-polished", "up", "lrec-real")  # real sets that give no contact details
# One signal at a time, then together: what the builder plants. Each is one of the model's named parts.
PLANTS: dict[str, str] = {
    "location": "the places do not fit together: the phone number's area or country code belongs somewhere other than the stated home, and a job or school is somewhere the person could not have been at that time",
    "name": "the email address is plainly named for a different person than the name at the top",
    "address": "the postal address is a mail drop, a PO box or a virtual office, or is in a different city from the stated home",
    "dates": "the dates and facts do not hold together: a degree dated after the senior job that needs it, two full-time jobs in different cities over the same years, or years of experience with a tool or at a company from before it existed",
    "built": "the history is built to a job posting and cannot be checked: employers described vaguely (a 'leading fintech startup', 'confidential client'), duties that are the posting's requirement list turned into the past tense, a skills list far wider than the jobs could teach, and no particular detail anywhere",
}
KINDS: tuple[str, ...] = (*PLANTS, "location+name", "dates+built", "name+address+dates")
CARE: dict[str, str] = {
    "careless": "Make no effort to hide it: a careful reader would notice at once.",
    "careful": "Hide it well: everything else must be consistent and convincing, and the defect small enough that only a careful check finds it.",
}
F1: str = (
    "Below are two resumes from a public collection, to show the FORM only.\n\n<form>\n{one}\n</form>\n\n<form>\n{two}\n"
    "</form>\n\nWrite the resume of an invented applicant in this category: {category}. Follow the form of the "
    "examples (their kinds of sections, their stand-in words where they use them, about {words} words), and begin "
    "with a contact block: name, city and state, phone, email address, street address. This applicant is a "
    "fraudulent one, and the resume must carry this defect: {plant}. {care} Do not mention the defect or explain "
    "it. Invent every fact; copy no sentence from the examples."
)
F2: str = (
    "Here is one real resume. Use it only for its form.\n\n<form>\n{one}\n</form>\n\nYou are building test material "
    "for a fraud team. Produce a resume for a person who does not exist, as a fraudulent applicant ring would "
    "produce it, in the same form and at about the same length ({words} words), in another line of work than the "
    "example. Put the applicant's name, home city, phone, email and street address at the top. What gives this "
    "one away: {plant}. {care} Say nothing about the test or the flaw. Every fact is invented; nothing is copied "
    "from the example."
)


def block(seed: str, home: tuple[str, str, str, str] | None = None) -> str:
    """A consistent contact block made by code: a name, a home, a phone with the home's area code, an email
    address named for the same person, a street address there."""
    rng = random.Random(f"glyphh-check6-contact:{seed}")
    first, last = rng.choice(FIRST), rng.choice(LAST)
    city, state, code, zipc = home or rng.choice(HOMES)
    number = f"({code}) {rng.randrange(200, 999)}-{rng.randrange(1000, 9999)}"
    return (f"{first} {last}\n{city}, {state} | {number} | {first.lower()}.{last.lower()}{rng.randrange(10, 99)}@mailbox.example\n"
            f"{rng.randrange(100, 9900)} {rng.choice(STREETS)}, {city}, {state} {zipc}\n\n")  # fmt: skip


def contacts() -> None:
    """Half of the real texts that give no contact details get a consistent block (which half: by the id's hash)."""
    texts = lab.load("texts.jsonl")
    n = 0
    for t in texts:
        half = int(hashlib.sha256(f"glyphh-check6-half:{t['uid']}".encode()).hexdigest(), 16) % 2 == 0
        if t["set"] in NEEDS_CONTACT and half and not t.get("contact"):
            t["text"], t["contact"] = (block(t["uid"]) + t["text"])[: lab.CUT], "added"
            n += 1
    lab.save("texts.jsonl", texts)
    print(f"{n} real texts given a contact block")


def writing(which: str) -> tuple[str, list[tuple[str, str, dict[str, Any]]]]:
    texts = lab.load("texts.jsonl")
    rng = random.Random(f"glyphh-check6-{which}")
    out = []
    if which == "F1":
        form = [t for t in texts if t["set"] == "lc" and t["split"] == "form"]
        per = 15  # of each kind and care: 11 seeded, 4 validation
        for kind in KINDS:
            for care in CARE:
                for n in range(per):
                    one, two = rng.sample(form, 2)
                    plant = "; and ".join(PLANTS[k] for k in kind.split("+"))
                    prompt = F1.format(one=one["text"], two=two["text"], category=one["category"].replace("-", " ").lower(),
                                       words=len(one["text"].split()), plant=plant, care=CARE[care])  # fmt: skip
                    made = lab.row(f"fraud-seen:{kind}:{care}:{n}", "fraud-seen", "seed" if n < 11 else "validation", "")
                    out.append((f"F1{len(out)}", prompt, made | {"kind": kind, "care": care}))
        return lab.SMALL, out
    real = [t for t in texts if t["set"] in ("gh", "up", "lrec-real")]
    for kind in KINDS:
        for care in CARE:
            for n in range(12):
                one = rng.choice(real)
                plant = "; and ".join(PLANTS[k] for k in kind.split("+"))
                prompt = F2.format(one=one["text"], words=len(one["text"].split()), plant=plant, care=CARE[care])
                made = lab.row(f"fraud-unseen:{kind}:{care}:{n}", "fraud-unseen", "test", "")
                out.append((f"F2{len(out)}", prompt, made | {"kind": kind, "care": care, "form": one["set"]}))
    return lab.OTHER, out


def write(which: str) -> None:
    model, asks = writing(which)
    made = lab.batch(f"write {which}", model, [(cid, {"system": lab.WRITER, "messages": [{"role": "user", "content": p}]})
                                               for cid, p, _ in asks], 3000)  # fmt: skip
    rows = [r | {"text": lab.plain(made[cid])} for cid, _, r in asks if len(made.get(cid, "")) > 300]
    kept = [t for t in lab.load("texts.jsonl") if t["uid"] not in {r["uid"] for r in rows}]
    lab.save("texts.jsonl", kept + rows)


SEEN: tuple[str, ...] = (*lab.SEEN, "fraud-seen")
SKIPPED: tuple[str, ...] = ("lrec-enhanced",)  # not read: AI-enhanced is not the question


def asked(stage: str, into: str, which: str, system: str, schema: dict[str, Any]) -> None:
    have = {r["uid"] for r in lab.load(into)}
    texts = [t for t in lab.load("texts.jsonl") if t["split"] in ("seed", "validation", "test") and t["set"] not in SKIPPED]
    todo = [t for t in texts if (t["set"] in SEEN) == (which == "seen") and t["uid"] not in have
            and (stage == "read" or t["split"] != "seed")]  # fmt: skip
    fmt = {"format": {"type": "json_schema", "schema": schema}, "effort": "low"}
    asks = [(t["uid"], {"system": system, "output_config": fmt, "messages": [{"role": "user", "content": reading2.user(t["text"])}]})
            for t in todo]  # fmt: skip
    got = lab.batch(f"{stage}2 {which}", lab.READER, asks, 2500) if asks else {}
    rows = []
    for t in todo:
        try:
            rows.append({"uid": t["uid"], "answer": json.loads(got[t["uid"]])})
        except (KeyError, ValueError):
            continue
    lab.save(into, lab.load(into) + rows)
    print(f"{into}: {len(rows)} added, {len(todo) - len(rows)} missing")


if __name__ == "__main__":
    what, *rest = sys.argv[1:]
    lab.LABEL |= {"fraud-seen": "fake", "fraud-unseen": "fake"}
    if what == "contacts":
        contacts()
    elif what == "write":
        write(rest[0])
    elif what == "read":
        asked("read", "facts2.jsonl", rest[0], reading2.SYSTEM, reading2.SCHEMA)
    elif what == "alone":
        asked("alone", "alone2.jsonl", rest[0], reading2.ALONE_SYSTEM, reading2.ALONE_SCHEMA)
