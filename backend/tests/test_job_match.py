"""Job Matching / Skill Gap API টেস্ট — Claude API mock করা (conftest-এর fake fixture)।"""
from datetime import datetime, timedelta

import pytest

import database
import models

ANALYSIS = {
    "match_score": 72, "eligibility": "eligible", "info_sufficient": True, "verdict": "ভালো মিল",
    "matched_skills": ["MS Excel"],
    "missing_skills": [{"skill": "AML/CFT", "importance": "high", "how_to_learn": "BIBM কোর্স"}],
    "strengths": ["Finance ব্যাকগ্রাউন্ড"], "action_plan": ["AML পড়ুন"],
}
PROFILE = {"skills": ["MS Excel", "Accounting"], "education": "BBA", "age": 26}


def _add_circulars(*specs):
    """specs: (title, qualification, is_active, deadline_offset_days|None)"""
    with database.SessionLocal() as db:
        org = models.Organization(name="Test Org", name_bn="টেস্ট প্রতিষ্ঠান")
        db.add(org)
        db.flush()
        ids = []
        for title, qual, active, offset in specs:
            c = models.JobCircular(
                title=title, qualification=qual, is_active=active, organization_id=org.id, category="Bank Job",
                application_deadline=(datetime.utcnow() + timedelta(days=offset)) if offset is not None else None,
            )
            db.add(c)
            db.flush()
            ids.append(c.id)
        db.commit()
        return ids


# ---------- /analyze ----------

def test_analyze_with_job_description(client, fake):
    ai = fake(ANALYSIS)
    r = client.post("/api/job-match/analyze", json={**PROFILE, "job_description": "Junior Officer, AML জ্ঞান"})
    assert r.status_code == 200
    d = r.json()
    assert d["match_score"] == 72 and d["circular_id"] is None and d["missing_skills"][0]["importance"] == "high"
    prompt = ai.calls[0]["messages"][0]["content"]
    assert "MS Excel, Accounting" in prompt and "Junior Officer" in prompt


def test_analyze_with_circular_uses_db_fields(client, fake):
    (cid,) = _add_circulars(("সিনিয়র অফিসার নিয়োগ", "স্নাতক, CGPA 3.0", True, 10))
    ai = fake({**ANALYSIS, "match_score": 130})
    d = client.post("/api/job-match/analyze", json={**PROFILE, "circular_id": cid}).json()
    assert d["circular_id"] == cid and d["job_title"] == "সিনিয়র অফিসার নিয়োগ"
    assert d["match_score"] == 100  # clamp
    prompt = ai.calls[0]["messages"][0]["content"]
    assert "স্নাতক, CGPA 3.0" in prompt and "টেস্ট প্রতিষ্ঠান" in prompt


@pytest.mark.parametrize("body,code", [
    ({"skills": [], "job_description": "x"}, 422),
    ({"skills": ["  "], "job_description": "x"}, 422),
    ({"skills": ["Excel"]}, 422),                                  # চাকরির তথ্য নেই
    ({"skills": ["Excel"], "job_description": "   "}, 422),
    ({"skills": ["Excel"], "circular_id": 9999}, 404),
    ({"skills": ["Excel"], "job_description": "x", "age": 5}, 422),
])
def test_analyze_validation(client, fake, body, code):
    fake(ANALYSIS)
    assert client.post("/api/job-match/analyze", json=body).status_code == code


def test_analyze_ai_failure_is_502(client, fake):
    fake("oops")
    assert client.post("/api/job-match/analyze", json={**PROFILE, "job_description": "x"}).status_code == 502


# ---------- /recommend ----------

def test_recommend_filters_pool_and_sanitizes_ai_output(client, fake):
    open_a, open_b, expired, inactive, no_deadline = _add_circulars(
        ("A অফিসার", None, True, 5),
        ("B ক্যাশিয়ার", None, True, 20),
        ("মেয়াদোত্তীর্ণ", None, True, -1),
        ("বন্ধ", None, False, 5),
        ("ডেডলাইন নেই", None, True, None),
    )
    ai = fake({"matches": [
        {"circular_id": open_a, "match_score": 60, "reason": "ঠিক আছে"},
        {"circular_id": expired, "match_score": 99, "reason": "তালিকায় ছিল না"},  # AI ভুল করে দিলে বাদ
        {"circular_id": no_deadline, "match_score": 85, "reason": "সেরা"},
        {"circular_id": open_a, "match_score": 10, "reason": "ডুপ্লিকেট"},
        {"circular_id": 12345, "match_score": 90, "reason": "অজানা"},
    ]})
    d = client.post("/api/job-match/recommend", json={**PROFILE, "limit": 5}).json()

    assert d["considered"] == 3  # open_a, open_b, no_deadline
    assert [(j["circular_id"], j["match_score"]) for j in d["jobs"]] == [(no_deadline, 85), (open_a, 60)]
    assert d["jobs"][0]["organization"] == "টেস্ট প্রতিষ্ঠান"
    prompt = ai.calls[0]["messages"][0]["content"]
    assert f"circular_id={open_b}" in prompt and f"circular_id={expired}" not in prompt
    assert f"circular_id={inactive}" not in prompt


def test_recommend_respects_limit(client, fake):
    ids = _add_circulars(*[(f"পদ {i}", None, True, 5) for i in range(4)])
    fake({"matches": [{"circular_id": i, "match_score": 50 + n, "reason": "r"} for n, i in enumerate(ids)]})
    d = client.post("/api/job-match/recommend", json={**PROFILE, "limit": 2}).json()
    assert [j["match_score"] for j in d["jobs"]] == [53, 52]


def test_recommend_no_circulars_skips_ai(client, fake):
    ai = fake({"matches": []})
    d = client.post("/api/job-match/recommend", json=PROFILE).json()
    assert d == {"considered": 0, "jobs": []}
    assert ai.calls == []
