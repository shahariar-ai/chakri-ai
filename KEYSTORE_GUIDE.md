# Release Keystore গাইড

## ১. keystore বানান (একবারই, নিজে করুন)
PowerShell/CMD-তে (keytool JDK/Android Studio-র সাথে আসে):

```
mkdir C:\Users\LAPTOP\keys
keytool -genkeypair -v -storetype JKS -keystore C:\Users\LAPTOP\keys\chakri-ai-upload.jks -alias upload -keyalg RSA -keysize 2048 -validity 10000
```
password ও নাম/সংস্থা জিজ্ঞেস করবে। **password ও .jks ফাইলের একাধিক ব্যাকআপ রাখুন (প্রজেক্ট ফোল্ডারের বাইরে)।** হারালে আপডেট দেওয়া কঠিন হবে (Play App Signing থাকলে upload key reset করা যায়)।

keytool না পেলে: `"C:\Program Files\Android\Android Studio\jbr\bin\keytool.exe"` দিয়ে চালান।

## ২. key.properties
`mobile_app/android/key.properties.example` কপি করে `key.properties` নাম দিন, আসল password ও পথ বসান। এটা `.gitignore`-এ আছে — কমিট হবে না।

## ৩. Build
```
cd mobile_app
flutter build appbundle --release --dart-define=API_BASE_URL=https://<আপনার-render-url> 
```
আউটপুট: `build/app/outputs/bundle/release/app-release.aab`। এটা Play Console-এ আপলোড করুন (Play App Signing চালু রাখুন)।

key.properties না থাকলে build debug key দিয়ে sign হয় — Play Store এটা গ্রহণ করবে না।
