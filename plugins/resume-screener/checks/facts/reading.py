"""The agent's reading of an application: one fixed prompt and one fixed schema, the same for every application.
The agent is asked what it observes, never whether the person is real. Version 1 of the schema, written before any
data was read; what is kept of it is decided on the seen sets only (docs/check-5-protocol.md)."""

from typing import Any

SCALE: dict[str, Any] = {"type": "integer", "enum": [0, 1, 2, 3]}


def kind(*values: str) -> dict[str, Any]:
    return {"type": "string", "enum": list(values)}


# Each fact: (name, schema, what the agent is told it means).
FACTS: list[tuple[str, dict[str, Any], str]] = [
    # The timeline: does the career hang together as a life does?
    ("jobs", {"type": "integer"}, "How many separate jobs or roles are listed (0 if none)."),
    ("dates", kind("none", "years", "months"), "How exactly jobs are dated: not at all, by year, or by month."),
    ("overlaps", kind("none", "some", "unclear"), "Do any jobs overlap in time?"),
    ("gaps", kind("none", "some", "unclear"), "Are there gaps of a year or more between jobs?"),
    ("tenures", kind("even", "uneven", "unclear"), "Are the lengths of the jobs all much alike, or uneven (some short, some long)?"),
    ("short_stints", kind("none", "some", "unclear"), "Is any job shorter than a year?"),
    ("path", kind("steady_climb", "sideways_or_mixed", "change_of_field", "unclear"),
     "The shape of the career: each job a step up in one field; sideways moves or a mix; or a change of field."),
    # Unevenness: the loose ends a real life has.
    ("unrelated_work", SCALE, "How much of the history has nothing to do with the main line of work (0 none, 3 a lot)."),
    ("loose_ends", SCALE, "Things that do not serve the application: odd jobs, unfinished study, hobbies, asides, leftovers (0 none, 3 many)."),
    ("education_path", kind("none_given", "straight", "winding"), "Education: not given; one straight line; or winding (changes, pauses, late or unfinished study)."),
    # Specifics: can the claims be checked, and are the numbers odd or round?
    ("named_things", SCALE, "How many specific, checkable things are named: particular products, systems, clients, places, projects, courses (0 none, 3 many). Do not count employers' names or placeholders for them."),
    ("numbers", SCALE, "How many figures are given for results or scale (0 none, 3 many)."),
    ("round_numbers", kind("no_numbers", "mostly_round", "mixed", "mostly_odd"), "Are the figures round (20%, 50, 1 million) or odd (17.4%, 43, 1,280)?"),
    ("one_off_details", SCALE, "Details only this person would have: something particular that happened, a named local thing, an unusual task (0 none, 3 many)."),
    # The writing: generic or lived?
    ("stock_phrases", SCALE, "How much of the text is general competence language that could be said of anyone in the trade (0 little, 3 nearly all)."),
    ("evenness_of_writing", SCALE, "How even the writing is from part to part: 0 very uneven (parts read as written at different times or with different care), 3 uniformly smooth."),
    ("slips", SCALE, "Typing, spelling, grammar or formatting slips left in (0 none, 3 many)."),
    ("every_line_sells", SCALE, "How much every line pushes one message for one kind of job (0 it just lists what happened, 3 every line is tuned to sell)."),
    # The whole: does it fit together too well, or not at all?
    ("fits_one_role", SCALE, "How neatly everything (titles, duties, skills, education) lines up behind a single target role (0 not at all, 3 perfectly)."),
    ("duties_match_titles", kind("yes", "partly", "no", "unclear"), "Do the duties described match the seniority and kind of each job title?"),
    ("contradictions", kind("none", "some"), "Does anything contradict anything else (dates, ages, places, claims)?"),
    ("skills_shown", kind("no_skills_listed", "shown_in_work", "partly", "only_listed"), "Are the skills listed actually seen being used in the work described?"),
    ("letter", kind("no_letter", "same_person", "partly", "different"), "If there is a cover letter: do its facts match the resume's?"),
]  # fmt: skip

SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {name: schema for name, schema, _ in FACTS},
    "required": [name for name, _, _ in FACTS],
    "additionalProperties": False,
}

SYSTEM: str = (
    "You read job applications carefully and report what you observe in them, as a careful recruiter with time to "
    "spare would. You are not asked to judge the applicant, and you are not asked whether the application is "
    "genuine: only to observe. Layout, section order, headings and stand-in words such as 'Company Name' or "
    "'City, State' tell you nothing and must not move any answer. Answer every item from the text alone. When the "
    "text does not let you tell, use the 'unclear' or lowest value. Answer with the JSON object only.\n\n"
    "The items:\n" + "\n".join(f"- {name}: {said}" for name, _, said in FACTS)
)


def user(text: str) -> str:
    return f"The application:\n\n<application>\n{text}\n</application>"


# The agent alone (a baseline): asked directly, with no Ada.
ALONE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {"answer": kind("real", "fake"), "confidence": {"type": "integer"}},
    "required": ["answer", "confidence"],
    "additionalProperties": False,
}
ALONE_SYSTEM: str = (
    "You are shown one job application. Decide whether it describes a real person who wrote it about themselves "
    "(`real`; it may have been polished with AI) or an invented person who does not exist (`fake`). Layout and "
    "stand-in words such as 'Company Name' tell you nothing. Give your answer and how sure you are, from 50 to 100. "
    "Answer with the JSON object only."
)
