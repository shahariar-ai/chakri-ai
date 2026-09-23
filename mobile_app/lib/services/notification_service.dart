import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:flutter/foundation.dart';
import 'api_service.dart';

/// ব্যাকগ্রাউন্ডে মেসেজ আসলে এই ফাংশন কল হয়।
/// অবশ্যই top-level (ক্লাসের বাইরে) ফাংশন হতে হবে - Flutter এর নিয়ম।
@pragma('vm:entry-point')
Future<void> firebaseMessagingBackgroundHandler(RemoteMessage message) async {
  debugPrint("ব্যাকগ্রাউন্ড নোটিফিকেশন পাওয়া গেছে: ${message.notification?.title}");
}

class NotificationService {
  final _firebaseMessaging = FirebaseMessaging.instance;
  final _api = ApiService();

  /// অ্যাপ চালু হওয়ার সময় একবার কল করতে হবে (main.dart থেকে)
  Future<void> init({String? preferredCategories}) async {
    // ইউজারের কাছে পারমিশন চাওয়া
    final settings = await _firebaseMessaging.requestPermission(
      alert: true,
      badge: true,
      sound: true,
    );

    if (settings.authorizationStatus == AuthorizationStatus.denied) {
      debugPrint("ব্যবহারকারী নোটিফিকেশন পারমিশন দেননি");
      return;
    }

    // ডিভাইস টোকেন নিয়ে ব্যাকএন্ডে রেজিস্টার করা
    final token = await _firebaseMessaging.getToken();
    if (token != null) {
      await _registerToken(token, preferredCategories);
    }

    // টোকেন রিফ্রেশ হলে আবার রেজিস্টার করা
    _firebaseMessaging.onTokenRefresh.listen((newToken) {
      _registerToken(newToken, preferredCategories);
    });

    // অ্যাপ চালু থাকা অবস্থায় (foreground) নোটিফিকেশন আসলে
    FirebaseMessaging.onMessage.listen((RemoteMessage message) {
      debugPrint("ফোরগ্রাউন্ডে নোটিফিকেশন: ${message.notification?.title}");
      // TODO: এখানে চাইলে in-app banner/snackbar দেখাতে পারেন
    });

    // ইউজার নোটিফিকেশনে ট্যাপ করে অ্যাপ খুললে
    FirebaseMessaging.onMessageOpenedApp.listen((RemoteMessage message) {
      final circularId = message.data['circular_id'];
      debugPrint("নোটিফিকেশনে ট্যাপ করা হয়েছে, circular_id: $circularId");
      // TODO: circularId থাকলে সরাসরি CircularDetailScreen এ নেভিগেট করানো যায়
      // (এর জন্য একটা global navigatorKey সেটআপ করতে হবে main.dart এ)
    });
  }

  Future<void> _registerToken(String token, String? preferredCategories) async {
    try {
      await _api.registerDevice(token: token, preferredCategories: preferredCategories);
      debugPrint("ডিভাইস টোকেন রেজিস্টার সফল হয়েছে");
    } catch (e) {
      debugPrint("ডিভাইস টোকেন রেজিস্টার করতে ব্যর্থ: $e");
    }
  }
}
