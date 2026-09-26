"""Admin bulk import (প্রশ্ন ও স্টাডি ম্যাটেরিয়াল) টেস্ট।"""
import json

import pytest

import database
import models

KEY = "test-admin-key"
HEADER = "subject_name,exam_name,exam_year,question_text,option_a,option_b,option_c,option_d,correct_answer\n"


@pytest.fixture(autouse=True)
def admin_key(monkeypatch):
    monkeypatch.setenv("ADMIN_API_KEY", KEY)


def _import(client, content: str, name="q.csv", dry_run=False, key=KEY, path="questions"):
    return client.post(
        f"/api/admin/{path}/import",
        params={"dry_run": str(dry_run).lower()},
        headers={"X-Admin-Key": key} if key else {},
        files={"file": (name, content.encode("utf-8"), "text/csv" if name.endswith(".csv") else "application/json")},
    )


def _questions():
    with database.SessionLocal() as db:
        return [(q.subject.name, q.question_text, q.correct_answer) for q in db.query(models.ExamQuestion).all()]


def _subjects():
    with database.SessionLocal() as db:
        return sorted(s.name for s in db.query(models.Subject).all())


def test_requires_admin_key(client):
    assert _import(client, HEADER, key=None).status_code == 401
    assert _import(client, HEADER, key="wrong").status_code == 401


def test_csv_import_dry_run_then_real_then_duplicate(client):
    csv = HEADER + "সাধারণ গণিত,৪৫তম BCS,2023,২+২=?,৩,৪,৫,৬,B\n"
    r = _import(client, csv, dry_run=True).json()
    assert r["would_insert"] == 1 and r["inserted"] == 0 and _questions() == []

    assert _import(client, csv).json()["inserted"] == 1
    r = _import(client, csv).json()
    assert r["inserted"] == 0 and r["skipped_duplicates"] == 1
    assert _questions() == [("সাধারণ গণিত", "২+২=?", "B")]


@pytest.mark.parametrize("answer,expected", [("B", "B"), ("b", "B"), (" খ ", "B"), ("৪", "B"), ("D", "D")])
def test_correct_answer_normalized_to_letter(client, answer, expected):
    r = _import(client, HEADER + f"সাধারণ গণিত,,,২+২=?,৩,৪,৫,৬,{answer}\n").json()
    assert r["inserted"] == 1, r
    assert _questions()[0][2] == expected


@pytest.mark.parametrize("row,reason_part", [
    ("সাধারণ গণিত,,,প্রশ্ন,শুধু এক,,,,A", "অন্তত দুটো অপশন"),
    ("সাধারণ গণিত,,,প্রশ্ন,ক,খ,গ,ঘ,", "correct_answer দিতে হবে"),
    ("সাধারণ গণিত,,,প্রশ্ন,ক,খ,,,C", "মেলে না"),          # C অপশন নেই
    ("সাধারণ গণিত,,,প্রশ্ন,ক,খ,গ,ঘ,অন্য কিছু", "মেলে না"),
])
def test_invalid_rows_reported_not_inserted(client, row, reason_part):
    r = _import(client, HEADER + row + "\n").json()
    assert r["inserted"] == 0 and len(r["errors"]) == 1
    assert reason_part in r["errors"][0]["reason"]
    assert r["errors"][0]["row"] == 2  # CSV হেডারের পরের লাইন


def test_old_short_subject_names_go_to_canonical_subject(client):
    csv = HEADER + "বাংলা,,,প্রশ্ন ১,ক,খ,গ,ঘ,A\n  গণিত ,,,প্রশ্ন ২,ক,খ,গ,ঘ,A\n"
    assert _import(client, csv).json()["inserted"] == 2
    assert _subjects() == ["বাংলা ব্যাকরণ ও সাহিত্য", "সাধারণ গণিত"]


def test_json_import(client):
    data = [{"subject_name": "সাধারণ জ্ঞান", "question_text": "রাজধানী?", "option_a": "ঢাকা",
             "option_b": "খুলনা", "correct_answer": "ঢাকা", "exam_year": 2024}]
    r = _import(client, json.dumps(data, ensure_ascii=False), name="q.json").json()
    assert r["inserted"] == 1, r
    assert _questions() == [("সাধারণ জ্ঞান (বাংলাদেশ বিষয়াবলি)", "রাজধানী?", "A")]


def test_study_material_import_uses_alias(client):
    csv = "subject_name,title,content,topic_tags\nগণিত,লসাগু,লসাগু হলো...,\"গণিত,সংখ্যা\"\n"
    r = _import(client, csv, path="study-materials").json()
    assert r["inserted"] == 1, r
    with database.SessionLocal() as db:
        m = db.query(models.StudyMaterial).one()
        assert m.subject.name == "সাধারণ গণিত" and m.topic_tags == "গণিত,সংখ্যা"


def test_template_uses_letter_answer(client):
    r = client.get("/api/admin/questions/import/template", headers={"X-Admin-Key": KEY})
    assert r.status_code == 200
    # টেমপ্লেটটাই যেন নিজে ইমপোর্ট করা যায় (অক্ষর-উত্তর সহ)
    assert _import(client, r.text).json()["inserted"] == 1
    assert _questions()[0][2] == "A"
