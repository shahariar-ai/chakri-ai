# Screenshots, Feature Graphic ও Closed Testing

## Screenshot তালিকা (Phone: ন্যূনতম ২টা, প্রস্তাবিত ৬-৮টা)
স্পেক: PNG/JPEG, প্রতিটি ≤ ৮ MB, 16:9 বা 9:16, দুই বাহুর মাপ ৩২০–৩৮৪০ px। প্রস্তাবিত: 1080×1920।
১. হোম স্ক্রিন (ফিচার মেনু)
২. রিজিউম ফর্ম
৩. রিজিউম প্রিভিউ/PDF
৪. কভার লেটার ফলাফল
৫. মক ইন্টারভিউ (প্রশ্ন + ফিডব্যাক)
৬. জব ম্যাচিং সাজেশন / স্কিল গ্যাপ স্কোর
৭. সার্কুলার তালিকা (সোর্স নোটসহ)
৮. প্রশ্নব্যাংক (উত্তর খোলা অবস্থায়)
- নিজের ফোনে বা emulator-এ অ্যাপ চালিয়ে নিন (`flutter run --release --dart-define=API_BASE_URL=<live url>`), ব্যক্তিগত তথ্য ছাড়া নমুনা ডেটা দিন।
- 7-inch/10-inch tablet screenshot ঐচ্ছিক (বড় স্ক্রিনে প্রদর্শনের জন্য প্রস্তাবিত)।

## অ্যাপ আইকন (Play Console-এ)
512×512 PNG, ≤ 1 MB। `mobile_app/assets/icon/icon.png` (1024×1024) ছোট করে (যেমন Paint/ইমেজ টুল) আপলোড করুন; Play নিজে কোণ গোল করে।

## Feature Graphic (১০২৪×৫০০ px, PNG/JPEG, ≤ ১৫ MB) বানানোর নির্দেশ
Canva (বিনামূল্যে) → Custom size 1024×500 px:
1. ব্যাকগ্রাউন্ড: গাঢ় সবুজ `#0F6E5C` থেকে নীল `#1565C0` গ্রেডিয়েন্ট।
2. বাঁ দিকে অ্যাপ আইকন (≈২৫০px), পাশে বড় সাদা লেখা: **চাকরি AI**, নিচে ছোট: "রিজিউম • ইন্টারভিউ • সার্কুলার • প্রশ্নব্যাংক"।
3. ডান দিকে ২টা ফোনের মকআপে দুটো screenshot (হোম ও ইন্টারভিউ)।
4. গুরুত্বপূর্ণ লেখা মাঝখানের ৮০% এলাকায় রাখুন (প্রান্তে কাটা পড়তে পারে); ফন্ট Hind Siliguri/Noto Sans Bengali (পড়া সহজ)।
5. ভুয়া র‍্যাঙ্কিং/"#1"/ডাউনলোড সংখ্যা/সরকারি লোগো ব্যবহার করবেন না (Play নীতি লঙ্ঘন)।
6. PNG হিসেবে এক্সপোর্ট → Play Console → Store listing → Feature graphic।

## নতুন personal developer account-এর Closed Testing শর্ত (web search দিয়ে যাচাই, ২০২৬-১০-১২)
- Google-এর Play Console Help অনুযায়ী (২০২৩-১১-১৩-র পর খোলা **personal** account): production-এ যাওয়ার আগে closed test-এ **কমপক্ষে ১২ জন tester একটানা ১৪ দিন opt-in** থাকতে হবে, তারপর Dashboard-এ "Apply for production access" করতে হয়। তার আগে Production track বন্ধ থাকে। (আগে ২০ জন লাগত; ১২-তে নামানো হয়েছে।)
- Organization account এই শর্ত থেকে মুক্ত (তবে organization account-এর জন্য D-U-N-S নম্বর/যাচাই লাগে)।
- সতর্কতা: tester opt-in ছেড়ে দিলে গণনা নেমে যেতে পারে — ১২-র বেশি (১৫-২০ জন) tester রাখুন; শুধু invite পাঠানো যথেষ্ট নয়, তাদের opt-in করে অ্যাপ ইনস্টল করতে হবে।
- সূত্র: [Play Console Help — testing requirements](https://support.google.com/googleplay/android-developer/answer/14151465?hl=en-GB)। নিয়ম বদলাতে পারে, আপলোডের সময় Console-এর বার্তা দেখুন।
- ব্যবহারিক পরামর্শ: Play Console-এ Testing → Closed testing → Alpha track বানিয়ে tester-দের Google Group বা ইমেইল তালিকা যোগ করুন; ১৪ দিন পর feedback নিয়ে আবেদন করুন; আবেদনে অ্যাপ কীভাবে পরীক্ষা হয়েছে লিখতে হয়।
- Target API: নতুন অ্যাপ/আপডেটে **API 36** লাগে (আমরা সেট করেছি)।
