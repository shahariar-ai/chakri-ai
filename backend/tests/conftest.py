"""
pytest সেটআপ: আসল chakri_ai.db না ছুঁয়ে প্রতিটা টেস্ট সেশনে আলাদা temp SQLite DB ব্যবহার করা হয়।
চালানোর নিয়ম (backend/ ফোল্ডার থেকে):
    pip install -r requirements-dev.txt
    python -m pytest tests -q
"""
import os
import sys
import tempfile

import pytest

_tmpdir = tempfile.mkdtemp(prefix="chakri_test_")
# database.py import হওয়ার আগেই env সেট করতে হবে
os.environ["DATABASE_URL"] = f"sqlite:///{os.path.join(_tmpdir, 'test.db')}"
os.environ.setdefault("ANTHROPIC_API_KEY", "test-key")
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
