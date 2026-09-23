"""পেমেন্ট/সাবস্ক্রিপশন API টেস্ট — mock মোড ও bKash callback (bKash HTTP mock করা)।"""
import re

import pytest

from payments import bkash

SUB = "sub-test-12345678"


def _create(client, provider="bkash", plan="monthly", sub=SUB):
    return client.post("/api/payments/create", json={"subscriber_id": sub, "plan_code": plan, "provider": provider})


def _status(client, sub=SUB):
    return client.get(f"/api/payments/status/{sub}").json()


def _payment(client, pid, sub=SUB):
    return client.get(f"/api/payments/{pid}", params={"subscriber_id": sub}).json()


def _pay(client, pid, outcome="success", wallet="01712345678", pin="12345"):
    return client.post(f"/api/payments/mock/complete/{pid}",
                       data={"outcome": outcome, "wallet": wallet, "pin": pin}, follow_redirects=False)


# ---------- প্ল্যান ও প্রোভাইডার মোড ----------

def test_providers_disabled_without_mock_or_credentials(client):
    providers = {p["code"]: p["mode"] for p in client.get("/api/payments/plans").json()["providers"]}
    assert providers == {"bkash": None, "nagad": None}
    r = _create(client, "nagad")
    assert r.status_code == 503


def test_providers_mock_mode(client, mock_mode):
    data = client.get("/api/payments/plans").json()
    assert {p["code"]: p["mode"] for p in data["providers"]} == {"bkash": "mock", "nagad": "mock"}
    assert [p["code"] for p in data["plans"]] == ["monthly", "quarterly", "yearly"]


def test_bkash_live_when_configured_even_if_mock_on(client, mock_mode, monkeypatch):
    for k in ("BKASH_APP_KEY", "BKASH_APP_SECRET", "BKASH_USERNAME", "BKASH_PASSWORD"):
        monkeypatch.setenv(k, "x")
    modes = {p["code"]: p["mode"] for p in client.get("/api/payments/plans").json()["providers"]}
    assert modes == {"bkash": "live", "nagad": "mock"}


def test_invalid_plan_and_provider(client, mock_mode):
    assert _create(client, plan="gold").status_code == 400
    assert _create(client, provider="mock").status_code == 422  # পুরনো "mock" প্রোভাইডার আর নেই


# ---------- mock চেকআউট ফ্লো ----------

@pytest.mark.parametrize("provider", ["bkash", "nagad"])
def test_mock_success_makes_premium(client, mock_mode, provider):
    created = _create(client, provider).json()
    assert created["redirect_url"].endswith(f"/api/payments/mock/checkout/{created['payment_id']}")

    page = client.get(f"/api/payments/mock/checkout/{created['payment_id']}").text
    assert "টেস্ট মোড" in page and ("bKash" if provider == "bkash" else "Nagad") in page

    assert _status(client)["is_premium"] is False
    r = _pay(client, created["payment_id"])
    assert "পেমেন্ট সফল হয়েছে" in r.text

    p = _payment(client, created["payment_id"])
    assert p["status"] == "completed" and p["is_test"] is True and p["trx_id"].startswith("TEST")
    s = _status(client)
    assert s["is_premium"] is True and s["plan_code"] == "monthly"


@pytest.mark.parametrize("outcome,expected", [("cancel", "cancelled"), ("failure", "failed")])
def test_mock_cancel_and_failure(client, mock_mode, outcome, expected):
    pid = _create(client).json()["payment_id"]
    _pay(client, pid, outcome=outcome)
    assert _payment(client, pid)["status"] == expected
    assert _status(client)["is_premium"] is False
    # শেষ হয়ে যাওয়া পেমেন্ট পরে আর সফল করা যায় না
    _pay(client, pid)
    assert _payment(client, pid)["status"] == expected


@pytest.mark.parametrize("wallet,pin", [("12345", "12345"), ("01212345678", "12345"), ("01712345678", "12")])
def test_mock_invalid_input_redirects_back(client, mock_mode, wallet, pin):
    pid = _create(client).json()["payment_id"]
    r = _pay(client, pid, wallet=wallet, pin=pin)
    assert r.status_code == 303 and f"/mock/checkout/{pid}?error=" in r.headers["location"]
    assert _payment(client, pid)["status"] == "pending"
    # error মেসেজ সহ ফর্ম আবার দেখায়
    assert 'class="err"' in client.get(r.headers["location"]).text


def test_mock_endpoints_hidden_when_mock_disabled(client, mock_mode, monkeypatch):
    pid = _create(client).json()["payment_id"]
    monkeypatch.setenv("PAYMENT_MOCK_ENABLED", "false")
    assert client.get(f"/api/payments/mock/checkout/{pid}").status_code == 404
    assert _pay(client, pid).status_code == 404


def test_subscription_stacks_expiry(client, mock_mode):
    for plan in ("monthly", "quarterly"):
        _pay(client, _create(client, plan=plan).json()["payment_id"])
    s = _status(client)
    assert s["plan_code"] == "quarterly"
    from datetime import datetime
    days = (datetime.fromisoformat(s["expires_at"]) - datetime.utcnow()).days
    assert 118 <= days <= 120  # ৩০ + ৯০ দিন


def test_other_subscriber_cannot_see_payment(client, mock_mode):
    pid = _create(client).json()["payment_id"]
    r = client.get(f"/api/payments/{pid}", params={"subscriber_id": "someone-else-1"})
    assert r.status_code == 404


# ---------- bKash live callback (HTTP mock করা) ----------

@pytest.fixture
def bkash_live(monkeypatch):
    for k in ("BKASH_APP_KEY", "BKASH_APP_SECRET", "BKASH_USERNAME", "BKASH_PASSWORD"):
        monkeypatch.setenv(k, "x")
    state = {"execute": {}}
    monkeypatch.setattr(bkash, "create_payment", lambda **kw: {
        "paymentID": f"PAY-{kw['invoice_number']}", "bkashURL": "https://sandbox.example/pay", "statusCode": "0000"})
    monkeypatch.setattr(bkash, "execute_payment", lambda pid: state["execute"][pid])
    return state


def _bkash_pid(client, pid):
    # create_payment mock থেকে paymentID বের করা
    from database import SessionLocal
    import models
    with SessionLocal() as db:
        return db.get(models.Payment, pid).provider_payment_id


def test_bkash_callback_success_and_idempotent(client, bkash_live):
    created = _create(client).json()
    assert created["redirect_url"] == "https://sandbox.example/pay"
    bpid = _bkash_pid(client, created["payment_id"])
    bkash_live["execute"][bpid] = {"transactionStatus": "Completed", "trxID": "TRX1", "amount": "99.00"}

    r = client.get("/api/payments/bkash/callback", params={"paymentID": bpid, "status": "success"})
    assert "পেমেন্ট সফল হয়েছে" in r.text
    p = _payment(client, created["payment_id"])
    assert p["status"] == "completed" and p["trx_id"] == "TRX1" and p["is_test"] is False

    again = client.get("/api/payments/bkash/callback", params={"paymentID": bpid, "status": "success"})
    assert "আগেই" in again.text


def test_bkash_callback_amount_mismatch_fails(client, bkash_live):
    pid = _create(client).json()["payment_id"]
    bpid = _bkash_pid(client, pid)
    bkash_live["execute"][bpid] = {"transactionStatus": "Completed", "trxID": "TRX2", "amount": "1.00"}
    client.get("/api/payments/bkash/callback", params={"paymentID": bpid, "status": "success"})
    assert _payment(client, pid)["status"] == "failed"
    assert _status(client)["is_premium"] is False


def test_bkash_callback_cancel(client, bkash_live):
    pid = _create(client).json()["payment_id"]
    client.get("/api/payments/bkash/callback", params={"paymentID": _bkash_pid(client, pid), "status": "cancel"})
    assert _payment(client, pid)["status"] == "cancelled"


def test_bkash_callback_ignores_mock_payments(client, mock_mode):
    pid = _create(client).json()["payment_id"]
    mock_id = _bkash_pid(client, pid)
    assert re.match(r"MOCK-", mock_id)
    r = client.get("/api/payments/bkash/callback", params={"paymentID": mock_id, "status": "success"})
    assert "খুঁজে পাওয়া যায়নি" in r.text
    assert _payment(client, pid)["status"] == "pending"


def test_completed_trx_helper():
    ok = {"transactionStatus": "Completed", "trxID": "T", "amount": "249"}
    assert bkash.completed_trx(ok, 249) == "T"
    assert bkash.completed_trx({**ok, "transactionStatus": "Initiated"}, 249) is None
    assert bkash.completed_trx({**ok, "amount": "abc"}, 249) is None
