# CLAUDE.md

এই ফাইলটা Claude Code-কে প্রজেক্টের কনটেক্সট দেওয়ার জন্য। কাজ শুরুর আগে পুরোটা পড়ে নাও।

## প্রজেক্ট পরিচিতি

**নাম:** চাকরি AI (Chakri AI)
**লক্ষ্য:** বাংলাদেশের চাকরিপ্রার্থীদের জন্য একটা সম্পূর্ণ AI-ভিত্তিক ক্যারিয়ার সহায়ক মোবাইল অ্যাপ।
**টার্গেট ইউজার:** বাংলাদেশের চাকরিপ্রার্থী — সরকারি/বেসরকারি চাকরি খুঁজছেন এমন মানুষ। বেশিরভাগ ইউজার বাংলায় স্বচ্ছন্দ, তাই UI বাংলা-প্রথম (bilingual bn/en সাপোর্ট থাকবে ভবিষ্যতে)।

## ব্যবহারকারী সম্পর্কে

প্রজেক্টের মালিক (Shahariar) একজন ব্যাংক কর্মকর্তা (Agrani Bank), প্রোগ্রামিং শিখছেন, এবং "FutureTech.ai" নামে একটা AI প্রোডাক্ট স্টুডিও চালানোর চেষ্টা করছেন যেখানে এটার মতো একাধিক অ্যাপ প্ল্যান করা আছে। **তিনি বাংলায় কথা বলেন — সব রেসপন্স বাংলায় দাও, প্রয়োজনে টেকনিক্যাল টার্ম ইংরেজিতে রাখতে পারো।** কোড/কমেন্ট ইংরেজি ভেরিয়েবল নাম + বাংলা কমেন্ট মিক্স স্টাইলে লেখা — এই কনভেনশন বজায় রাখো।

## টেক স্ট্যাক

- **Backend:** FastAPI (Python) + SQLAlchemy + SQLite (dev; প্রোডাকশনে PostgreSQL migrate করা যাবে)
- **AI:** Anthropic Claude API (`claude-sonnet-4-6` মডেল, `backend/main.py`-তে ব্যবহৃত)
- **Frontend:** Flutter (Dart), Material 3
- **Notification:** Firebase Cloud Messaging
- **PDF export:** `pdf` + `printing` প্যাকেজ (Flutter সাইডে)

## ফোল্ডার স্ট্রাকচার

```
chakri-ai/
├── backend/
│   ├── main.py                 FastAPI অ্যাপ এন্ট্রি, resume/cover-letter AI endpoints
│   ├── database.py             SQLAlchemy engine/session
│   ├── models.py               ORM models: Organization, JobCircular, Subject,
│   │                           ExamQuestion, StudyMaterial, DeviceToken
│   ├── schemas.py              Pydantic request/response স্কিমা
│   ├── scheduler.py            পর্যায়ক্রমিক scraper রান + push notification trigger
│   ├── routers/
│   │   ├── circulars.py        /api/circulars/*
│   │   ├── questions.py        /api/questions/*, /api/study/*
│   │   └── notifications.py    /api/notifications/*
│   ├── scrapers/
│   │   ├── base_scraper.py     সব scraper-এর abstract base class
│   │   └── site_scrapers.py    bdjobs/govt site scraper — ⚠️ CSS selector placeholder, কাজ করবে না as-is
│   └── notifications/
│       └── fcm_service.py      Firebase push notification পাঠানোর লজিক
└── mobile_app/
    └── lib/
        ├── main.dart                        Firebase init + app entry
        ├── models/                          resume, circular, question ডেটা মডেল
        ├── services/
        │   ├── api_service.dart             ব্যাকএন্ডের সব endpoint-এর জন্য HTTP wrapper
        │   └── notification_service.dart    FCM token রেজিস্ট্রেশন
        └── screens/
            ├── home_screen.dart              মেইন মেনু
            ├── resume_form_screen.dart        + resume_preview_screen.dart
            ├── circular_list_screen.dart      + circular_detail_screen.dart
            └── subject_list_screen.dart       + question_list_screen.dart
```

## বর্তমান অবস্থা (এই মুহূর্তে যা কাজ করছে)

✅ **সম্পূর্ণ ও টেস্ট করা (ব্যাকএন্ড, curl/python দিয়ে verify করা হয়েছে):**
- Resume generation ও cover letter generation (Claude API দিয়ে)
- Job Circular CRUD + list/search/filter API
- Question Bank CRUD + bulk import API
- Study Material list API
- Device token registration API

✅ **কোড লেখা হয়েছে কিন্তু আনটেস্টেড (Flutter SDK আগের sandbox-এ ছিল না):**
- সব Flutter screen — import path ও bracket balance ম্যানুয়ালি চেক করা হয়েছে, কিন্তু `flutter pub get` / `flutter analyze` / `flutter run` কখনো চালানো হয়নি
- **তোমার প্রথম কাজ হওয়া উচিত:** `mobile_app` এ `flutter pub get` চালিয়ে dependency resolve করা, `flutter analyze` দিয়ে টাইপো/এরর ধরা, এবং সম্ভব হলে emulator-এ রান করে দেখা

⚠️ **অসম্পূর্ণ / প্লেসহোল্ডার:**
- `backend/scrapers/site_scrapers.py` — CSS selector (`.job-title-link`, `.job-title-text` ইত্যাদি) placeholder মাত্র, আসল bdjobs.com/সরকারি সাইট HTML দেখে বসাতে হবে
- Firebase — `mobile_app`-এ `flutterfire configure` চালানো হয়নি, তাই `firebase_options.dart` নেই। এটা ছাড়া notification কাজ করবে না, কিন্তু `main.dart`-এ try/catch দিয়ে wrap করা আছে বলে বাকি অ্যাপ ক্র্যাশ করবে না
- Study Material দেখানোর Flutter স্ক্রিন এখনো লেখা হয়নি (API আছে, UI নেই)
- Cover Letter Generator-এর Flutter UI নেই (API আছে)

❌ **এখনো শুরুই হয়নি:**
- Mock Interview Coach
- Job Matching / Skill Gap Analysis
- বাস্তব প্রশ্ন-উত্তর ডেটা (এখন খালি ডেটাবেস, শুধু কাঠামো তৈরি)
- বাস্তব সার্কুলার ডেটা (scraper selector ঠিক না করা পর্যন্ত কিছু আসবে না)

## সেটআপ কমান্ড

**Backend:**
```bash
cd backend
pip install -r requirements.txt
cp .env.example .env   # তারপর ANTHROPIC_API_KEY বসাও
uvicorn main:app --reload
```

**Flutter:**
```bash
cd mobile_app
flutter pub get
flutter analyze        # প্রথমবার এটা চালিয়ে যা এরর আসে ঠিক করো
flutter run
```

`lib/services/api_service.dart`-এ `baseUrl = "http://10.0.2.2:8000"` — Android emulator-এর জন্য ঠিক আছে, রিয়েল ডিভাইসে টেস্ট করলে লোকাল IP-তে বদলাতে হবে।

## কাজ করার নিয়ম

1. **যেকোনো নতুন ফিচারের আগে প্রথমে ব্যাকএন্ড এন্ডপয়েন্ট বানাও, curl/httpie দিয়ে টেস্ট করে নিশ্চিত হও যে কাজ করছে, তারপর Flutter UI বানাও।** আগের সেশনে এই প্যাটার্নটাই অনুসরণ করা হয়েছে।
2. স্ক্র্যাপিং নিয়ে কাজ করার সময় প্রতিটা সাইটের robots.txt ও ToS চেক করে নিও — এটা আগে ব্যবহারকারীকে বলা হয়েছে।
3. `.env`, `firebase-service-account.json`, `*.db` — এসব কখনো কমিট কোরো না (`.gitignore`-এ আছে)।
4. নতুন Flutter dependency যোগ করলে `pubspec.yaml`-এ ভার্সন pin করে দাও, শুধু `any` লিখো না।
5. ডাটাবেস মডেল পরিবর্তন করলে মনে রেখো এখনো কোনো migration tool (Alembic) সেটআপ নেই — এখন পর্যন্ত `Base.metadata.create_all()` দিয়ে টেবিল বানানো হচ্ছে, যেটা schema change-এ existing DB আপডেট করে না। বড় স্কিমা পরিবর্তনের সময় এটা মাথায় রেখো (হয়ত Alembic যোগ করার সময় হয়ে গেছে)।

## পরবর্তী প্রায়োরিটি (রোডম্যাপ অনুযায়ী)

1. Flutter কোড `flutter analyze` দিয়ে verify ও ফিক্স করা
2. Study Material পড়ার স্ক্রিন বানানো
3. আসল bdjobs.com/সরকারি সাইট স্ক্র্যাপ করে selector ঠিক করা, বাস্তব ডেটা দিয়ে টেস্ট
4. Firebase প্রজেক্ট কানেক্ট করে নোটিফিকেশন এন্ড-টু-এন্ড টেস্ট করা
5. Cover Letter Generator UI
6. Mock Interview Coach (নতুন ফিচার)
