"""
pytest সেটআপ: আসল chakri_ai.db না ছুঁয়ে প্রতিটা টেস্ট সেশনে আলাদা temp SQLite DB ব্যবহার করা হয়।
চালানোর নিয়ম (backend/ ফোল্ডার থেকে):
    pip install -r requirements-dev.txt
    python -m pytest tests -q
    TEST_DATABASE_URL=postgresql://... python -m pytest tests -q   # PostgreSQL-এ চালাতে (খালি টেস্ট DB দিন)
"""
import json
import os
import sys
import tempfile
from types import SimpleNamespace

import pytest

_tmpdir = tempfile.mkdtemp(prefix="chakri_test_")
# database.py import হওয়ার আগেই env সেট করতে হবে।
# TEST_DATABASE_URL দিলে (যেমন একটা খালি লোকাল PostgreSQL) সেখানে টেস্ট চলবে — সব টেবিল মুছে ফেলা হয়!
os.environ["DATABASE_URL"] = os.getenv("TEST_DATABASE_URL") or f"sqlite:///{os.path.join(_tmpdir, 'test.db')}"
os.environ.setdefault("ANTHROPIC_API_KEY", "test-key")
os.environ["RATE_LIMIT_ENABLED"] = "false"  # নির্দিষ্ট টেস্টে monkeypatch দিয়ে চালু করা হয়
for k in ("BKASH_APP_KEY", "BKASH_APP_SECRET", "BKASH_USERNAME", "BKASH_PASSWORD"):
    os.environ.pop(k, None)

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import database  # noqa: E402
import models  # noqa: E402
from main import app  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

# main.py-র load_dotenv() .env থেকে আসল bKash key বা mock ফ্ল্যাগ আনতে পারে — টেস্টে নিজেরা নিয়ন্ত্রণ করি
for k in ("BKASH_APP_KEY", "BKASH_APP_SECRET", "BKASH_USERNAME", "BKASH_PASSWORD", "PAYMENT_MOCK_ENABLED"):
    os.environ.pop(k, None)


@pytest.fixture(autouse=True)
def fresh_db():
    models.Base.metadata.drop_all(database.engine)
    models.Base.metadata.create_all(database.engine)
    yield


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def mock_mode(monkeypatch):
    monkeypatch.setenv("PAYMENT_MOCK_ENABLED", "true")


class FakeClaude:
    """ai_json._client()-এর বদলে বসানো হয় — নির্দিষ্ট JSON ফেরত দেয় ও কলগুলো মনে রাখে।"""

    def __init__(self, payload, stop_reason="end_turn"):
        self.payload = payload
        self.stop_reason = stop_reason
        self.calls = []
        self.messages = self

    def create(self, **kwargs):
        self.calls.append(kwargs)
        text = self.payload if isinstance(self.payload, str) else json.dumps(self.payload, ensure_ascii=False)
        return SimpleNamespace(stop_reason=self.stop_reason, content=[SimpleNamespace(type="text", text=text)])


@pytest.fixture
def fake(monkeypatch):
    """fake(payload) কল করলে Claude API-র বদলে FakeClaude বসে যায় (কোনো খরচ হয় না)।"""
    import ai_json

    def install(payload, stop_reason="end_turn"):
        client = FakeClaude(payload, stop_reason)
        monkeypatch.setattr(ai_json, "_client", lambda: client)
        return client
    return install
