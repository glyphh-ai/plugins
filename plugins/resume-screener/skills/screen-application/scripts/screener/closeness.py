"""How close a resume and a cover letter are to real people's and to fakes: the simple check.

One Ada model, `closeness` (models/closeness.json; every role and why is in docs/closeness-model.md), holds two
labelled sets of applications read the same way: `fake` (the generated examples that ship with the plugin) and
`real` (resumes written by people: the person's own past applicants, loaded by them). A new resume is read into the
same sections, Ada is asked for the nearest applications it holds, and the answer is two numbers: how alike the
nearest fake is, and how alike the nearest real one is, each from 0 to 1, with the nearest few on each side.

Only words are compared. Before a section is handed to Ada its formatting is taken out (`neutral`): case, digits and
dates, punctuation and bullets, addresses and phone numbers, a resume site's stand-in words, and everything past
the section's first words, so that a long section and a short one are compared on the same footing. Section order
and headings never reach the model: each section is its own role.

The cover letter is compared apart: with fakes and with real letters if any are held. It does not move the
resume's two numbers."""

import json
import re
from typing import Any

from . import others, resumes, sections

RESUME: tuple[str, ...] = ("summary", "titles", "duties", "school", "skills")
KEPT: dict[str, int] = {"summary": 80, "titles": 30, "duties": 200, "school": 30, "skills": 60, "letter": 250}
SIDES: tuple[str, ...] = ("fake", "real")
SHOWN: int = 3  # the nearest few on each side that are shown
TIE: float = 0.02  # closer by less than this is "between the two"
WORD: re.Pattern[str] = re.compile(r"[a-z][a-z'+#.-]*[a-z+#]|[a-z]")
STAND_INS: re.Pattern[str] = re.compile(r"\b(?:company name|city|state|n/a|current|present)\b", re.I)
SPACED: re.Pattern[str] = re.compile(r" {2,}")
LINK: re.Pattern[str] = re.compile(r"(?:https?://|www\.)\S+", re.I)


def neutral(said: Any, keep: int) -> str:
    """A section's words with its formatting taken out: lower case, no addresses, phones, links, digits, dates,
    punctuation or a resume site's stand-in words, and only its first `keep` words."""
    text = " ".join(said) if isinstance(said, list) else str(said or "")
    text = STAND_INS.sub(" ", LINK.sub(" ", others.EMAIL.sub(" ", others.PHONE.sub(" ", text))))
    return " ".join(WORD.findall(text.lower())[:keep])


def lines(text: str) -> str:
    """A text whose line breaks came as runs of spaces (some sources flatten them) given its lines back; a text
    that has line breaks is left as it is."""
    return SPACED.sub("\n", text) if text.count("\n") < 5 else text


def parts(resume: str, letter: str = "") -> dict[str, str]:
    """The resume's sections and the cover letter, each as neutral words; a part with nothing in it is left out."""
    resume = lines(resume)
    cut = sections.split(resume)
    jobs = sections.entries(cut["experience"] or resume)
    duties = " ".join(ln for ln in cut["experience"].splitlines() if not resumes.SPAN.search(ln))
    read = {
        "summary": cut["summary"],
        "titles": [j["title"] for j in jobs if j["title"]],
        "duties": duties,
        "school": cut["education"],
        "skills": sections.terms(cut["skills"]),
        "letter": letter,
    }
    made = {name: neutral(said, KEPT[name]) for name, said in read.items()}
    return {name: words for name, words in made.items() if words}


def case(found: dict[str, str], mid: str, side: str = "", source: str = "", label: str = "") -> dict[str, Any]:
    """The application as the closeness model holds it and is asked about it. `label` is what is shown for it when
    it is someone's nearest: a fake's made-up name and role, a real one's source and category, never a person."""
    tag = json.dumps([side, label or source, mid])
    out: dict[str, Any] = {"who": {"s": {"source": source, "label": label, "id": mid}}}
    if side:
        out["side"] = {"s": {"is": side}}
    resume = {name: found[name] for name in RESUME if name in found}
    if "duties" in resume:  # the experience section's words are what every resume is compared on: without them, none
        out["resume"] = {"s": resume | {"resume_who": tag}}
    if "letter" in found:
        out["letter"] = {"s": {"letter": found["letter"], "letter_who": tag}}
    return out


def asks(asked: dict[str, Any]) -> list[dict[str, Any]]:
    """What to ask the model (ada_facts), each {key, data, top}: for the resume, and for the cover letter apart,
    the nearest applications on each side. Naming the side in the question puts that side's applications first;
    how alike each one is, is read from the part's own score in Ada's answer, which the side does not touch."""
    return [{"key": f"{part}:{side}", "data": {part: asked[part], "side": {"s": {"is": side}}}, "top": SHOWN + 1}
            for part in ("resume", "letter") if part in asked for side in SIDES]  # fmt: skip


def _score(tree: Any, part: str) -> float | None:
    """The part's own score in one of Ada's fact trees: how alike the two applications are on that part alone."""
    if not isinstance(tree, dict):
        return None
    if tree.get("key") == part and isinstance(tree.get("score"), int | float):
        return float(tree["score"])
    found = (_score(child, part) for child in tree.get("children") or [])
    return next((s for s in found if s is not None), None)


def _nearest(answer: Any, part: str, side: str, mine: str) -> list[dict[str, Any]]:
    """The side's nearest applications on the part, nearest first; the asked application itself is left out."""
    trees = next((v for v in answer.values() if isinstance(v, list)), []) if isinstance(answer, dict) else answer
    out = []
    for fact in trees or []:
        held_side, label, mid = others._tagged(fact.get("tree"))
        score = _score(fact.get("tree"), part)
        if held_side == side and mid != mine and score is not None:
            out.append({"closeness": round(score, 2), "like": label})
    return sorted(out, key=lambda n: -n["closeness"])[:SHOWN]


def _reads(fake: dict[str, Any], real: dict[str, Any]) -> str:
    a, b = fake["closeness"], real["closeness"]
    if a is None and b is None:
        return "nothing is held to compare it with"
    if b is None:
        return "only fakes are held to compare it with"
    if a is None:
        return "only real ones are held to compare it with"
    return "reads like the fakes" if a - b >= TIE else "reads like real people" if b - a >= TIE else "between the two"


def decision(answer: dict[str, Any]) -> dict[str, Any]:
    """Ada's own decision on the application (ada_decide with its facts): the outcome, Ada's confidence in it,
    whether Ada would ask a person first, and Ada's fact tree for it, exactly as Ada gave it."""
    outcome = answer.get("outcome")
    p = (answer.get("probabilities") or {}).get(outcome or "")
    return {
        "outcome": outcome,
        "confidence": round(float(p), 2) if isinstance(p, int | float) else None,
        "ask": bool(answer.get("ask")),
        "probabilities": answer.get("probabilities") or {},
        "facts": answer.get("facts"),
    }


def result(asked: dict[str, Any], facts: dict[str, Any]) -> dict[str, Any]:
    """The answer: for the resume, and for the cover letter apart, {fake, real, reads}; each side is its closeness
    (0 to 1; None when the model holds nothing on that side for this part) and its nearest few. `facts` is Ada's
    answer to each of `asks`, by key."""
    mine = asked["who"]["s"]["id"]
    out: dict[str, Any] = {}
    for part in ("resume", "letter"):
        if part not in asked:
            continue
        sides = {}
        for side in SIDES:
            near = _nearest(facts.get(f"{part}:{side}"), part, side, mine)
            sides[side] = {"closeness": near[0]["closeness"] if near else None, "nearest": near}
        out[part] = sides | {"reads": _reads(sides["fake"], sides["real"])}
    return out or {"reads": "there was nothing to read"}
