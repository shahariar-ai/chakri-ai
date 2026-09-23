import 'dart:math';
import 'package:shared_preferences/shared_preferences.dart';

/// এখনো user login নেই, তাই প্রথমবার অ্যাপ চালু হলে একটা random ID বানিয়ে ডিভাইসে রাখা হয়।
/// প্রিমিয়াম সাবস্ক্রিপশন এই ID-র সাথে যুক্ত থাকে।
/// ⚠️ অ্যাপ আনইনস্টল/ডেটা ক্লিয়ার করলে ID হারিয়ে যাবে — login সিস্টেম এলে সেখানে migrate করতে হবে।
class SubscriberId {
  static const _key = 'subscriber_id';

  static Future<String> get() async {
    final prefs = await SharedPreferences.getInstance();
    final existing = prefs.getString(_key);
    if (existing != null) return existing;

    final rand = Random.secure();
    final id = List.generate(16, (_) => rand.nextInt(256).toRadixString(16).padLeft(2, '0')).join();
    await prefs.setString(_key, id);
    return id;
  }
}
