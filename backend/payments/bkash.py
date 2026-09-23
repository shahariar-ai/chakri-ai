"""
bKash Tokenized Checkout (API v1.2.0-beta) ক্লায়েন্ট।

ফ্লো:
  1. grant token  -> id_token (১ ঘণ্টা মেয়াদ, ক্যাশ করা হয়)
  2. create       -> paymentID + bkashURL (ইউজারকে এই URL-এ পাঠাতে হয়)
  3. ইউজার পেমেন্ট শেষে bKash আমাদের callbackURL-এ ?paymentID=..&status=success|failure|cancel সহ redirect করে
  4. execute      -> আসল টাকা কাটা হয়, trxID আসে
  5. query        -> execute টাইমআউট/এরর হলে আসল অবস্থা জানার জন্য

⚠️ মার্চেন্ট ক্রেডেনশিয়াল (.env) ছাড়া এটা চালানো/টেস্ট করা হয়নি।
bKash মার্চেন্ট অ্যাকাউন্ট খুলে sandbox ক্রেডেনশিয়াল দিয়ে প্রথমে end-to-end টেস্ট করতে হবে।

দরকারি env:
  BKASH_BASE_URL   sandbox: https://tokenized.sandbox.bka.sh/v1.2.0-beta
                   live:    https://tokenized.pay.bka.sh/v1.2.0-beta
  BKASH_APP_KEY, BKASH_APP_SECRET, BKASH_USERNAME, BKASH_PASSWORD
"""
import os
import time
from typing import Optional

import requests

SANDBOX_BASE_URL = "https://tokenized.sandbox.bka.sh/v1.2.0-beta"
_TIMEOUT = 30  # সেকেন্ড

_token_cache: dict = {"id_token": None, "expires_at": 0.0}


class BkashError(Exception):
    pass


def is_configured() -> bool:
    return all(os.getenv(k) for k in ("BKASH_APP_KEY", "BKASH_APP_SECRET", "BKASH_USERNAME", "BKASH_PASSWORD"))


def _base_url() -> str:
    return os.getenv("BKASH_BASE_URL", SANDBOX_BASE_URL).rstrip("/")


def _grant_token() -> str:
    # মেয়াদ শেষের ৫ মিনিট আগে পর্যন্ত ক্যাশ করা টোকেন ব্যবহার
    if _token_cache["id_token"] and time.time() < _token_cache["expires_at"] - 300:
        return _token_cache["id_token"]

    resp = requests.post(
        f"{_base_url()}/tokenized/checkout/token/grant",
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "username": os.getenv("BKASH_USERNAME", ""),
            "password": os.getenv("BKASH_PASSWORD", ""),
        },
        json={"app_key": os.getenv("BKASH_APP_KEY"), "app_secret": os.getenv("BKASH_APP_SECRET")},
        timeout=_TIMEOUT,
    )
    data = resp.json()
    token = data.get("id_token")
    if not token:
        raise BkashError(f"bKash token grant ব্যর্থ: {data.get('statusMessage') or data}")
    _token_cache["id_token"] = token
    _token_cache["expires_at"] = time.time() + int(data.get("expires_in", 3600))
    return token


def _post(path: str, body: dict) -> dict:
    resp = requests.post(
        f"{_base_url()}/tokenized/checkout/{path}",
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": _grant_token(),
            "X-APP-Key": os.getenv("BKASH_APP_KEY", ""),
        },
        json=body,
        timeout=_TIMEOUT,
    )
    return resp.json()


def create_payment(amount: int, invoice_number: str, payer_reference: str, callback_url: str) -> dict:
    """সফল হলে {'paymentID', 'bkashURL', ...} রিটার্ন করে।"""
    data = _post("create", {
        "mode": "0011",  # tokenized checkout (agreement ছাড়া)
        "payerReference": payer_reference,
        "callbackURL": callback_url,
        "amount": str(amount),
        "currency": "BDT",
        "intent": "sale",
        "merchantInvoiceNumber": invoice_number,
    })
    if data.get("statusCode") != "0000" or not data.get("bkashURL"):
        raise BkashError(f"bKash create payment ব্যর্থ: {data.get('statusMessage') or data}")
    return data


def execute_payment(payment_id: str) -> dict:
    return _post("execute", {"paymentID": payment_id})


def query_payment(payment_id: str) -> dict:
    return _post("payment/status", {"paymentID": payment_id})


def completed_trx(result: dict, expected_amount: int) -> Optional[str]:
    """execute/query রেসপন্স সফল ও amount মিললে trxID, নাহলে None।"""
    if result.get("transactionStatus") != "Completed" or not result.get("trxID"):
        return None
    try:
        if float(result.get("amount", 0)) != float(expected_amount):
            return None
    except (TypeError, ValueError):
        return None
    return result["trxID"]
