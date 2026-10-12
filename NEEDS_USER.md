# NEEDS_USER (আপনার সিদ্ধান্ত/তথ্য লাগবে)

1. **GitHub remote:** repo-তে কোনো `origin` নেই। GitHub-এ খালি repo বানিয়ে URL দিন, তারপর:
   `git remote add origin <URL>` এবং `git push -u origin main`
   (আমি কিছু বানাতে পারি না কারণ authentication আপনার হাতে।)

2. **Firebase (push notification):** আপনাকে দিতে হবে/করতে হবে:
   - Firebase Console-এ প্রজেক্ট বানান (Project ID আমাকে জানান)
   - Android app যোগ করুন, package name হুবহু: `com.futuretechai.chakriai`
   - `google-services.json` ডাউনলোড করে `mobile_app/android/app/`-এ রাখুন (gitignore করা উচিত; আমি google-services gradle plugin ও `flutterfire configure` তখন সেট করব)
   - Service account JSON (Project settings → Service accounts) ডাউনলোড করে `backend/firebase-service-account.json` বা Render env-এ দিন
   - release keystore-এর SHA-1/SHA-256 Firebase-এ যোগ করুন (KEYSTORE_GUIDE.md দেখে keystore বানানোর পর)
   Firebase ছাড়াই অ্যাপ চলে, শুধু notification কাজ করবে না।

3. **Render URL:** Render deploy-এর পর আসল URL জানান। এখন `api_service.dart`-এ `https://chakri-ai-backend.onrender.com` অনুমান করে বসানো (বা build-এ `--dart-define=API_BASE_URL=...`)।
