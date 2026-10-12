# PROGRESS (অগ্রগতি)

## ধাপ ০ — অবস্থা যাচাই (2026-10-12 ~09:05)
- git: branch main, working tree clean, commit ২টা (576b526, 255a578)।
- **git remote নেই → GitHub-এ push হয়নি।**
- backend pytest: 85 passed
- flutter analyze: No issues found
- flutter test: 11 টেস্ট সব pass
- আগেই হয়ে আছে: Render prep (render.yaml), job matching, PDF export, payments, interview।
- পরবর্তী: ধাপ ১ (remote নেই → NEEDS_USER), ধাপ ২।

## ধাপ ১ (~09:10)
- remote নেই → push করা যায়নি, NEEDS_USER.md-তে লেখা। কাজ চালিয়ে যাচ্ছি, সব লোকাল commit।

## ধাপ ২-৩ (~09:25) ✅
- package: `com.futuretechai.chakriai` (build.gradle namespace/applicationId, MainActivity ফোল্ডার+package), app label "চাকরি AI"।
- version 1.0.0+1; targetSdk 36 (Play: 31 Aug 2026 থেকে নতুন অ্যাপ/আপডেটে API 36 লাগে; web search-এ যাচাই — developer.android.com/google/play/requirements/target-sdk)।
- flutter_launcher_icons 0.14.4 দিয়ে adaptive icon (নীল ব্যাকগ্রাউন্ড + ব্রিফকেস/চেক)।
- signing: android/key.properties থাকলে release key, না থাকলে debug key। `key.properties.example` + `KEYSTORE_GUIDE.md` লেখা।

## ধাপ ৪-৫ (code) (~09:40) ✅
- api_service: release-এ ডিফল্ট `https://chakri-ai-backend.onrender.com` (render.yaml-এর নাম অনুযায়ী অনুমান — আসল URL হলে --dart-define=API_BASE_URL দিন), debug-এ 10.0.2.2/localhost। cleartext release-এ বন্ধ (targetSdk 36 ডিফল্ট)।
- ৬০ সেকেন্ড timeout + ৩ বার retry, ৫ সেকেন্ডের বেশি লাগলে বাংলা "সার্ভার ঘুম থেকে জাগছে" বার্তা (main.dart overlay)।
- `AppConfig.paymentsEnabled` (--dart-define=PAYMENTS_ENABLED, ডিফল্ট false) — হোম থেকে প্রিমিয়াম কার্ড লুকানো।
- flutter analyze: clean; flutter test: 11/11 pass।

## ধাপ ৬ (~09:50) ✅
- Firebase gradle plugin/google-services.json নেই; main.dart-এ Firebase init try/catch-এ — Firebase ছাড়াই অ্যাপ ক্র্যাশ করে না (flutter test pass)। দরকারি তথ্য NEEDS_USER.md-তে।

## ধাপ ৭ (~10:00) ✅
- নতুন `backend/rate_limit.py` middleware: AI endpoint (resume/cover-letter/interview/job-match) প্রতি IP 10/মিনিট, 60/ঘণ্টা (env দিয়ে বদলানো যায়), সীমা পেরোলে বাংলা 429 + Retry-After। নতুন dependency নেই।
- /api/health (DB চেক সহ), render.yaml (Postgres, alembic, healthCheck, secrets sync:false), requirements.txt, CORS (CORS_ORIGINS env, ডিফল্ট *; cookie নেই) যাচাই করা — ঠিক আছে।
- pytest: 87 passed (rate limit-এর ২টা নতুন টেস্ট সহ)।
- ⚠️ in-memory limiter: একাধিক ইনস্ট্যান্সে গেলে Redis লাগবে; Render free-তে এক ইনস্ট্যান্স তাই ঠিক।
