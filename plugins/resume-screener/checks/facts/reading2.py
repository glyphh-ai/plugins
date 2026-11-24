"""The agent's reading of an application for fraud (check 6): does it describe a person whose facts line up, or
one who was invented or misrepresented? One fixed prompt and one fixed schema for every application. The agent
reports what does and does not line up, quoting the evidence; where an answer needs knowledge of the world (did
that product exist then?) it says how sure it is. It is never asked whether the applicant is real: Ada decides
that, from precedent over these facts. Written before any text was read with it."""

from typing import Any

SCALE: dict[str, Any] = {"type": "integer", "enum": [0, 1, 2, 3]}
SURE: dict[str, Any] = {"type": "string", "enum": ["not_applicable", "unsure", "fairly_sure", "sure"]}
QUOTE: dict[str, Any] = {"type": "string"}


def kind(*values: str) -> dict[str, Any]:
    return {"type": "string", "enum": list(values)}


LINE_UP = ("lines_up", "minor_doubt", "does_not_line_up", "cannot_tell")

# What lines up, each with the evidence quoted: (name, schema, what it means, whether evidence is quoted).
CHECKS: list[tuple[str, dict[str, Any], str]] = [
    ("dates", kind(*LINE_UP), "Do the dates hold together? Does not line up: jobs or study that could not have happened as dated (impossible overlaps of full-time roles, an end before a start, a span that contradicts another line)."),
    ("study_and_work", kind(*LINE_UP), "Do education and career fit in time and kind? Does not line up: a degree dated after the job that needs it, senior work before or during school with no explanation, a degree that does not lead to the work."),
    ("existed_then", kind(*LINE_UP), "Did the employers, products, tools and technologies exist when the resume says the person worked with them, and for as long as claimed? Use what you know of the world. Cannot tell: nothing named or dated to check."),
    ("places", kind(*LINE_UP), "Location. Do the places fit together: where the person says they live, where the jobs and schools are, and how the person could have been in each when dated? Cannot tell: no places given."),
    ("phone", kind("fits_the_location", "does_not_fit_the_location", "no_phone", "cannot_tell"), "Location. Does the phone number's country or area code fit where the person says they live? Use what you know of dialling codes."),
    ("email_time", kind("fits_the_location", "does_not_fit_the_location", "no_email_time"), "Location. If a line 'Email sent:' gives the time and UTC offset the email was written at: do that offset and hour fit where the person says they live? No such line: no_email_time."),
    ("name_and_email", kind("fits", "another_name", "no_name_in_address", "no_email"), "Name. Is the email address's own name part this applicant's name (or a plain variant of it), or plainly someone else's?"),
    ("postal_address", kind("full", "city_only", "none", "mail_drop_or_virtual", "does_not_fit_the_location"), "Address. The postal address given: a full street address; only a city or region; none; one that reads as a mail drop, PO box, virtual office or forwarding service; or one that does not fit the rest (another city or country than the claimed home)."),
    ("seniority", kind(*LINE_UP), "Do titles, duties and years fit each other? Does not line up: senior titles with junior duties or after too few years, or duties far beyond the title."),
    ("role_at_employer", kind(*LINE_UP), "Is each role one that the named employer, or that kind of employer, would have? Cannot tell: employers not named."),
    ("letter_and_resume", kind("no_letter", "lines_up", "minor_doubt", "does_not_line_up"), "If there is a cover letter: do its facts agree with the resume's (names, employers, years, role)?"),
]  # fmt: skip

# What can be checked, and how the history is built.
BUILD: list[tuple[str, dict[str, Any], str]] = [
    ("employers", kind("named_and_checkable", "named_but_unknown", "vague", "withheld_by_the_source"), "How the employers are given: real organisations one could check; names one cannot place; vague descriptions ('a fintech startup', 'various clients', 'confidential'); or replaced by a site's stand-in words such as 'Company Name' (withheld by the source: this says nothing about the person)."),
    ("schools", kind("named_and_checkable", "named_but_unknown", "vague", "none_given", "withheld_by_the_source"), "The same for schools and qualifications."),
    ("one_off_details", SCALE, "Details only this person would have: something particular that happened, a named local thing, an unusual task (0 none, 3 many)."),
    ("checkable_claims", SCALE, "Claims a referee or a record could confirm or deny: named projects, clients, systems, publications, licences with numbers, dated events (0 none, 3 many)."),
    ("generic_body", SCALE, "How much of the work described could be pasted under any name in the trade (0 little, 3 nearly all)."),
    ("mirrors_a_posting", SCALE, "How much the history reads as a job posting turned into a past: requirement lists as duties, every keyword of one role present, nothing else (0 not at all, 3 entirely)."),
    ("breadth_of_skills", kind("fits_the_history", "wider_than_the_history", "implausibly_wide"), "Do the skills claimed fit what the history could have taught?"),
    ("path", kind("steady_climb", "sideways_or_mixed", "change_of_field", "unclear"), "The shape of the career: each job a step up in one field; sideways moves or a mix; or a change of field."),
    ("gaps", kind("none", "some", "unclear"), "Are there gaps of a year or more between jobs?"),
    ("overlaps", kind("none", "some", "unclear"), "Do any jobs overlap in time?"),
    ("short_stints", kind("none", "some", "unclear"), "Is any job shorter than a year?"),
    ("unrelated_work", SCALE, "How much of the history has nothing to do with the main line of work (0 none, 3 a lot)."),
    ("loose_ends", SCALE, "Things that do not serve the application: odd jobs, unfinished study, hobbies, asides, leftovers (0 none, 3 many)."),
    ("education_path", kind("none_given", "straight", "winding"), "Education: not given; one straight line; or winding (changes, pauses, late or unfinished study)."),
    ("fits_one_role", SCALE, "How neatly everything lines up behind a single target role (0 not at all, 3 perfectly)."),
]  # fmt: skip

EVIDENCE: tuple[str, ...] = tuple(name for name, _, _ in CHECKS)
FACTS: list[tuple[str, dict[str, Any], str]] = [*CHECKS, *BUILD]

_props: dict[str, Any] = {}
for _name, _schema, _ in FACTS:
    _props[_name] = _schema
    if _name in EVIDENCE:
        _props[f"{_name}_evidence"] = QUOTE
_props["existed_then_sure"] = SURE
SCHEMA: dict[str, Any] = {"type": "object", "properties": _props, "required": list(_props), "additionalProperties": False}

SYSTEM: str = (
    "You read job applications the way a careful investigator checks a file: you report what lines up and what "
    "does not. You are not asked whether the applicant is genuine and you must not guess at it: only observe and "
    "quote. Layout, section order, headings, spelling slips, polish and stand-in words such as 'Company Name' or "
    "'City, State' say nothing and must not move any answer.\n\n"
    "For each of the first twelve items give the finding, and in the matching `_evidence` field quote the few "
    "words of the application the finding rests on (at most 25 words; an empty string when nothing is wrong or "
    "nothing can be told). Never quote a person's name, email address or phone number: write "
    "[name], [email] or [phone] in their place. For `existed_then`, also say in `existed_then_sure` how sure you are "
    "of what you know about when those things existed ('not_applicable' when there was nothing to check). Say "
    "'does_not_line_up' only for something a reader could point to; a doubt without a line to point to is "
    "'minor_doubt'. Answer with the JSON object only.\n\nThe items:\n"
    + "\n".join(f"- {name}: {said}" for name, _, said in FACTS)
)


def user(text: str) -> str:
    return f"The application:\n\n<application>\n{text}\n</application>"


# Claude alone (a baseline): asked directly, with no Ada.
ALONE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {"answer": kind("real", "fake"), "confidence": {"type": "integer"}},
    "required": ["answer", "confidence"],
    "additionalProperties": False,
}
ALONE_SYSTEM: str = (
    "You are shown one job application. Decide whether it is a genuine application from a real person describing "
    "their own history (`real`; it may have been polished with AI, which does not matter) or a fraudulent one: an "
    "invented or misrepresented person (`fake`). Layout and stand-in words such as 'Company Name' tell you nothing. "
    "Give your answer and how sure you are, from 50 to 100. Answer with the JSON object only."
)
