# Data Safety ও Content Rating — উত্তরের খসড়া

> প্রথম release (Firebase ছাড়া, PAYMENTS_ENABLED=false) ধরে লেখা। Firebase/payments চালু করলে হালনাগাদ করতে হবে। Play Console-এর আসল প্রশ্ন বদলাতে পারে — মিলিয়ে নিন।

## Data Safety

**Does your app collect or share any of the required user data types?** → Yes
**Is all of the user data collected by your app encrypted in transit?** → Yes (HTTPS)
**Do you provide a way for users to request that their data be deleted?** → Yes — ইমেইল shahriar.sharif406@gmail.com (privacy policy ৪ নং ধারা)

| Data type | Collected | Shared | Purpose | Optional? |
|---|---|---|---|---|
| Personal info → Name, Email, Phone, Address (রিজিউম/কভার লেটার ফর্মে ইউজার যা লেখে) | Yes (প্রক্রিয়া হয়, সার্ভারে সংরক্ষণ হয় না) | **Yes** — Anthropic (Claude API), service provider হিসেবে | App functionality | Yes (ইউজার ইচ্ছামতো দেয়) |
| Other user-generated content / Messages (ইন্টারভিউ উত্তর, জব ডেসক্রিপশন, স্কিল) | Yes | Yes — Anthropic | App functionality | Yes |
| App activity / Device or other IDs → Device token (FCM) | Yes — **শুধু Firebase চালু হলে** | Yes — Google Firebase | App functionality (notifications) | Yes |
| Financial info → Purchase history | **No** (payments বন্ধ; চালু করলে Yes) | — | — | — |
| Location, Contacts, Photos, Files, Health, Audio | No | — | — | — |

নোট:
- Anthropic/Firebase/Render-কে "service provider" হিসেবে গণ্য করলে Play-র "sharing" সংজ্ঞায় ব্যতিক্রম প্রযোজ্য হতে পারে (data processed on behalf of developer); নিশ্চিত না হলে নিরাপদ দিক = "shared"-এ চিহ্ন দিন।
- রিজিউম ডেটা Claude API-তে যায় — এটা privacy policy-তে উল্লেখ আছে, Data Safety-তেও আছে।
- Data is not sold; no ads; no data used for advertising.
- অ্যাপ লোকালি ফোনে সংরক্ষণ করে: সাবস্ক্রাইবার আইডি, জব ম্যাচিং প্রোফাইল।

## অন্যান্য App content ঘোষণা
- Target audience: **18+** (বা 13+; শিশুদের জন্য নয়) — Designed for Families নয়
- Ads: No
- Government app: No (সরকারি নয়; সার্কুলার সংগ্রহ করে মাত্র — বর্ণনায় উল্লেখ আছে)
- Financial features: No
- Health: No
- News app: No
- Generative AI: অ্যাপে AI-তৈরি কনটেন্ট আছে — Play-র AI-Generated Content policy অনুযায়ী ইউজারকে ভুল রিপোর্ট করার উপায় লাগে (প্রশ্নব্যাংকে "ভুল জানান" বাটন আছে) এবং আপত্তিকর কনটেন্ট ঠেকানোর ব্যবস্থা। Claude-এর নিজস্ব নিরাপত্তা ফিল্টার আছে।

## Content Rating (IARC প্রশ্নমালা) — প্রত্যাশিত উত্তর
- Category: **Utility / Productivity / Reference** (Game নয়)
- Violence, Blood, Sexual content, Nudity: **No**
- Profanity / Crude humor: **No**
- Drugs, alcohol, tobacco: **No**
- Gambling / simulated gambling: **No**
- User-generated content shared with other users / user interaction / chat between users: **No** (ইউজার শুধু নিজের জন্য কনটেন্ট বানায়; কারো সাথে শেয়ার হয় না)
- Shares user location: **No**
- Digital purchases: **No** (প্রথম release)
- Unrestricted internet access/web browsing: **No** (শুধু নির্দিষ্ট লিংক ব্রাউজারে খোলে)
- প্রত্যাশিত ফল: IARC 3+ / Everyone। (AI chatbot-ধর্মী মক ইন্টারভিউ থাকায় প্রশ্নমালায় AI/generated content-সংক্রান্ত প্রশ্ন এলে "Yes, শুধু ব্যক্তিগত ব্যবহার" ধরনের উত্তর দিন।)
