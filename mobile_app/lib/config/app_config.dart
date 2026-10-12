/// build-সময় ফিচার ফ্ল্যাগ। উদাহরণ: flutter build appbundle --dart-define=PAYMENTS_ENABLED=true
class AppConfig {
  /// প্রিমিয়াম/পেমেন্ট স্ক্রিন। ডিফল্ট false — প্রথম release-এ সব ফিচার ফ্রি টায়ারে।
  /// (Google Play-তে অ্যাপের ভেতরে ডিজিটাল সাবস্ক্রিপশনে Play Billing বাধ্যতামূলক হতে পারে; PROGRESS.md দেখুন)
  static const bool paymentsEnabled = bool.fromEnvironment('PAYMENTS_ENABLED', defaultValue: false);
}
