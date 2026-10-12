# Privacy Policy GitHub Pages-এ হোস্ট করার ধাপ

Play Store-এ privacy policy-র একটা **সর্বজনীন URL** লাগে। (ফাইলগুলো আইনি খসড়া — সম্ভব হলে একজন আইনজীবীকে দেখিয়ে নিন।)

**সবচেয়ে নিরাপদ উপায়: শুধু আইনি পাতার জন্য আলাদা ছোট পাবলিক repo**

1. GitHub-এ নতুন **Public** repo বানান, নাম যেমন `chakri-ai-legal`। (ফ্রি অ্যাকাউন্টে GitHub Pages শুধু পাবলিক repo-তে চলে। মূল `chakri-ai` repo-কে পাবলিক না করাই ভালো।)
2. `store_listing/privacy_policy.html`, `terms.html`, `refund_policy.html` ফাইল ৩টা ওই repo-র root-এ আপলোড করুন (GitHub ওয়েবসাইটে "Add file → Upload files" দিয়ে)।
3. repo-র **Settings → Pages → Source: Deploy from a branch** → Branch: `main`, Folder: `/ (root)` → Save।
4. ১-২ মিনিট পর URL:
   `https://<আপনার-ইউজারনেম>.github.io/chakri-ai-legal/privacy_policy.html`
5. লিংকটা ব্রাউজারে খুলে দেখুন বাংলা ঠিকমতো দেখায় কিনা, এবং ইংরেজি/বাংলা বাটন কাজ করে কিনা।
6. এই URL Play Console → App content → **Privacy policy**-তে বসান। Data Safety ফর্মে "delete data" URL চাইলে একই পাতা দিন (৪ নং ধারায় মোছার নিয়ম আছে)।

**বিকল্প:** মূল repo পাবলিক করলে ফাইলগুলো `docs/` ফোল্ডারে রেখে Pages-এ Folder `/docs` সিলেক্ট করুন। তার আগে নিশ্চিত হোন repo-তে কোনো secret নেই।
