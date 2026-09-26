"""Resume ও Cover Letter API টেস্ট — main.client (Claude) mock করা।"""
import pytest

import main
from conftest import FakeClaude

RESUME = {
    "full_name": "রাকিব হাসান", "email": "r@example.com", "phone": "01700000000",
    "target_position": "জুনিয়র অফিসার",
    "education": [{"institution": "জাতীয় বিশ্ববিদ্যালয়", "degree": "BBA", "field": "Finance", "passing_year": "2023"}],
    "skills": ["MS Excel", "Customer Service"],
}
COVER = {"resume_summary": "BBA", "job_description": "Officer", "company_name": "XYZ Bank", "target_position": "Officer"}
MD_TEXT = "# রাকিব হাসান\n\n---\n\n## SUMMARY\n\n**Subject:** আবেদন\n\n- MS Excel"


@pytest.fixture
def fake_main(monkeypatch):
    def install(text):
        client = FakeClaude(text)
        monkeypatch.setattr(main, "client", client)
        return client
    return install


def test_resume_generate_strips_markdown_and_builds_prompt(client, fake_main):
    ai = fake_main(MD_TEXT)
    r = client.post("/api/resume/generate", json={**RESUME, "language": "en"})
    assert r.status_code == 200
    d = r.json()
    assert d["resume_text"] == "রাকিব হাসান\n\nSUMMARY\n\nSubject: আবেদন\n\n- MS Excel"
    assert len(d["ats_score_tips"]) == 3
    prompt = ai.calls[0]["messages"][0]["content"]
    assert "BBA in Finance, জাতীয় বিশ্ববিদ্যালয় (2023)" in prompt
    assert "কোনো পূর্ব অভিজ্ঞতা নেই" in prompt  # experience খালি
    assert "professional English" in prompt and "Markdown ব্যবহার কোরো না" in prompt


def test_cover_letter_generate(client, fake_main):
    ai = fake_main("**Subject:** Application\n\nDear Sir,")
    d = client.post("/api/cover-letter/generate", json=COVER).json()
    assert d == {"cover_letter": "Subject: Application\n\nDear Sir,"}
    prompt = ai.calls[0]["messages"][0]["content"]
    assert "XYZ Bank" in prompt and "বাংলায় লিখো" in prompt


@pytest.mark.parametrize("path,body", [
    ("/api/resume/generate", {"full_name": "x"}),
    ("/api/resume/generate", {**RESUME, "education": "not-a-list"}),
    ("/api/cover-letter/generate", {"company_name": "x"}),
])
def test_validation_errors(client, fake_main, path, body):
    fake_main("x")
    assert client.post(path, json=body).status_code == 422


def test_missing_api_key_is_500(client, fake_main, monkeypatch):
    fake_main("x")
    monkeypatch.delenv("ANTHROPIC_API_KEY")
    assert client.post("/api/resume/generate", json=RESUME).status_code == 500
    assert client.post("/api/cover-letter/generate", json=COVER).status_code == 500


def test_ai_failure_is_502(client, monkeypatch):
    class Boom:
        class messages:
            @staticmethod
            def create(**_):
                raise RuntimeError("network down")
    monkeypatch.setattr(main, "client", Boom)
    assert client.post("/api/resume/generate", json=RESUME).status_code == 502
    assert client.post("/api/cover-letter/generate", json=COVER).status_code == 502


@pytest.mark.parametrize("text,expected", [
    ("### হেডিং\nলেখা", "হেডিং\nলেখা"),
    ("__bold__ ও **আরো**", "bold ও আরো"),
    ("২*৩ = ৬, *italic* থাকবে", "২*৩ = ৬, *italic* থাকবে"),
    ("ক\n\n***\n\n\n\nখ", "ক\n\nখ"),
])
def test_strip_markdown(text, expected):
    assert main.strip_markdown(text) == expected
