"""Quiz generation labeling tests."""
from app.services.quiz_bank import _maybe_generate, _counts


def test_generated_questions_are_ai_generated_not_pyq():
    items = _maybe_generate("Euler's theorem: x fx + y fy = n f for homogeneous f.", 2, "euler-theorem-dc", "em1-btech")
    for it in items:
        assert it["source"] == "AI_GENERATED"
        assert it["source"] != "PYQ"
        assert it.get("year") is None


def test_source_counts():
    c = _counts([{"source": "PYQ"}, {"source": "DEMO"}, {"source": "AI_GENERATED"}])
    assert c["PYQ"] == 1
    assert c["DEMO"] == 1
    assert c["AI_GENERATED"] == 1
