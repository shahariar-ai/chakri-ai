"""
প্রিমিয়াম সাবস্ক্রিপশন ও পেমেন্ট API (/api/payments/*)।

প্রোভাইডার ও মোড:
  - bkash : .env-এ bKash ক্রেডেনশিয়াল থাকলে "live" (payments/bkash.py), নাহলে mock
  - nagad : আসল ইন্টিগ্রেশন এখনো নেই (মার্চেন্ট অ্যাকাউন্ট + RSA key লাগবে) — শুধু mock
  - mock মোড চালু হয় কেবল PAYMENT_MOCK_ENABLED=true হলে (ডেভেলপমেন্ট)। তখন আমাদের নিজেদের
    সিমুলেটেড চেকআউট পেজ খোলে — আসল টাকা লেনদেন হয় না। প্রোডাকশনে কখনো চালু করবেন না।

নিয়ম: অ্যাপের কথায় কখনো পেমেন্ট "সফল" ধরা হয় না — সার্ভার নিজে প্রোভাইডারের কাছ থেকে
execute/query করে amount মিলিয়ে তারপর completed করে।
"""
import os
import re
import uuid
from datetime import datetime, timedelta
from html import escape
from typing import List, Literal, Optional
from urllib.parse import quote

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

import models
from database import get_db
from payments import bkash

router = APIRouter(prefix="/api/payments", tags=["Payments"])

# ⚠️ দাম placeholder — চূড়ান্ত দাম ঠিক করে এখানে বসাতে হবে
PLANS = {
    "monthly": {"name": "মাসিক", "amount": 99, "days": 30},
    "quarterly": {"name": "৩ মাস", "amount": 249, "days": 90},
    "yearly": {"name": "বার্ষিক", "amount": 799, "days": 365},
}


def _mock_enabled() -> bool:
    return os.getenv("PAYMENT_MOCK_ENABLED", "").lower() == "true"


PROVIDER_NAMES = {"bkash": "bKash", "nagad": "Nagad"}
MOCK_PREFIX = "MOCK-"  # mock পেমেন্টের provider_payment_id এই prefix দিয়ে শুরু হয়


def _provider_mode(provider: str) -> Optional[str]:
    """'live', 'mock', অথবা None (এই মুহূর্তে এই প্রোভাইডারে পেমেন্ট করা যাবে না)।"""
    if provider == "bkash" and bkash.is_configured():
        return "live"
    if provider in PROVIDER_NAMES and _mock_enabled():
        return "mock"
    return None


def _public_base_url(request: Request) -> str:
    # bKash callback-এর জন্য ব্রাউজার থেকে পৌঁছানো যায় এমন URL; প্রোডাকশনে PUBLIC_BASE_URL সেট করতে হবে
    return os.getenv("PUBLIC_BASE_URL", str(request.base_url)).rstrip("/")


# ---------- Schemas ----------

class PlanOut(BaseModel):
    code: str
    name: str
    amount: int
    days: int


class ProviderOut(BaseModel):
    code: str
    name: str
    mode: Optional[str]  # live | mock | null (চালু নেই)


class PlansResponse(BaseModel):
    plans: List[PlanOut]
    providers: List[ProviderOut]


class PaymentCreate(BaseModel):
    subscriber_id: str = Field(..., min_length=8, max_length=64)
    plan_code: str
    provider: Literal["bkash", "nagad"]


class PaymentCreated(BaseModel):
    payment_id: int
    redirect_url: str


class PaymentOut(BaseModel):
    id: int
    plan_code: str
    amount: int
    provider: str
    status: str
    trx_id: Optional[str] = None
    failure_reason: Optional[str] = None
    is_test: bool = False


class SubscriptionStatus(BaseModel):
    subscriber_id: str
    is_premium: bool
    plan_code: Optional[str] = None
    expires_at: Optional[datetime] = None


# ---------- Helpers ----------

def _mark_completed(db: Session, payment: models.Payment, trx_id: str):
    payment.status = models.PaymentStatus.completed
    payment.trx_id = trx_id
    payment.completed_at = datetime.utcnow()
    db.commit()


def _mark_failed(db: Session, payment: models.Payment, status: models.PaymentStatus, reason: str):
    payment.status = status
    payment.failure_reason = reason[:255]
    db.commit()


def _result_page(success: bool, message: str) -> HTMLResponse:
    """পেমেন্ট শেষে ব্রাউজারে দেখানো পেজ — ইউজারকে অ্যাপে ফিরে যেতে বলে।"""
    color = "#0F6E5C" if success else "#B3261E"
    title = "পেমেন্ট সফল হয়েছে" if success else "পেমেন্ট সম্পন্ন হয়নি"
    return HTMLResponse(f"""<!doctype html><html lang="bn"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>চাকরি AI - পেমেন্ট</title></head>
<body style="font-family:sans-serif;text-align:center;padding:48px 16px;background:#F7F8FA">
<h2 style="color:{color}">{title}</h2><p>{escape(message)}</p>
<p style="color:#555">এখন চাকরি AI অ্যাপে ফিরে যান।</p></body></html>""")


def subscription_status(db: Session, subscriber_id: str) -> SubscriptionStatus:
    """completed পেমেন্টগুলো সময়ক্রমে সাজিয়ে মেয়াদ যোগ করা হয় (আগের মেয়াদ থাকতে কিনলে তার পরে যোগ হয়)।"""
    payments = (
        db.query(models.Payment)
        .filter(models.Payment.subscriber_id == subscriber_id,
                models.Payment.status == models.PaymentStatus.completed)
        .order_by(models.Payment.completed_at)
        .all()
    )
    expires_at, plan_code = None, None
    for p in payments:
        days = PLANS.get(p.plan_code, {}).get("days", 0)
        start = max(expires_at, p.completed_at) if expires_at else p.completed_at
        expires_at = start + timedelta(days=days)
        plan_code = p.plan_code

    is_premium = expires_at is not None and expires_at > datetime.utcnow()
    return SubscriptionStatus(
        subscriber_id=subscriber_id,
        is_premium=is_premium,
        plan_code=plan_code if is_premium else None,
        expires_at=expires_at if is_premium else None,
    )


# ---------- Endpoints ----------

@router.get("/plans", response_model=PlansResponse)
def list_plans():
    return PlansResponse(
        plans=[PlanOut(code=c, **p) for c, p in PLANS.items()],
        providers=[ProviderOut(code=c, name=n, mode=_provider_mode(c)) for c, n in PROVIDER_NAMES.items()],
    )


@router.post("/create", response_model=PaymentCreated)
def create_payment(data: PaymentCreate, request: Request, db: Session = Depends(get_db)):
    plan = PLANS.get(data.plan_code)
    if not plan:
        raise HTTPException(status_code=400, detail="অজানা প্ল্যান")
    mode = _provider_mode(data.provider)
    if mode is None:
        raise HTTPException(status_code=503, detail=f"{PROVIDER_NAMES[data.provider]} পেমেন্ট এখনো চালু হয়নি")

    payment = models.Payment(
        subscriber_id=data.subscriber_id,
        plan_code=data.plan_code,
        amount=plan["amount"],
        provider=data.provider,
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)

    base = _public_base_url(request)
    if mode == "mock":
        payment.provider_payment_id = f"{MOCK_PREFIX}{uuid.uuid4().hex[:12]}"
        db.commit()
        return PaymentCreated(payment_id=payment.id, redirect_url=f"{base}/api/payments/mock/checkout/{payment.id}")

    try:
        result = bkash.create_payment(
            amount=payment.amount,
            invoice_number=f"CHAKRI-{payment.id}-{uuid.uuid4().hex[:8]}",
            payer_reference=data.subscriber_id[:32],
            callback_url=f"{base}/api/payments/bkash/callback",
        )
    except Exception as e:
        _mark_failed(db, payment, models.PaymentStatus.failed, str(e))
        raise HTTPException(status_code=502, detail="bKash পেমেন্ট শুরু করা যায়নি")

    payment.provider_payment_id = result["paymentID"]
    db.commit()
    return PaymentCreated(payment_id=payment.id, redirect_url=result["bkashURL"])


@router.get("/bkash/callback", response_class=HTMLResponse)
def bkash_callback(paymentID: str, status: str, db: Session = Depends(get_db)):
    payment = (
        db.query(models.Payment)
        .filter(models.Payment.provider == "bkash", models.Payment.provider_payment_id == paymentID,
                ~models.Payment.provider_payment_id.startswith(MOCK_PREFIX))
        .first()
    )
    if not payment:
        return _result_page(False, "পেমেন্টটি খুঁজে পাওয়া যায়নি।")
    # callback একাধিকবার আসলেও একবারই প্রসেস হবে
    if payment.status != models.PaymentStatus.pending:
        return _result_page(payment.status == models.PaymentStatus.completed, "পেমেন্ট আগেই প্রসেস হয়েছে।")

    if status != "success":
        new_status = models.PaymentStatus.cancelled if status == "cancel" else models.PaymentStatus.failed
        _mark_failed(db, payment, new_status, f"bKash callback status={status}")
        return _result_page(False, "আপনি পেমেন্ট বাতিল করেছেন বা এটি ব্যর্থ হয়েছে। কোনো টাকা কাটা হয়নি।")

    try:
        result = bkash.execute_payment(paymentID)
    except Exception:
        # execute টাইমআউট হলেও টাকা কেটে থাকতে পারে — তাই query করে আসল অবস্থা দেখা
        try:
            result = bkash.query_payment(paymentID)
        except Exception as e:
            return _result_page(False, f"পেমেন্ট যাচাই করা যায়নি, কিছুক্ষণ পরে অ্যাপে স্ট্যাটাস চেক করুন। ({e})")

    trx_id = bkash.completed_trx(result, payment.amount)
    if trx_id:
        _mark_completed(db, payment, trx_id)
        return _result_page(True, f"ট্রানজেকশন আইডি: {trx_id}")

    _mark_failed(db, payment, models.PaymentStatus.failed,
                 f"execute: {result.get('statusMessage') or result.get('transactionStatus')}")
    return _result_page(False, "bKash পেমেন্ট সম্পন্ন হয়নি।")


def _is_mock(payment: models.Payment) -> bool:
    return (payment.provider_payment_id or "").startswith(MOCK_PREFIX)


def _get_mock_payment(db: Session, payment_id: int) -> models.Payment:
    if not _mock_enabled():
        raise HTTPException(status_code=404)
    payment = db.get(models.Payment, payment_id)
    if not payment or not _is_mock(payment):
        raise HTTPException(status_code=404)
    return payment


_MOCK_PAGE_STYLE = """<style>
body{font-family:sans-serif;background:#F7F8FA;margin:0;padding:24px 16px;color:#222}
.box{max-width:380px;margin:0 auto;background:#fff;border-radius:16px;padding:20px;border:1px solid #e5e5e5}
.test{background:#FFF4CE;color:#7A5B00;border-radius:8px;padding:8px 10px;font-size:13px;margin-bottom:16px}
label{display:block;font-size:14px;margin:12px 0 4px}
input{width:100%;box-sizing:border-box;padding:10px;font-size:16px;border:1px solid #ccc;border-radius:8px}
button{width:100%;padding:12px;font-size:15px;border-radius:8px;border:0;margin-top:10px;cursor:pointer}
.pay{background:#0F6E5C;color:#fff}.fail{background:#eee}.cancel{background:#fff;border:1px solid #ccc}
.err{color:#B3261E;font-size:14px}
</style>"""


@router.get("/mock/checkout/{payment_id}", response_class=HTMLResponse)
def mock_checkout(payment_id: int, error: Optional[str] = None, db: Session = Depends(get_db)):
    """সিমুলেটেড চেকআউট পেজ — ওয়ালেট নম্বর + PIN চায় (আসল পেজের মতো), কিন্তু কোনো টাকা কাটে না।"""
    payment = _get_mock_payment(db, payment_id)
    provider = PROVIDER_NAMES.get(payment.provider, payment.provider)
    plan = PLANS.get(payment.plan_code, {}).get("name", payment.plan_code)
    if payment.status != models.PaymentStatus.pending:
        return _result_page(payment.status == models.PaymentStatus.completed, "এই পেমেন্ট আগেই প্রসেস হয়েছে।")

    err = f'<p class="err">{escape(error)}</p>' if error else ""
    return HTMLResponse(f"""<!doctype html><html lang="bn"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>টেস্ট পেমেন্ট - {provider}</title>
{_MOCK_PAGE_STYLE}</head><body><div class="box">
<div class="test">🧪 টেস্ট মোড — এটি {provider}-এর সিমুলেশন, কোনো আসল টাকা কাটা হবে না। আসল PIN দেবেন না।</div>
<h3 style="margin:0">চাকরি AI প্রিমিয়াম</h3>
<p style="margin:4px 0 0">প্ল্যান: {escape(plan)} &nbsp;·&nbsp; <b>৳{payment.amount}</b> &nbsp;·&nbsp; {provider}</p>
{err}
<form method="post" action="/api/payments/mock/complete/{payment.id}">
<label>{provider} ওয়ালেট নম্বর (টেস্ট)</label>
<input name="wallet" inputmode="numeric" placeholder="01XXXXXXXXX" maxlength="11">
<label>PIN (যেকোনো ৫ অঙ্ক)</label>
<input name="pin" type="password" inputmode="numeric" maxlength="5">
<button class="pay" name="outcome" value="success">পেমেন্ট নিশ্চিত করুন</button>
<button class="fail" name="outcome" value="failure">ব্যর্থতা সিমুলেট করুন (ব্যালেন্স নেই)</button>
<button class="cancel" name="outcome" value="cancel">বাতিল</button>
</form></div></body></html>""")


@router.post("/mock/complete/{payment_id}", response_class=HTMLResponse)
def mock_complete(
    payment_id: int,
    outcome: Literal["success", "failure", "cancel"] = Form(...),
    wallet: str = Form(""),
    pin: str = Form(""),
    db: Session = Depends(get_db),
):
    payment = _get_mock_payment(db, payment_id)
    if payment.status != models.PaymentStatus.pending:
        return _result_page(payment.status == models.PaymentStatus.completed, "এই পেমেন্ট আগেই প্রসেস হয়েছে।")

    if outcome == "cancel":
        _mark_failed(db, payment, models.PaymentStatus.cancelled, "mock: user cancelled")
        return _result_page(False, "আপনি পেমেন্ট বাতিল করেছেন। কোনো টাকা কাটা হয়নি।")
    if outcome == "failure":
        _mark_failed(db, payment, models.PaymentStatus.failed, "mock: insufficient balance")
        return _result_page(False, "পর্যাপ্ত ব্যালেন্স নেই (সিমুলেটেড)। কোনো টাকা কাটা হয়নি।")

    # আসল পেজের মতো ইনপুট যাচাই — ভুল হলে আবার ফর্মে ফেরত
    if not re.fullmatch(r"01[3-9]\d{8}", wallet.strip()):
        return RedirectResponse(
            f"/api/payments/mock/checkout/{payment.id}?error=" + quote("সঠিক ১১ অঙ্কের মোবাইল নম্বর দিন (01XXXXXXXXX)"),
            status_code=303,
        )
    if not re.fullmatch(r"\d{5}", pin.strip()):
        return RedirectResponse(
            f"/api/payments/mock/checkout/{payment.id}?error=" + quote("PIN ৫ অঙ্কের হতে হবে"),
            status_code=303,
        )

    _mark_completed(db, payment, f"TEST{payment.id:06d}")
    return _result_page(True, f"ট্রানজেকশন আইডি: {payment.trx_id} (টেস্ট)")


@router.get("/status/{subscriber_id}", response_model=SubscriptionStatus)
def get_subscription_status(subscriber_id: str, db: Session = Depends(get_db)):
    return subscription_status(db, subscriber_id)


@router.get("/{payment_id}", response_model=PaymentOut)
def get_payment(payment_id: int, subscriber_id: str, db: Session = Depends(get_db)):
    payment = db.get(models.Payment, payment_id)
    # অন্যের পেমেন্ট দেখা ঠেকাতে subscriber_id মিলিয়ে দেখা হয়
    if not payment or payment.subscriber_id != subscriber_id:
        raise HTTPException(status_code=404, detail="পেমেন্ট পাওয়া যায়নি")
    return PaymentOut(
        id=payment.id,
        plan_code=payment.plan_code,
        amount=payment.amount,
        provider=payment.provider,
        status=payment.status.value,
        trx_id=payment.trx_id,
        failure_reason=payment.failure_reason,
        is_test=_is_mock(payment),
    )
