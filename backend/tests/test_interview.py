"""Mock Interview API টেস্ট — Claude API কল mock করা, তাই কোনো খরচ হয় না।"""
import pytest


BASE = {"target_position": "অফিসার", "interview_type": "bank", "total_questions": 3}
FEEDBACK = {"score": 7, "strengths": ["a"], "improvements": ["b"], "sample_answer": "c"}


def _turns(n):
    return [{"question": f"q{i}", "answer": f"a{i}"} for i in range(n)]


def test_first_question(client, fake):
    c = fake({"next_question": "নিজের সম্পর্কে বলুন"})
    r = client.post("/api/interview/turn", json={**BASE, "history": []}).json()
    assert r == {"question_number": 1, "feedback": None, "next_question": "নিজের সম্পর্কে বলুন",
                 "finished": False, "summary": None}
    schema = c.calls[0]["extra_body"]["output_config"]["format"]["schema"]
    assert schema["required"] == ["next_question"]


def test_middle_turn_has_feedback_and_next(client, fake):
    c = fake({"feedback": FEEDBACK, "next_question": "q2"})
    r = client.post("/api/interview/turn", json={**BASE, "history": _turns(1)}).json()
    assert r["question_number"] == 2 and r["feedback"]["score"] == 7 and not r["finished"]
    assert c.calls[0]["extra_body"]["output_config"]["format"]["schema"]["required"] == ["feedback", "next_question"]
    assert "ব্যাংক" in c.calls[0]["messages"][0]["content"]


def test_last_turn_returns_summary_and_clamps_scores(client, fake):
    fake({"feedback": {**FEEDBACK, "score": 15},
          "summary": {"overall_score": 140, "verdict": "ভালো", "strengths": [], "improvements": []}})
    r = client.post("/api/interview/turn", json={**BASE, "history": _turns(3)}).json()
    assert r["finished"] is True and r["next_question"] is None
    assert r["feedback"]["score"] == 10 and r["summary"]["overall_score"] == 100


@pytest.mark.parametrize("body,code", [
    ({**BASE, "history": _turns(4)}, 400),                                     # total-এর বেশি
    ({**BASE, "history": [{"question": "q", "answer": "  "}]}, 400),           # খালি উত্তর
    ({**BASE, "total_questions": 20, "history": []}, 422),                     # সীমার বাইরে
    ({**BASE, "interview_type": "army", "history": []}, 422),                  # অজানা ধরন
])
def test_validation(client, fake, body, code):
    fake({"next_question": "x"})
    assert client.post("/api/interview/turn", json=body).status_code == code


def test_truncated_or_invalid_ai_output_is_502(client, fake):
    fake({"next_question": "x"}, stop_reason="max_tokens")
    assert client.post("/api/interview/turn", json={**BASE, "history": []}).status_code == 502
    fake("not json")
    assert client.post("/api/interview/turn", json={**BASE, "history": []}).status_code == 502
