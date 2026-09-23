"""
Firebase Cloud Messaging (FCM) দিয়ে পুশ নোটিফিকেশন পাঠানোর সার্ভিস।

সেটআপ:
1. https://console.firebase.google.com এ প্রজেক্ট বানান
2. Project Settings > Service Accounts > Generate new private key
   ডাউনলোড করা JSON ফাইলটা backend/firebase-service-account.json হিসেবে রাখুন
   (⚠️ এই ফাইলটা .gitignore-এ রাখবেন, কখনো পাবলিক রিপোতে কমিট করবেন না)
3. Flutter অ্যাপে firebase_messaging প্যাকেজ যোগ করে ডিভাইস টোকেন নিয়ে
   /api/notifications/register-device এন্ডপয়েন্টে পাঠান
"""
import os
import logging

logger = logging.getLogger(__name__)

FIREBASE_CRED_PATH = os.getenv("FIREBASE_CRED_PATH", "firebase-service-account.json")

_firebase_app = None


def _init_firebase():
    global _firebase_app
    if _firebase_app is not None:
        return _firebase_app

    if not os.path.exists(FIREBASE_CRED_PATH):
        logger.warning(
            "Firebase credential file পাওয়া যায়নি (%s) — নোটিফিকেশন পাঠানো হবে না। "
            "README দেখে সেটআপ করুন।",
            FIREBASE_CRED_PATH,
        )
        return None

    import firebase_admin
    from firebase_admin import credentials

    cred = credentials.Certificate(FIREBASE_CRED_PATH)
    _firebase_app = firebase_admin.initialize_app(cred)
    return _firebase_app


def send_push_to_all(title: str, body: str, tokens: list[str], data: dict | None = None) -> dict:
    """
    একাধিক ডিভাইসে (topic-less, token-based) পুশ নোটিফিকেশন পাঠায়।
    tokens বেশি হলে (>500) FCM ব্যাচে ভাগ করে পাঠানো উচিত — এখানে সরলীকৃত ভার্সন।
    """
    app = _init_firebase()
    if app is None or not tokens:
        return {"sent": 0, "reason": "firebase not configured or no tokens"}

    from firebase_admin import messaging

    success_count = 0
    failed_tokens = []

    # FCM এর multicast লিমিট ৫০০ - ব্যাচে ভাগ করছি
    batch_size = 500
    for i in range(0, len(tokens), batch_size):
        batch = tokens[i : i + batch_size]
        message = messaging.MulticastMessage(
            notification=messaging.Notification(title=title, body=body),
            data=data or {},
            tokens=batch,
        )
        try:
            response = messaging.send_multicast(message)
            success_count += response.success_count
            for idx, resp in enumerate(response.responses):
                if not resp.success:
                    failed_tokens.append(batch[idx])
        except Exception as e:
            logger.error("FCM send failed: %s", e)

    return {"sent": success_count, "failed_tokens": failed_tokens}
