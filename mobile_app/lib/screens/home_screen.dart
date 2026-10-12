import 'package:flutter/material.dart';
import 'resume_form_screen.dart';
import 'circular_list_screen.dart';
import 'subject_list_screen.dart';
import 'cover_letter_screen.dart';
import 'mock_interview_screen.dart';
import 'premium_screen.dart';
import '../config/app_config.dart';
import 'job_match_screen.dart';

class HomeScreen extends StatelessWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    final features = [
      _FeatureItem(
        icon: Icons.description_outlined,
        title: "AI রিজিউম বিল্ডার",
        subtitle: "তথ্য দিন, AI আপনার জন্য প্রফেশনাল রিজিউম বানাবে",
        enabled: true,
        onTap: (ctx) => Navigator.push(
          ctx,
          MaterialPageRoute(builder: (_) => const ResumeFormScreen()),
        ),
      ),
      _FeatureItem(
        icon: Icons.campaign_outlined,
        title: "চাকরির সার্কুলার",
        subtitle: "সরকারি ও বেসরকারি সকল চাকরির বিজ্ঞপ্তি",
        enabled: true,
        onTap: (ctx) => Navigator.push(
          ctx,
          MaterialPageRoute(builder: (_) => const CircularListScreen()),
        ),
      ),
      _FeatureItem(
        icon: Icons.quiz_outlined,
        title: "প্রশ্নব্যাংক ও স্টাডি",
        subtitle: "পুরনো পরীক্ষার প্রশ্ন-উত্তর ও বিষয়ভিত্তিক পড়ার উপকরণ",
        enabled: true,
        onTap: (ctx) => Navigator.push(
          ctx,
          MaterialPageRoute(builder: (_) => const SubjectListScreen()),
        ),
      ),
      _FeatureItem(
        icon: Icons.mail_outline,
        title: "কভার লেটার জেনারেটর",
        subtitle: "জব পোস্ট অনুযায়ী কাস্টম কভার লেটার",
        enabled: true,
        onTap: (ctx) => Navigator.push(
          ctx,
          MaterialPageRoute(builder: (_) => const CoverLetterScreen()),
        ),
      ),
      _FeatureItem(
        icon: Icons.mic_none_rounded,
        title: "মক ইন্টারভিউ কোচ",
        subtitle: "AI এর সাথে ইন্টারভিউ প্র্যাকটিস করুন",
        enabled: true,
        onTap: (ctx) => Navigator.push(
          ctx,
          MaterialPageRoute(builder: (_) => const MockInterviewScreen()),
        ),
      ),
      // প্রথম release-এ বন্ধ (Play Billing নীতি); চালু করতে --dart-define=PAYMENTS_ENABLED=true
      if (AppConfig.paymentsEnabled)
      _FeatureItem(
        icon: Icons.workspace_premium_outlined,
        title: "প্রিমিয়াম",
        subtitle: "bKash/Nagad দিয়ে সাবস্ক্রিপশন নিন",
        enabled: true,
        onTap: (ctx) => Navigator.push(
          ctx,
          MaterialPageRoute(builder: (_) => const PremiumScreen()),
        ),
      ),
      _FeatureItem(
        icon: Icons.search_rounded,
        title: "জব ম্যাচিং",
        subtitle: "আপনার স্কিল অনুযায়ী চাকরির সাজেশন",
        enabled: true,
        onTap: (ctx) => Navigator.push(
          ctx,
          MaterialPageRoute(builder: (_) => const JobMatchScreen(initialTab: JobMatchScreen.tabRecommend)),
        ),
      ),
      _FeatureItem(
        icon: Icons.trending_up_rounded,
        title: "স্কিল গ্যাপ অ্যানালাইসিস",
        subtitle: "কোন স্কিল শিখলে চাকরি পাওয়া সহজ হবে",
        enabled: true,
        onTap: (ctx) => Navigator.push(
          ctx,
          MaterialPageRoute(builder: (_) => const JobMatchScreen(initialTab: JobMatchScreen.tabSkillGap)),
        ),
      ),
    ];

    return Scaffold(
      body: SafeArea(
        child: CustomScrollView(
          slivers: [
            SliverToBoxAdapter(
              child: Padding(
                padding: const EdgeInsets.fromLTRB(20, 24, 20, 8),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      "চাকরি AI",
                      style: theme.textTheme.headlineMedium?.copyWith(
                        fontWeight: FontWeight.bold,
                        color: theme.colorScheme.primary,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      "আপনার AI ক্যারিয়ার সহায়ক",
                      style: theme.textTheme.bodyLarge?.copyWith(
                        color: Colors.black54,
                      ),
                    ),
                  ],
                ),
              ),
            ),
            SliverPadding(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
              sliver: SliverList(
                delegate: SliverChildBuilderDelegate(
                  (context, index) {
                    final f = features[index];
                    return _FeatureCard(item: f);
                  },
                  childCount: features.length,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _FeatureItem {
  final IconData icon;
  final String title;
  final String subtitle;
  final bool enabled;
  final void Function(BuildContext)? onTap;

  _FeatureItem({
    required this.icon,
    required this.title,
    required this.subtitle,
    required this.enabled,
    this.onTap,
  });
}

class _FeatureCard extends StatelessWidget {
  final _FeatureItem item;
  const _FeatureCard({required this.item});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      elevation: 0,
      color: Colors.white,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
        side: BorderSide(color: Colors.grey.shade200),
      ),
      child: InkWell(
        borderRadius: BorderRadius.circular(16),
        onTap: item.enabled ? () => item.onTap?.call(context) : null,
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Row(
            children: [
              Container(
                width: 48,
                height: 48,
                decoration: BoxDecoration(
                  color: item.enabled
                      ? theme.colorScheme.primary.withValues(alpha: 0.1)
                      : Colors.grey.shade100,
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Icon(
                  item.icon,
                  color: item.enabled ? theme.colorScheme.primary : Colors.grey,
                ),
              ),
              const SizedBox(width: 14),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      item.title,
                      style: theme.textTheme.titleMedium?.copyWith(
                        fontWeight: FontWeight.w600,
                        color: item.enabled ? Colors.black87 : Colors.grey,
                      ),
                    ),
                    const SizedBox(height: 2),
                    Text(
                      item.subtitle,
                      style: theme.textTheme.bodySmall?.copyWith(
                        color: Colors.black45,
                      ),
                    ),
                  ],
                ),
              ),
              if (!item.enabled)
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                  decoration: BoxDecoration(
                    color: Colors.grey.shade100,
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: const Text(
                    "শীঘ্রই আসছে",
                    style: TextStyle(fontSize: 11, color: Colors.grey),
                  ),
                )
              else
                const Icon(Icons.chevron_right_rounded, color: Colors.grey),
            ],
          ),
        ),
      ),
    );
  }
}
