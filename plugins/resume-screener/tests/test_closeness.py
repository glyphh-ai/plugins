"""The closeness check's own code (screener/closeness.py, check.py), with Ada's answers written by hand in the
shape Ada really gives them (a fact tree per nearest application: key, weight, score, children). What is tested
is what is read, what is asked and how the answer is put together, not Ada."""

import base64
import io
import json
import sys
import types
from pathlib import Path
from typing import Any

from screener import closeness

FIXTURES: Path = Path(__file__).resolve().parent / "fixtures"
RESUME: str = """Ann Lee
Austin, TX | ann.lee@mail.example | (512) 555-0100 | www.annlee.example

SUMMARY
Data analyst with 6 years of experience. Built dashboards — fast!

EXPERIENCE
Senior Data Analyst, Acme Corp 2021 - Present
- Built 14 dashboards in Looker for the finance team
- Wrote SQL for weekly reports at Company Name, City, State

EDUCATION
B.S. Statistics, State University 2018

SKILLS
SQL, Excel, Looker, dbt
"""


def fact(side: str, label: str, mid: str, part: str, score: float) -> dict[str, Any]:
    """One of Ada's nearest applications as ada_facts answers it, cut to what is read."""
    who = {"key": f"{part}_who", "weight": 0.0, "score": 0.0, "record": json.dumps([side, label, mid])}
    layer = {"key": part, "weight": 0.3, "score": score, "children": [{"key": "s", "score": score, "children": [who]}]}
    side_layer = {"key": "side", "weight": 1.0, "score": 1.0, "children": []}
    return {"id": mid, "outcome": side, "score": (0.3 * score + 1) / 1.3, "tree": {"key": "", "children": [layer, side_layer]}}


def test_a_resume_is_read_into_its_sections_as_neutral_words() -> None:
    found = closeness.parts(RESUME, "Dear team,\nI'd love to join. Call (512) 555-0100.\nSincerely, Ann")
    assert found["summary"] == "data analyst with years of experience built dashboards fast"
    assert found["duties"] == "built dashboards in looker for the finance team wrote sql for weekly reports at"
    assert found["titles"] == "senior data analyst" and found["skills"] == "dbt excel looker sql"
    assert found["school"] == "b.s statistics university" and found["letter"] == "dear team i'd love to join call sincerely ann"
    assert closeness.neutral("C++ and C#, .NET; a@b.example https://x.example 2019-2021", 3) == "c++ and c#"
    assert len(closeness.neutral("word " * 500, closeness.KEPT["duties"]).split()) == 200
    flat = "Jane Roe     Summary    Careful nurse.     Experience    Staff Nurse    Charted for 30 patients.    Skills    triage, charting"
    assert closeness.parts(flat)["duties"] == "staff nurse charted for patients"  # a site's flattened lines, given back


def test_the_case_holds_only_words_a_label_and_a_side_and_a_resume_without_experience_is_not_compared() -> None:
    held = closeness.case(closeness.parts(RESUME), "x1", "real", "your own applicants", "your own applicants")
    assert held["side"] == {"s": {"is": "real"}} and held["who"]["s"]["id"] == "x1"
    assert json.loads(held["resume"]["s"]["resume_who"]) == ["real", "your own applicants", "x1"]
    assert "ann" not in json.dumps(held) and "555" not in json.dumps(held) and "letter" not in held
    asked = closeness.case(closeness.parts(RESUME, "Dear team, hello."), "asked")
    assert "side" not in asked and [a["key"] for a in closeness.asks(asked)] == [
        "resume:fake", "resume:real", "letter:fake", "letter:real"]  # fmt: skip
    assert closeness.asks(asked)[1]["data"]["side"] == {"s": {"is": "real"}} and closeness.asks(asked)[0]["top"] == 4
    bare = closeness.case(closeness.parts("Ann Lee\nSKILLS\nsql, excel"), "asked")
    assert "resume" not in bare and closeness.asks(bare) == []
    assert closeness.result(bare, {}) == {"reads": "there was nothing to read"}


def test_the_answer_is_the_nearest_on_each_side_by_the_parts_own_score() -> None:
    asked = closeness.case(closeness.parts(RESUME, "Dear team, hello."), "asked")
    facts = {
        "resume:fake": [fact("fake", "Keisha Dubois - backend engineer", "a1", "resume", 0.911), fact("fake", "B", "a2", "resume", 0.4),
                        fact("fake", "C", "a3", "resume", 0.3), fact("fake", "D", "a4", "resume", 0.2)],
        "resume:real": {"facts": [fact("real", "livecareer - FINANCE", "r1", "resume", 0.62),
                                  fact("fake", "not this side", "a9", "resume", 0.99)]},  # a connector's wrapped answer
        "letter:fake": [fact("fake", "Keisha Dubois - backend engineer", "a1", "letter", 0.3)],
        "letter:real": [fact("fake", "only fakes came back", "a1", "letter", 0.3)],
    }  # fmt: skip
    got = closeness.result(asked, facts)
    assert got["resume"]["fake"] == {"closeness": 0.91, "nearest": [
        {"closeness": 0.91, "like": "Keisha Dubois - backend engineer"}, {"closeness": 0.4, "like": "B"},
        {"closeness": 0.3, "like": "C"}]}  # fmt: skip
    assert got["resume"]["real"] == {"closeness": 0.62, "nearest": [{"closeness": 0.62, "like": "livecareer - FINANCE"}]}
    assert got["resume"]["reads"] == "reads like the fakes"
    assert got["letter"]["real"]["closeness"] is None and got["letter"]["reads"] == "only fakes are held to compare it with"
    near = closeness.result(asked, {"resume:fake": [fact("fake", "A", "a", "resume", 0.5)],
                                    "resume:real": [fact("real", "R", "r", "resume", 0.51)]})["resume"]  # fmt: skip
    assert near["reads"] == "between the two"
    real = closeness.result(asked, {"resume:fake": [fact("fake", "A", "a", "resume", 0.2)],
                                    "resume:real": [fact("real", "R", "r", "resume", 0.6)]})["resume"]  # fmt: skip
    assert real["reads"] == "reads like real people"
    mine = closeness.result(asked, {"resume:fake": [fact("fake", "me", "asked", "resume", 1.0)]})["resume"]
    assert mine["fake"]["closeness"] is None and mine["reads"] == "nothing is held to compare it with"


def test_adas_decision_is_passed_on_with_its_confidence_and_its_fact_tree_untouched() -> None:
    tree = [{"id": "p1", "outcome": "fake", "score": 0.4, "tree": {"key": "", "children": []}}]
    got = closeness.decision({"outcome": "fake", "probabilities": {"fake": 0.7879, "real": 0.2121}, "ask": False, "facts": tree})
    assert (got["outcome"], got["confidence"], got["ask"]) == ("fake", 0.79, False) and got["facts"] is tree
    assert closeness.decision({})["confidence"] is None


def test_one_request_on_standard_input_is_checked_without_touching_the_disk(monkeypatch: Any, capsys: Any) -> None:
    import check

    asked: list[tuple[str, str]] = []

    class Model:
        def __init__(self, name: str) -> None:
            self.name = name

        def facts(self, data: Any, top: int = 0) -> Any:
            side = data["side"]["s"]["is"]
            asked.append((self.name, f"facts {next(k for k in data if k != 'side')} {side}"))
            return types.SimpleNamespace(data=[fact(side, f"a {side} one", "p1", "resume", 0.4 if side == "fake" else 0.1)])

        def decide(self, data: Any, include: Any = None) -> Any:
            asked.append((self.name, f"decide {list(data)} {include}"))
            return types.SimpleNamespace(outcome="fake", probabilities={"fake": 0.8, "real": 0.2}, ask=False, facts=[{"tree": {}}])

    fake = types.ModuleType("glyphh")
    fake.Ada = lambda: types.SimpleNamespace(model=Model)  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "glyphh", fake)
    resume = base64.b64encode((FIXTURES / "strong-backend-resume.docx").read_bytes()).decode()
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps({"resume": {"name": "cv.docx", "base64": resume}})))
    monkeypatch.setattr(sys, "argv", ["check.py", "--stdin", "--prefix", "demo-screener-"])
    monkeypatch.setattr("pathlib.Path.write_text", lambda *a, **k: (_ for _ in ()).throw(AssertionError("wrote a file")))
    check.main()
    said = json.loads(capsys.readouterr().out)
    assert said["resume"]["reads"] == "reads like the fakes" and said["resume"]["fake"]["closeness"] == 0.4
    assert said["decision"] == {"outcome": "fake", "confidence": 0.8, "ask": False, "on": "resume",
                                "probabilities": {"fake": 0.8, "real": 0.2}, "facts": [{"tree": {}}]}  # fmt: skip
    assert asked == [("demo-screener-closeness", "facts resume fake"), ("demo-screener-closeness", "facts resume real"),
                     ("demo-screener-closeness", "decide ['resume'] ['facts']")]  # fmt: skip
    assert "letter" not in said


def test_files_are_told_apart_and_what_cannot_be_read_is_said() -> None:
    import check

    letter = b"Dear team,\nI would like to apply.\nSincerely, Ann"
    resume, said, problems = check.texts([("a.txt", letter), ("b.txt", RESUME.encode()), ("c.xyz", b"??")])
    assert resume.startswith("Ann Lee") and said.startswith("Dear team") and problems == ["c.xyz: not PDF, DOCX or text"]
    assert check.texts([], None, ("l.txt", letter))[:2] == ("", letter.decode())
    assert check.texts([], ("bad.pdf", b"%PDF-1.4 nothing"))[2][0].startswith("bad.pdf: the pdf file could not be read")


def test_your_own_real_resumes_are_read_from_a_folder_named_by_no_one(tmp_path: Path) -> None:
    import seed

    (tmp_path / "Ann Lee resume.txt").write_text(RESUME)
    (tmp_path / "Ann Lee cover letter.txt").write_text("Dear team, sincerely")
    (tmp_path / "notes.xyz").write_text("not a resume")
    (tmp_path / "thin.txt").write_text("Bo Li\nSKILLS\nsql")
    (got,) = seed.real(tmp_path)
    assert got["outcome"] == "real" and got["data"]["side"] == {"s": {"is": "real"}}
    assert got["data"]["who"]["s"]["id"].startswith("real-") and "ann" not in json.dumps(got).lower().replace("analyst", "")
