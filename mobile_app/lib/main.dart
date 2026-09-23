import 'package:flutter/material.dart';
import 'package:flutter/foundation.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_messaging/firebase_messaging.dart';
import 'screens/home_screen.dart';
import 'services/notification_service.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // ⚠️ Firebase চালু করার আগে flutterfire configure চালিয়ে
  // firebase_options.dart জেনারেট করতে হবে (README দেখুন)।
  //ততক্ষণ নিচের অংশ কমেন্ট করা থাকলেও বাকি অ্যাপ ঠিকমতো চলবে।
  // firebase_messaging শুধু Android/iOS-এ কাজ করে — Windows/web-এ push notification নেই,
  // তাই ডেস্কটপে Firebase init পুরোপুরি স্কিপ করা হয়।
  final supportsPush = !kIsWeb &&
      (defaultTargetPlatform == TargetPlatform.android || defaultTargetPlatform == TargetPlatform.iOS);
  if (supportsPush) {
    try {
      await Firebase.initializeApp();
      FirebaseMessaging.onBackgroundMessage(firebaseMessagingBackgroundHandler);
      await NotificationService().init();
    } catch (e) {
      debugPrint("Firebase init স্কিপ করা হলো (এখনো সেটআপ করা হয়নি): $e");
    }
  }

  runApp(const ChakriAiApp());
}

class ChakriAiApp extends StatelessWidget {
  const ChakriAiApp({super.key});

  @override
  Widget build(BuildContext context) {
    const seedColor = Color(0xFF0F6E5C); // গাঢ় সবুজ - বিশ্বাসযোগ্যতা ও পেশাদারিত্ব বোঝায়

    return MaterialApp(
      title: 'চাকরি AI',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: seedColor),
        useMaterial3: true,
        textTheme: GoogleFonts.hindSiliguriTextTheme(),
        scaffoldBackgroundColor: const Color(0xFFF7F8FA),
        appBarTheme: const AppBarTheme(
          centerTitle: true,
          elevation: 0,
          backgroundColor: Colors.transparent,
          foregroundColor: Colors.black87,
        ),
      ),
      home: const HomeScreen(),
    );
  }
}
