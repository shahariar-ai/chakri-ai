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

## ধাপ ৮ (~10:25) ✅
- সব ডেটা-স্ক্রিনে (সার্কুলার তালিকা/বিস্তারিত, সাবজেক্ট, প্রশ্নব্যাংক, স্টাডি মেটেরিয়াল) loading/error(আবার চেষ্টা)/empty আগে থেকেই ছিল — যাচাই করা হয়েছে; error বার্তা থেকে "Exception:" প্রিফিক্স সরানো।
- প্রশ্নব্যাংকে AI-content disclaimer + প্রতিটা প্রশ্নে "ভুল জানান" (ইমেইল খসড়া, প্রশ্ন ID সহ; Android mailto query যোগ)।
- সার্কুলার তালিকা ও বিস্তারিতে সোর্স নোট (bpsc.gov.bd ইত্যাদি অফিসিয়াল সাইট, যাচাইয়ের পরামর্শ)।
- flutter analyze: clean; flutter test: 11/11 pass।

## ধাপ ৯ (~10:50) ✅
- `store_listing/` : privacy_policy.html, terms.html, refund_policy.html (প্রতিটায় বাংলা+English), যোগাযোগ shahriar.sharif406@gmail.com, ডেটা/Claude API/ডিভাইস টোকেন/মোছার নিয়ম আছে। `HOSTING_GITHUB_PAGES.md` — হোস্টিংয়ের ধাপ। ⚠️ খসড়া, আইনজীবী দেখালে ভালো।

## ধাপ ৫ — Google Play payment নীতি যাচাই (web search) ✅
- **ফলাফল:** অ্যাপের ভেতরে ডিজিটাল পণ্য/সাবস্ক্রিপশন/প্রিমিয়াম ফিচার বিক্রিতে সাধারণভাবে **Google Play Billing বাধ্যতামূলক** (নীতির নির্দিষ্ট ব্যতিক্রম ছাড়া)। অ্যাপ থেকে অন্য পেমেন্ট মাধ্যমে (যেমন bKash/Nagad ওয়েব পেজ) ইউজারকে পাঠানোও সাধারণত নিষিদ্ধ। বিকল্প বিলিং শুধু নির্দিষ্ট অঞ্চলে (EEA, দক্ষিণ কোরিয়া, ভারত, মার্কিন যুক্তরাষ্ট্র ইত্যাদি) — **বাংলাদেশ তালিকায় পাইনি**।
- **ঝুঁকি:** বর্তমান bKash/Nagad প্রিমিয়াম ফ্লো সহ Play-তে গেলে নীতি লঙ্ঘনে অ্যাপ reject/suspend হতে পারে।
- **সিদ্ধান্ত:** প্রথম release-এ `PAYMENTS_ENABLED=false` (ডিফল্ট), সব ফিচার ফ্রি। পরে প্রিমিয়াম চাইলে Play Billing (`in_app_purchase` প্যাকেজ) ব্যবহার করতে হবে; Play-তে bKash/Nagad সরাসরি চলবে বলে নিশ্চিত হইনি (তৃতীয়-পক্ষ সূত্রে Play-র নিজস্ব পেমেন্ট মেথডে bKash লিংক করার কথা আছে, কিন্তু অনানুষ্ঠানিক)। যাচাইয়ের সূত্র: [Payments policy](https://support.google.com/googleplay/android-developer/answer/10281818?hl=en)।
- **বিকল্প:** bKash/Nagad শুধু ওয়েবসাইট বা Play-বহির্ভূত (sideload/APK) বিতরণে।

## ধাপ ১০ (~11:10) ✅
- `store_listing/LISTING.md` (নাম, short/full description বাংলা+English), `DATA_SAFETY_AND_RATING.md`, `GRAPHICS_AND_TESTING.md` (screenshot তালিকা, feature graphic নির্দেশ, closed testing শর্ত)।
- closed testing (web search): নতুন personal account → ১২ tester × একটানা ১৪ দিন, তারপর production access আবেদন।

## ধাপ ১১ — appbundle build ⚠️ সম্পন্ন হয়নি
- `flutter build appbundle --release` শুরু হয়েছিল, কিন্তু সিস্টেমে RAM কম থাকায় Claude Code প্রক্রিয়াটি বন্ধ করে দেয় (কোড/কনফিগের ত্রুটি নয়)। নিরাপত্তার জন্য নিজে থেকে আবার চালাইনি।
- আপনি অন্য অ্যাপ বন্ধ করে নিজে চালান:
  `cd mobile_app && flutter build appbundle --release --dart-define=API_BASE_URL=https://<render-url>`
- keystore (`key.properties`) না থাকলে debug key দিয়ে sign হবে — Play Store-এ আপলোডযোগ্য নয়।
- debug-signed বিল্ড আগে যাচাই হয়নি; `flutter analyze` ও `flutter test` pass, Gradle-এর signing/targetSdk 36 কনফিগ বিল্ডে এখনো পরীক্ষিত নয়।

---
# চূড়ান্ত সারাংশ (2026-10-12)

## সম্পূর্ণ
ধাপ ২–১০ (কোড ও কাগজ): package `com.futuretechai.chakriai`, targetSdk 36, v1.0.0+1, আইকন, signing কনফিগ, API URL/retry/বাংলা loading, PAYMENTS_ENABLED=false, Firebase-ছাড়া নিরাপদ, rate limiting, UX disclaimer/ভুল জানান/সোর্স নোট, আইনি পাতা, Play listing/Data Safety/rating খসড়া।
টেস্ট: pytest 87 pass, flutter analyze clean, flutter test 11 pass।

## বাকি (আপনাকে করতে হবে)
1. GitHub repo বানিয়ে remote যোগ ও push (NEEDS_USER.md #1) — push-এর আগে `git ls-files` দিয়ে .env/*.db/*.bak/key নেই নিশ্চিত করুন
2. Play Developer account ফি ($25) ও পরিচয় যাচাই
3. keystore বানানো ও key.properties (KEYSTORE_GUIDE.md)
4. Firebase project + google-services.json (NEEDS_USER.md #2)
5. Render deploy: ANTHROPIC_API_KEY সেট করুন, আসল URL জানান
6. Screenshot ও feature graphic (store_listing/GRAPHICS_AND_TESTING.md)
7. bKash/Nagad live credential — এবং Play Billing সিদ্ধান্ত (আগে নীতি ঝুঁকি দেখুন)
8. আইনি পাতা GitHub Pages-এ হোস্ট করুন

## Play Store আপলোডের ক্রম
1. Render deploy → URL নিশ্চিত
2. keystore বানান → `flutter build appbundle --release --dart-define=API_BASE_URL=...`
3. Play Console-এ অ্যাপ তৈরি, listing/privacy URL/Data Safety/Content rating পূরণ
4. Closed testing-এ .aab আপলোড, ১২+ tester ১৪ দিন
5. Production access আবেদন → Production release
