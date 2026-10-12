import 'dart:async';
import 'dart:convert';
import 'dart:io' show SocketException;
import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import '../models/resume_models.dart';
import '../models/circular_models.dart';
import '../models/question_models.dart';
import '../models/interview_models.dart';
import '../models/payment_models.dart';
import '../models/job_match_models.dart';

class ApiService {
  // ব্যাকএন্ড URL: --dart-define=API_BASE_URL=http://192.168.x.x:8000 দিয়ে override করা যায়
  // (রিয়েল ডিভাইস/প্রোডাকশন সার্ভারের জন্য)। না দিলে প্ল্যাটফর্ম অনুযায়ী ডিফল্ট:
  // Android emulator -> 10.0.2.2 (হোস্ট মেশিনের localhost), web/desktop -> localhost
  static const String _overrideUrl = String.fromEnvironment('API_BASE_URL');

  // প্রোডাকশন (release) বিল্ডে ডিফল্ট লাইভ URL; build-এর সময় --dart-define=API_BASE_URL=... দিয়ে বদলানো যায়।
  // ⚠️ Render deploy-এর পর আসল URL বসান (বা --dart-define দিন)। release-এ সবসময় https হতে হবে।
  static const String _productionUrl = 'https://chakri-ai-backend.onrender.com';

  static String get baseUrl {
    if (_overrideUrl.isNotEmpty) return _overrideUrl;
    if (kReleaseMode) return _productionUrl;
    if (!kIsWeb && defaultTargetPlatform == TargetPlatform.android) {
      return "http://10.0.2.2:8000";
    }
    return "http://localhost:8000";
  }

  /// সার্ভার ধীর সাড়া দিলে (Render free tier ঘুম থেকে জাগার সময়) true হয়; UI একটা বাংলা বার্তা দেখায়।
  static final ValueNotifier<bool> serverWaking = ValueNotifier<bool>(false);
  static int _pending = 0;
  static const _slowAfter = Duration(seconds: 5);
  static const _timeout = Duration(seconds: 60);
  static const _maxAttempts = 3;

  static Future<http.Response> _send(Future<http.Response> Function() call) async {
    _pending++;
    final slowTimer = Timer(_slowAfter, () => serverWaking.value = true);
    try {
      for (var attempt = 1;; attempt++) {
        try {
          return await call().timeout(_timeout);
        } on TimeoutException {
          if (attempt >= _maxAttempts) {
            throw Exception('সার্ভার সাড়া দিচ্ছে না। কিছুক্ষণ পর আবার চেষ্টা করুন।');
          }
        } on SocketException {
          if (attempt >= _maxAttempts) {
            throw Exception('ইন্টারনেট সংযোগ বা সার্ভারে সমস্যা হয়েছে। সংযোগ দেখে আবার চেষ্টা করুন।');
          }
          await Future.delayed(Duration(seconds: 3 * attempt));
        } on http.ClientException {
          if (attempt >= _maxAttempts) {
            throw Exception('সার্ভারে সংযোগ করা যায়নি। কিছুক্ষণ পর আবার চেষ্টা করুন।');
          }
          await Future.delayed(Duration(seconds: 3 * attempt));
        }
      }
    } finally {
      slowTimer.cancel();
      if (--_pending <= 0) {
        _pending = 0;
        serverWaking.value = false;
      }
    }
  }

  static Future<http.Response> _get(Uri uri) => _send(() => http.get(uri));

  static Future<http.Response> _post(Uri uri, {Map<String, String>? headers, Object? body}) =>
      _send(() => http.post(uri, headers: headers, body: body));

  Future<ResumeResult> generateResume(ResumeFormData data) async {
    final uri = Uri.parse("$baseUrl/api/resume/generate");
    final response = await _post(
      uri,
      headers: {"Content-Type": "application/json; charset=UTF-8"},
      body: jsonEncode(data.toJson()),
    );

    if (response.statusCode == 200) {
      final decoded = jsonDecode(utf8.decode(response.bodyBytes));
      return ResumeResult.fromJson(decoded);
    } else {
      final err = jsonDecode(utf8.decode(response.bodyBytes));
      throw Exception(err['detail'] ?? 'রিজিউম তৈরি করতে সমস্যা হয়েছে');
    }
  }

  Future<String> generateCoverLetter({
    required String resumeSummary,
    required String jobDescription,
    required String companyName,
    required String targetPosition,
    String language = "bn",
  }) async {
    final uri = Uri.parse("$baseUrl/api/cover-letter/generate");
    final response = await _post(
      uri,
      headers: {"Content-Type": "application/json; charset=UTF-8"},
      body: jsonEncode({
        "resume_summary": resumeSummary,
        "job_description": jobDescription,
        "company_name": companyName,
        "target_position": targetPosition,
        "language": language,
      }),
    );

    if (response.statusCode == 200) {
      final decoded = jsonDecode(utf8.decode(response.bodyBytes));
      return decoded['cover_letter'];
    } else {
      final err = jsonDecode(utf8.decode(response.bodyBytes));
      throw Exception(err['detail'] ?? 'কভার লেটার তৈরি করতে সমস্যা হয়েছে');
    }
  }

  /// রিজিউম টেক্সট -> PDF bytes। PDF ব্যাকএন্ডে বানানো হয়, কারণ Flutter-এর pdf প্যাকেজ
  /// বাংলা যুক্তাক্ষর/কার shape করতে পারে না (backend/pdf_export.py দেখুন)।
  Future<Uint8List> exportResumePdf(String text) async {
    final uri = Uri.parse("$baseUrl/api/resume/pdf");
    final response = await _post(
      uri,
      headers: {"Content-Type": "application/json; charset=UTF-8"},
      body: jsonEncode({"text": text}),
    );

    if (response.statusCode == 200) {
      return response.bodyBytes;
    } else {
      throw Exception('PDF তৈরি করতে সমস্যা হয়েছে (${response.statusCode})');
    }
  }

  // ---------------- Mock Interview ----------------

  /// history-তে শুধু উত্তর দেওয়া প্রশ্নগুলো পাঠাতে হবে। খালি history = প্রথম প্রশ্ন।
  Future<InterviewTurnResult> interviewTurn(InterviewSetup setup, List<InterviewTurn> history) async {
    final uri = Uri.parse("$baseUrl/api/interview/turn");
    final response = await _post(
      uri,
      headers: {"Content-Type": "application/json; charset=UTF-8"},
      body: jsonEncode({
        ...setup.toJson(),
        "history": [
          for (final t in history) {"question": t.question, "answer": t.answer},
        ],
      }),
    );

    final decoded = jsonDecode(utf8.decode(response.bodyBytes));
    if (response.statusCode == 200) {
      return InterviewTurnResult.fromJson(decoded);
    } else {
      throw Exception(decoded['detail'] ?? 'ইন্টারভিউ প্রশ্ন আনতে সমস্যা হয়েছে');
    }
  }

  // ---------------- Job Matching / Skill Gap ----------------

  /// circularId অথবা jobDescription — যেকোনো একটা দিতে হবে
  Future<JobMatchAnalysis> analyzeJobMatch(
    CandidateProfile profile, {
    int? circularId,
    String? jobDescription,
    String language = "bn",
  }) async {
    final response = await _post(
      Uri.parse("$baseUrl/api/job-match/analyze"),
      headers: {"Content-Type": "application/json; charset=UTF-8"},
      body: jsonEncode({
        ...profile.toJson(),
        "language": language,
        if (circularId != null) "circular_id": circularId,
        if (jobDescription != null && jobDescription.isNotEmpty) "job_description": jobDescription,
      }),
    );
    final decoded = jsonDecode(utf8.decode(response.bodyBytes));
    if (response.statusCode == 200) return JobMatchAnalysis.fromJson(decoded);
    throw Exception(_detail(decoded) ?? 'বিশ্লেষণ করতে সমস্যা হয়েছে');
  }

  Future<RecommendResult> recommendJobs(CandidateProfile profile, {int limit = 5, String language = "bn"}) async {
    final response = await _post(
      Uri.parse("$baseUrl/api/job-match/recommend"),
      headers: {"Content-Type": "application/json; charset=UTF-8"},
      body: jsonEncode({...profile.toJson(), "limit": limit, "language": language}),
    );
    final decoded = jsonDecode(utf8.decode(response.bodyBytes));
    if (response.statusCode == 200) return RecommendResult.fromJson(decoded);
    throw Exception(_detail(decoded) ?? 'চাকরির সাজেশন আনতে সমস্যা হয়েছে');
  }

  /// FastAPI-র detail কখনো string (HTTPException), কখনো list (422 validation) — দুটোই সামলানো
  static String? _detail(dynamic decoded) {
    final d = decoded is Map ? decoded['detail'] : null;
    if (d is String) return d;
    if (d is List && d.isNotEmpty && d.first is Map) {
      return (d.first['msg'] as String?)?.replaceFirst('Value error, ', '');
    }
    return null;
  }

  // ---------------- Premium / Payments ----------------

  Future<PlansInfo> getPlans() async {
    final response = await _get(Uri.parse("$baseUrl/api/payments/plans"));
    if (response.statusCode == 200) {
      return PlansInfo.fromJson(jsonDecode(utf8.decode(response.bodyBytes)));
    }
    throw Exception('প্ল্যান লোড করতে সমস্যা হয়েছে');
  }

  Future<SubscriptionStatus> getSubscriptionStatus(String subscriberId) async {
    final response = await _get(Uri.parse("$baseUrl/api/payments/status/$subscriberId"));
    if (response.statusCode == 200) {
      return SubscriptionStatus.fromJson(jsonDecode(utf8.decode(response.bodyBytes)));
    }
    throw Exception('সাবস্ক্রিপশন স্ট্যাটাস লোড করতে সমস্যা হয়েছে');
  }

  Future<PaymentCreated> createPayment({
    required String subscriberId,
    required String planCode,
    required String provider,
  }) async {
    final response = await _post(
      Uri.parse("$baseUrl/api/payments/create"),
      headers: {"Content-Type": "application/json; charset=UTF-8"},
      body: jsonEncode({"subscriber_id": subscriberId, "plan_code": planCode, "provider": provider}),
    );
    final decoded = jsonDecode(utf8.decode(response.bodyBytes));
    if (response.statusCode == 200) return PaymentCreated.fromJson(decoded);
    throw Exception(decoded['detail'] ?? 'পেমেন্ট শুরু করতে সমস্যা হয়েছে');
  }

  Future<PaymentInfo> getPayment(int paymentId, String subscriberId) async {
    final uri = Uri.parse("$baseUrl/api/payments/$paymentId")
        .replace(queryParameters: {"subscriber_id": subscriberId});
    final response = await _get(uri);
    if (response.statusCode == 200) {
      return PaymentInfo.fromJson(jsonDecode(utf8.decode(response.bodyBytes)));
    }
    throw Exception('পেমেন্ট স্ট্যাটাস লোড করতে সমস্যা হয়েছে');
  }

  // ---------------- Job Circulars ----------------

  Future<List<JobCircular>> getCirculars({
    String? category,
    String? search,
    int skip = 0,
    int limit = 30,
  }) async {
    final params = <String, String>{
      'skip': '$skip',
      'limit': '$limit',
      if (category != null) 'category': category,
      if (search != null && search.isNotEmpty) 'search': search,
    };
    final uri = Uri.parse("$baseUrl/api/circulars/").replace(queryParameters: params);
    final response = await _get(uri);

    if (response.statusCode == 200) {
      final List decoded = jsonDecode(utf8.decode(response.bodyBytes));
      return decoded.map((e) => JobCircular.fromJson(e)).toList();
    }
    throw Exception('সার্কুলার লোড করতে সমস্যা হয়েছে');
  }

  Future<JobCircular> getCircularDetail(int id) async {
    final uri = Uri.parse("$baseUrl/api/circulars/$id");
    final response = await _get(uri);
    if (response.statusCode == 200) {
      return JobCircular.fromJson(jsonDecode(utf8.decode(response.bodyBytes)));
    }
    throw Exception('সার্কুলার বিস্তারিত লোড করতে সমস্যা হয়েছে');
  }

  Future<List<String>> getCircularCategories() async {
    final uri = Uri.parse("$baseUrl/api/circulars/categories/list");
    final response = await _get(uri);
    if (response.statusCode == 200) {
      final List decoded = jsonDecode(utf8.decode(response.bodyBytes));
      return decoded.cast<String>();
    }
    return [];
  }

  // ---------------- Question Bank ----------------

  Future<List<Subject>> getSubjects() async {
    final uri = Uri.parse("$baseUrl/api/questions/subjects");
    final response = await _get(uri);
    if (response.statusCode == 200) {
      final List decoded = jsonDecode(utf8.decode(response.bodyBytes));
      return decoded.map((e) => Subject.fromJson(e)).toList();
    }
    throw Exception('বিষয় লোড করতে সমস্যা হয়েছে');
  }

  Future<List<ExamQuestion>> getQuestions({
    int? subjectId,
    int? examYear,
    int skip = 0,
    int limit = 30,
  }) async {
    final params = <String, String>{
      'skip': '$skip',
      'limit': '$limit',
      if (subjectId != null) 'subject_id': '$subjectId',
      if (examYear != null) 'exam_year': '$examYear',
    };
    final uri = Uri.parse("$baseUrl/api/questions/").replace(queryParameters: params);
    final response = await _get(uri);
    if (response.statusCode == 200) {
      final List decoded = jsonDecode(utf8.decode(response.bodyBytes));
      return decoded.map((e) => ExamQuestion.fromJson(e)).toList();
    }
    throw Exception('প্রশ্ন লোড করতে সমস্যা হয়েছে');
  }

  Future<List<StudyMaterial>> getStudyMaterials({int? subjectId}) async {
    final params = <String, String>{
      if (subjectId != null) 'subject_id': '$subjectId',
    };
    final uri = Uri.parse("$baseUrl/api/study/").replace(queryParameters: params);
    final response = await _get(uri);
    if (response.statusCode == 200) {
      final List decoded = jsonDecode(utf8.decode(response.bodyBytes));
      return decoded.map((e) => StudyMaterial.fromJson(e)).toList();
    }
    throw Exception('স্টাডি ম্যাটেরিয়াল লোড করতে সমস্যা হয়েছে');
  }

  // ---------------- Notifications ----------------

  Future<void> registerDevice({
    required String token,
    String platform = "android",
    String? preferredCategories,
  }) async {
    final uri = Uri.parse("$baseUrl/api/notifications/register-device");
    await _post(
      uri,
      headers: {"Content-Type": "application/json; charset=UTF-8"},
      body: jsonEncode({
        "token": token,
        "platform": platform,
        "preferred_categories": preferredCategories,
      }),
    );
  }
}
