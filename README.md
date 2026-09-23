# চাকরি AI (Chakri AI)

বাংলাদেশের চাকরিপ্রার্থীদের জন্য AI ভিত্তিক ক্যারিয়ার সহায়ক অ্যাপ।

## বর্তমান অবস্থা
- ✅ Phase 1: AI Resume Builder (ব্যাকএন্ড + Flutter UI)
- ✅ Backend + Flutter UI: Job Circular লিস্ট, সার্চ, ফিল্টার, বিস্তারিত
- ✅ Backend + Flutter UI: Exam Question Bank (বিষয় → প্রশ্ন তালিকা → উত্তর দেখা)
- ✅ Backend + Flutter: Push Notification (Firebase) — রেজিস্ট্রেশন যুক্ত
- ⏳ বাকি: Study Material পড়ার স্ক্রিন (API রেডি, UI বাকি), Scraper selector, Firebase প্রজেক্ট সেটআপ

## প্রজেক্ট স্ট্রাকচার
```
chakri-ai/
├── backend/
│   ├── main.py                    FastAPI অ্যাপ এন্ট্রি পয়েন্ট
│   ├── database.py                DB কানেকশন
│   ├── models.py                  SQLAlchemy মডেল (Circular, Question, Subject...)
│   ├── schemas.py                 Pydantic স্কিমা
│   ├── scheduler.py                পর্যায়ক্রমিক স্ক্র্যাপিং + নোটিফিকেশন ট্রিগার
│   ├── routers/
│   │   ├── circulars.py           /api/circulars/*
│   │   ├── questions.py           /api/questions/*, /api/study/*
│   │   └── notifications.py       /api/notifications/*
│   ├── scrapers/
│   │   ├── base_scraper.py        সব স্ক্র্যাপারের বেস ক্লাস
│   │   └── site_scrapers.py       bdjobs/govt সাইটের স্ক্র্যাপার (selector আপডেট করা লাগবে)
│   ├── notifications/
│   │   └── fcm_service.py         Firebase পুশ নোটিফিকেশন
│   ├── requirements.txt
│   └── .env.example
└── mobile_app/       Flutter অ্যাপ
    ├── pubspec.yaml
    └── lib/
        ├── main.dart
        ├── models/resume_models.dart
        ├── services/api_service.dart
        └── screens/
            ├── home_screen.dart
            ├── resume_form_screen.dart
            └── resume_preview_screen.dart
```

## ব্যাকএন্ড চালানোর নিয়ম

1. Python 3.10+ থাকতে হবে
2. টার্মিনালে:
   ```bash
   cd backend
   pip install -r requirements.txt
   cp .env.example .env
   ```
3. `.env` ফাইল খুলে আপনার Anthropic API key বসান:
   ```
   ANTHROPIC_API_KEY=sk-ant-xxxxxxxx
   ```
   (API key পাবেন console.anthropic.com থেকে)
4. সার্ভার চালু করুন:
   ```bash
   uvicorn main:app --reload
   ```
5. ব্রাউজারে `http://127.0.0.1:8000` খুললে `{"status":"ok"}` দেখা উচিত।

## Flutter অ্যাপ চালানোর নিয়ম

1. Flutter SDK ইনস্টল করুন (যদি না থাকে): https://docs.flutter.dev/get-started/install
2. টার্মিনালে:
   ```bash
   cd mobile_app
   flutter pub get
   ```
3. Android Emulator/ফোন কানেক্ট করে:
   ```bash
   flutter run
   ```
4. **গুরুত্বপূর্ণ:** `lib/services/api_service.dart` ফাইলে `baseUrl` চেক করুন:
   - Android Emulator ব্যবহার করলে: `http://10.0.2.2:8000` (ডিফল্ট, ঠিক আছে)
   - রিয়েল ফোনে টেস্ট করলে: আপনার কম্পিউটারের লোকাল IP address ব্যবহার করুন (যেমন `http://192.168.1.5:8000`)
   - প্রোডাকশনে: আপনার ডিপ্লয় করা সার্ভারের URL

## Job Circular Scraper সেটআপ

`backend/scrapers/site_scrapers.py` ফাইলে স্কেলেটন কোড আছে, কিন্তু CSS selector গুলো placeholder — এগুলো কাজ করবে না যতক্ষণ না আপনি:

1. আসল সাইটে (যেমন jobs.bdjobs.com) গিয়ে ব্রাউজারে Inspect Element (F12) দিয়ে চেক করুন কোন class/id তে টাইটেল, ডেডলাইন ইত্যাদি আছে
2. `site_scrapers.py`-তে `TODO` কমেন্ট চিহ্নিত জায়গাগুলোতে সঠিক selector বসান
3. প্রতিটা নতুন সোর্সের জন্য `BaseScraper` থেকে ইনহেরিট করে নতুন ক্লাস বানান, `ALL_SCRAPERS` লিস্টে যোগ করুন
4. **আইনি সতর্কতা:** প্রতিটা সাইটের robots.txt ও ToS চেক করে নেবেন। সরকারি সাইটে RSS/API থাকলে সেটাই ব্যবহার করা ভালো।

শিডিউলার চালানোর নিয়ম (আলাদা টার্মিনালে, API সার্ভারের পাশাপাশি):
```bash
cd backend
python scheduler.py
```

## Push Notification (Firebase) সেটআপ

### ব্যাকএন্ড সাইড
1. https://console.firebase.google.com এ নতুন প্রজেক্ট বানান
2. Project Settings → Service Accounts → Generate new private key
3. ডাউনলোড হওয়া JSON ফাইলটা `backend/firebase-service-account.json` নামে রাখুন (এটা `.gitignore`-এ আছে)

### Flutter সাইড
1. FlutterFire CLI ইনস্টল করুন:
   ```bash
   dart pub global activate flutterfire_cli
   ```
2. একই Firebase প্রজেক্টে অ্যাপ কানেক্ট করুন (এটা `firebase_options.dart` অটো-জেনারেট করবে):
   ```bash
   cd mobile_app
   flutterfire configure
   ```
3. Android এ push notification পেতে `android/app/build.gradle`-এ Google Services plugin লাগবে — `flutterfire configure` এটা সাধারণত অটোমেটিক করে দেয়, তবুও build error পেলে FlutterFire-এর অফিসিয়াল ডকুমেন্টেশন চেক করুন
4. `lib/main.dart`-এ ইতিমধ্যে `Firebase.initializeApp()` এবং `NotificationService().init()` কল করা আছে — এই কল আপাতত try/catch এ মোড়ানো, তাই Firebase সেটআপ না করা পর্যন্ত অ্যাপের বাকি অংশ স্বাভাবিকভাবে চলবে
5. সেটআপ শেষে ডিভাইস টোকেন স্বয়ংক্রিয়ভাবে ব্যাকএন্ডে (`/api/notifications/register-device`) রেজিস্টার হয়ে যাবে

## পরবর্তী ধাপ (Roadmap)

- [x] Phase 1: AI Resume Builder
- [x] Backend + Flutter: Job Circular list/detail
- [x] Backend + Flutter: Question Bank browse (বিষয় → প্রশ্ন → উত্তর)
- [x] Backend + Flutter: Notification registration স্ট্রাকচার
- [ ] Flutter UI: Study Material পড়ার স্ক্রিন (API আছে, স্ক্রিন বাকি)
- [ ] Phase 2: Cover Letter Generator UI (ব্যাকএন্ড রেডি)
- [ ] Scraper: আসল সাইটের selector বসিয়ে টেস্ট করা
- [ ] নোটিফিকেশন ট্যাপ করলে সরাসরি Circular Detail এ নেভিগেট করা (navigatorKey সেটআপ লাগবে)
- [ ] Phase 3: Mock Interview Coach
- [ ] Phase 4: Skill Gap Analysis

## নোট
- বর্তমানে Flutter UI-তে "AI রিজিউম বিল্ডার", "চাকরির সার্কুলার", "প্রশ্নব্যাংক ও স্টাডি" — এই তিনটা ফিচার চালু আছে; বাকিগুলো ব্যাকএন্ডে আংশিক রেডি
- প্রশ্ন ব্যাংক ম্যানুয়ালি এন্ট্রি করতে `/api/questions/bulk` এন্ডপয়েন্ট ব্যবহার করে একসাথে অনেক প্রশ্ন আপলোড করা যাবে (PDF থেকে পার্স করে JSON বানিয়ে)
- **⚠️ গুরুত্বপূর্ণ:** Flutter কোড এই sandbox-এ কম্পাইল করে টেস্ট করা সম্ভব হয়নি (Flutter SDK এখানে ইনস্টলযোগ্য নয়)। ইম্পোর্ট পাথ ও ব্র্যাকেট ব্যালেন্স ম্যানুয়ালি যাচাই করা হয়েছে, কিন্তু `flutter pub get` ও `flutter run` করার পর ছোটখাটো টাইপো/এরর থাকলে ঠিক করে দেব — নিশ্চিন্তে এরর মেসেজ শেয়ার করবেন
