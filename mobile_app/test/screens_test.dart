import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

import 'package:chakri_ai/models/question_models.dart';
import 'package:chakri_ai/screens/cover_letter_screen.dart';
import 'package:chakri_ai/screens/home_screen.dart';
import 'package:chakri_ai/screens/mock_interview_screen.dart';
import 'package:chakri_ai/screens/premium_screen.dart';
import 'package:chakri_ai/screens/question_list_screen.dart';
import 'package:chakri_ai/screens/study_material_detail_screen.dart';
import 'package:chakri_ai/screens/subject_list_screen.dart';

// ApiService সরাসরি http.get/post ব্যবহার করে, তাই http.runWithClient দিয়ে
// MockClient ঢুকিয়ে ব্যাকএন্ড ছাড়াই স্ক্রিনগুলো টেস্ট করা হয়।
http.Response _json(Object body, [int status = 200]) => http.Response.bytes(
      utf8.encode(jsonEncode(body)),
      status,
      headers: {'content-type': 'application/json; charset=utf-8'},
    );

Map<String, dynamic> _question(int id) => {
      'id': id,
      'subject_id': 5,
      'question_text': 'প্রশ্ন $id',
      'option_a': 'ক',
      'option_b': 'খ',
      'option_c': 'গ',
      'option_d': 'ঘ',
      'correct_answer': 'A',
      'explanation': 'ব্যাখ্যা $id',
      'difficulty': 'medium',
    };

Widget _wrap(Widget child) => MaterialApp(home: child);

// QuestionListScreen-এ TabBarView (PageView) + ListView দুটোই Scrollable,
// তাই scrollUntilVisible-কে বলে দিতে হয় কোনটা স্ক্রল করবে।
final _listScrollable =
    find.descendant(of: find.byType(ListView), matching: find.byType(Scrollable)).first;

void main() {
  testWidgets('হোম স্ক্রিনে কভার লেটার এখন চালু (শীঘ্রই আসছে নয়)', (tester) async {
    await tester.pumpWidget(_wrap(const HomeScreen()));
    await tester.tap(find.text('কভার লেটার জেনারেটর'));
    await tester.pumpAndSettle();
    expect(find.byType(CoverLetterScreen), findsOneWidget);
  });

  testWidgets('সাবজেক্ট লিস্ট API থেকে লোড হয়, লম্বা নামেও আইকন মেলে', (tester) async {
    final client = MockClient((req) async {
      expect(req.url.path, '/api/questions/subjects');
      return _json([
        {'id': 7, 'name': 'বাংলা ব্যাকরণ ও সাহিত্য', 'description': null},
        {'id': 12, 'name': 'কম্পিউটার ও তথ্যপ্রযুক্তি', 'description': null},
      ]);
    });
    await http.runWithClient(() async {
      await tester.pumpWidget(_wrap(const SubjectListScreen()));
      await tester.pumpAndSettle();
    }, () => client);

    expect(find.text('বাংলা ব্যাকরণ ও সাহিত্য'), findsOneWidget);
    expect(find.byIcon(Icons.menu_book_rounded), findsOneWidget);
    expect(find.byIcon(Icons.computer_rounded), findsOneWidget);
  });

  testWidgets('প্রশ্ন লিস্ট ৩০টার পর "আরো প্রশ্ন দেখুন" দিয়ে পরের পেজ আনে', (tester) async {
    final requestedSkips = <String?>[];
    final client = MockClient((req) async {
      if (req.url.path == '/api/questions/') {
        final skip = req.url.queryParameters['skip'];
        requestedSkips.add(skip);
        final start = int.parse(skip ?? '0');
        final count = start == 0 ? 30 : 5;
        return _json(List.generate(count, (i) => _question(start + i + 1)));
      }
      return _json([]); // study materials
    });

    await http.runWithClient(() async {
      await tester.pumpWidget(_wrap(QuestionListScreen(subject: Subject(id: 5, name: 'সাধারণ গণিত'))));
      await tester.pumpAndSettle();

      await tester.scrollUntilVisible(find.text('আরো প্রশ্ন দেখুন'), 500, scrollable: _listScrollable);
      await tester.tap(find.text('আরো প্রশ্ন দেখুন'));
      await tester.pumpAndSettle();
      await tester.scrollUntilVisible(find.textContaining('প্রশ্ন 35'), 500, scrollable: _listScrollable);
    }, () => client);

    expect(requestedSkips, ['0', '30']);
    expect(find.textContaining('প্রশ্ন 35'), findsOneWidget);
    // শেষ পেজে ৩০-এর কম এসেছে, তাই বাটন আর থাকবে না
    expect(find.text('আরো প্রশ্ন দেখুন'), findsNothing);
  });

  testWidgets('স্টাডি ম্যাটেরিয়াল কার্ডে ট্যাপ করলে ডিটেইল স্ক্রিন খোলে', (tester) async {
    final client = MockClient((req) async {
      if (req.url.path == '/api/study/') {
        return _json([
          {
            'id': 1,
            'subject_id': 5,
            'title': 'লসাগু ও গসাগু',
            'content': 'লসাগু (LCM) হলো সবচেয়ে ছোট সাধারণ গুণিতক। ' * 10,
            'topic_tags': 'গণিত, সংখ্যাতত্ত্ব',
          }
        ]);
      }
      return _json([]);
    });

    await http.runWithClient(() async {
      await tester.pumpWidget(_wrap(QuestionListScreen(subject: Subject(id: 5, name: 'সাধারণ গণিত'))));
      await tester.pumpAndSettle();
      await tester.tap(find.text('পড়ার উপকরণ'));
      await tester.pumpAndSettle();
      await tester.tap(find.text('লসাগু ও গসাগু'));
      await tester.pumpAndSettle();
    }, () => client);

    expect(find.byType(StudyMaterialDetailScreen), findsOneWidget);
    expect(find.text('সংখ্যাতত্ত্ব'), findsOneWidget);
  });

  testWidgets('কভার লেটার: খালি ফর্মে ভ্যালিডেশন, পূর্ণ ফর্মে API কল ও রেজাল্ট', (tester) async {
    // ডিফল্ট 800x600 টেস্ট স্ক্রিনে সাবমিট বাটন ListView-এর নিচে build-ই হয় না,
    // তাই ফোনের মতো লম্বা স্ক্রিন দেওয়া হলো।
    tester.view.physicalSize = const Size(800, 1600);
    tester.view.devicePixelRatio = 1.0;
    addTearDown(tester.view.reset);

    Map<String, dynamic>? sentBody;
    final client = MockClient((req) async {
      expect(req.url.path, '/api/cover-letter/generate');
      sentBody = jsonDecode(utf8.decode(req.bodyBytes));
      return _json({'cover_letter': 'বরাবর, নিয়োগ ব্যবস্থাপক'});
    });

    await http.runWithClient(() async {
      await tester.pumpWidget(_wrap(const CoverLetterScreen(
        initialCompany: 'ABC Bank',
        initialPosition: 'Officer',
      )));

      final submit = find.text('AI দিয়ে কভার লেটার তৈরি করুন');
      await tester.tap(submit);
      await tester.pump();
      expect(find.text('এই তথ্যটি দিতে হবে'), findsNWidgets(2)); // job desc + summary খালি
      expect(sentBody, isNull);

      await tester.enterText(find.widgetWithText(TextFormField, 'জব ডেসক্রিপশন / সার্কুলারের চাহিদা'), 'Excel জানতে হবে');
      await tester.enterText(find.widgetWithText(TextFormField, 'আপনার সংক্ষিপ্ত পরিচিতি'), 'BBA, ২ বছর অভিজ্ঞতা');
      await tester.tap(find.text('English'));
      await tester.tap(submit);
      await tester.pumpAndSettle();
    }, () => client);

    expect(sentBody, {
      'resume_summary': 'BBA, ২ বছর অভিজ্ঞতা',
      'job_description': 'Excel জানতে হবে',
      'company_name': 'ABC Bank',
      'target_position': 'Officer',
      'language': 'en',
    });
    expect(find.text('বরাবর, নিয়োগ ব্যবস্থাপক'), findsOneWidget);
    expect(find.text('কপি করুন'), findsOneWidget);
  });

  testWidgets('মক ইন্টারভিউ: সেটআপ -> ৩টা প্রশ্ন-উত্তর -> ফিডব্যাক ও সারাংশ', (tester) async {
    tester.view.physicalSize = const Size(800, 1600);
    tester.view.devicePixelRatio = 1.0;
    addTearDown(tester.view.reset);

    final sentHistoryLengths = <int>[];
    Map<String, dynamic>? firstBody;
    final client = MockClient((req) async {
      expect(req.url.path, '/api/interview/turn');
      final body = jsonDecode(utf8.decode(req.bodyBytes)) as Map<String, dynamic>;
      firstBody ??= body;
      final n = (body['history'] as List).length;
      sentHistoryLengths.add(n);
      final feedback = n == 0
          ? null
          : {'score': 7, 'strengths': ['স্পষ্ট'], 'improvements': ['উদাহরণ দিন'], 'sample_answer': 'নমুনা $n'};
      if (n == 3) {
        return _json({
          'question_number': 3,
          'feedback': feedback,
          'next_question': null,
          'finished': true,
          'summary': {'overall_score': 72, 'verdict': 'ভালো প্রস্তুতি', 'strengths': ['আত্মবিশ্বাস'], 'improvements': ['তথ্য']},
        });
      }
      return _json({'question_number': n + 1, 'feedback': feedback, 'next_question': 'প্রশ্ন-${n + 1}', 'finished': false});
    });

    await http.runWithClient(() async {
      await tester.pumpWidget(_wrap(const MockInterviewScreen()));

      // পদ না দিলে শুরু হবে না
      await tester.tap(find.text('ইন্টারভিউ শুরু করুন'));
      await tester.pump();
      expect(find.text('এই তথ্যটি দিতে হবে'), findsOneWidget);
      expect(sentHistoryLengths, isEmpty);

      await tester.enterText(find.widgetWithText(TextFormField, 'যে পদের জন্য প্রস্তুতি নিচ্ছেন'), 'সিনিয়র অফিসার');
      await tester.tap(find.text('ব্যাংক'));
      await tester.tap(find.text('৩টি'));
      await tester.tap(find.text('ইন্টারভিউ শুরু করুন'));
      await tester.pumpAndSettle();
      expect(find.text('প্রশ্ন-1'), findsOneWidget);

      for (var i = 1; i <= 3; i++) {
        await tester.enterText(find.byType(TextField).last, 'উত্তর $i');
        await tester.tap(find.byTooltip('উত্তর পাঠান'));
        await tester.pumpAndSettle();
      }
    }, () => client);

    expect(firstBody!['interview_type'], 'bank');
    expect(firstBody!['total_questions'], 3);
    expect(firstBody!['target_position'], 'সিনিয়র অফিসার');
    expect(sentHistoryLengths, [0, 1, 2, 3]);
    expect(find.text('স্কোর: 7/10'), findsNWidgets(3));
    expect(find.text('72'), findsOneWidget);
    expect(find.text('ভালো প্রস্তুতি'), findsOneWidget);
    // শেষ হলে উত্তর দেওয়ার বক্স আর থাকে না
    expect(find.byTooltip('উত্তর পাঠান'), findsNothing);
  });

  testWidgets('প্রিমিয়াম: প্ল্যান দেখায়, Nagad শীঘ্রই, পেমেন্ট পেজ খোলে ও সফল হলে প্রিমিয়াম দেখায়', (tester) async {
    tester.view.physicalSize = const Size(800, 1600);
    tester.view.devicePixelRatio = 1.0;
    addTearDown(tester.view.reset);

    var paid = false;
    Map<String, dynamic>? createBody;
    final client = MockClient((req) async {
      switch (req.url.path) {
        case '/api/payments/plans':
          return _json({
            'plans': [
              {'code': 'monthly', 'name': 'মাসিক', 'amount': 99, 'days': 30},
              {'code': 'yearly', 'name': 'বার্ষিক', 'amount': 799, 'days': 365},
            ],
            'providers': [
              {'code': 'bkash', 'name': 'bKash', 'mode': 'mock'},
              {'code': 'nagad', 'name': 'Nagad', 'mode': null},
            ],
          });
        case '/api/payments/status/sub-test-0001':
          return _json(paid
              ? {'subscriber_id': 'sub-test-0001', 'is_premium': true, 'plan_code': 'yearly', 'expires_at': '2027-09-23T10:00:00'}
              : {'subscriber_id': 'sub-test-0001', 'is_premium': false, 'plan_code': null, 'expires_at': null});
        case '/api/payments/create':
          createBody = jsonDecode(utf8.decode(req.bodyBytes));
          return _json({'payment_id': 5, 'redirect_url': 'https://sandbox.bka.sh/pay/5'});
        case '/api/payments/5':
          expect(req.url.queryParameters['subscriber_id'], 'sub-test-0001');
          paid = true;
          return _json({'id': 5, 'status': 'completed', 'trx_id': 'TEST000005', 'is_test': true});
      }
      return _json({'detail': 'not found'}, 404);
    });

    final launched = <Uri>[];
    await http.runWithClient(() async {
      await tester.pumpWidget(_wrap(PremiumScreen(
        subscriberIdOverride: 'sub-test-0001',
        launcher: (uri) async {
          launched.add(uri);
          return true;
        },
      )));
      await tester.pumpAndSettle();

      expect(find.text('৳99'), findsOneWidget);
      expect(find.text('Nagad (শীঘ্রই)'), findsOneWidget);
      expect(find.text('bKash (টেস্ট)'), findsOneWidget);
      expect(find.textContaining('টেস্ট মোড'), findsOneWidget);

      await tester.tap(find.text('বার্ষিক'));
      await tester.tap(find.text('পেমেন্ট করুন'));
      await tester.pumpAndSettle();
      expect(launched.single.toString(), 'https://sandbox.bka.sh/pay/5');

      await tester.tap(find.text('পেমেন্ট স্ট্যাটাস চেক করুন'));
      await tester.pumpAndSettle();
    }, () => client);

    expect(createBody, {'subscriber_id': 'sub-test-0001', 'plan_code': 'yearly', 'provider': 'bkash'});
    expect(find.text('আপনি প্রিমিয়াম সদস্য'), findsOneWidget);
    expect(find.text('পেমেন্ট স্ট্যাটাস চেক করুন'), findsNothing);
  });

  testWidgets('প্রিমিয়াম: Nagad টেস্ট পেমেন্ট ব্যর্থ হলে প্রিমিয়াম হয় না, আবার চেষ্টা করা যায়', (tester) async {
    tester.view.physicalSize = const Size(800, 1600);
    tester.view.devicePixelRatio = 1.0;
    addTearDown(tester.view.reset);

    String? provider;
    final client = MockClient((req) async {
      switch (req.url.path) {
        case '/api/payments/plans':
          return _json({
            'plans': [{'code': 'monthly', 'name': 'মাসিক', 'amount': 99, 'days': 30}],
            'providers': [
              {'code': 'bkash', 'name': 'bKash', 'mode': 'mock'},
              {'code': 'nagad', 'name': 'Nagad', 'mode': 'mock'},
            ],
          });
        case '/api/payments/status/sub-test-0002':
          return _json({'subscriber_id': 'sub-test-0002', 'is_premium': false, 'plan_code': null, 'expires_at': null});
        case '/api/payments/create':
          provider = jsonDecode(utf8.decode(req.bodyBytes))['provider'];
          return _json({'payment_id': 9, 'redirect_url': 'http://localhost:8000/api/payments/mock/checkout/9'});
        case '/api/payments/9':
          return _json({'id': 9, 'status': 'failed', 'trx_id': null, 'is_test': true});
      }
      return _json({'detail': 'not found'}, 404);
    });

    await http.runWithClient(() async {
      await tester.pumpWidget(_wrap(PremiumScreen(
        subscriberIdOverride: 'sub-test-0002',
        launcher: (_) async => true,
      )));
      await tester.pumpAndSettle();
      await tester.tap(find.text('Nagad (টেস্ট)'));
      await tester.tap(find.text('পেমেন্ট করুন'));
      await tester.pumpAndSettle();
      await tester.tap(find.text('পেমেন্ট স্ট্যাটাস চেক করুন'));
      await tester.pump();
    }, () => client);

    expect(provider, 'nagad');
    expect(find.textContaining('পেমেন্ট সম্পন্ন হয়নি'), findsOneWidget);
    expect(find.text('আপনি প্রিমিয়াম সদস্য'), findsNothing);
    expect(find.text('পেমেন্ট স্ট্যাটাস চেক করুন'), findsNothing);
    expect(find.text('পেমেন্ট করুন'), findsOneWidget);
  });
}
