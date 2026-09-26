import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../models/job_match_models.dart';
import '../services/api_service.dart';
import 'circular_detail_screen.dart';

/// জব ম্যাচিং ও স্কিল গ্যাপ অ্যানালাইসিস।
/// ট্যাব ০: প্রোফাইল অনুযায়ী উপযুক্ত সার্কুলার সাজেশন
/// ট্যাব ১: একটা নির্দিষ্ট চাকরির (সার্কুলার বা পেস্ট করা বিবরণ) সাথে মিল ও স্কিল ঘাটতি
class JobMatchScreen extends StatefulWidget {
  static const tabRecommend = 0;
  static const tabSkillGap = 1;

  final int initialTab;
  final int? circularId; // সার্কুলার ডিটেইল থেকে এলে
  final String? circularTitle;

  const JobMatchScreen({super.key, this.initialTab = tabRecommend, this.circularId, this.circularTitle});

  @override
  State<JobMatchScreen> createState() => _JobMatchScreenState();
}

class _JobMatchScreenState extends State<JobMatchScreen> with SingleTickerProviderStateMixin {
  static const _prefsKey = 'job_match_profile';

  final _api = ApiService();
  late final TabController _tabs =
      TabController(length: 2, vsync: this, initialIndex: widget.circularId != null ? 1 : widget.initialTab);

  // প্রোফাইল (দুই ট্যাবে শেয়ার করা)
  final List<String> _skills = [];
  final _skillInput = TextEditingController();
  final _education = TextEditingController();
  final _experience = TextEditingController();
  final _age = TextEditingController();
  bool _profileExpanded = true;

  // স্কিল গ্যাপ ট্যাব
  late int? _circularId = widget.circularId;
  late String? _circularTitle = widget.circularTitle;
  final _jobDescription = TextEditingController();
  JobMatchAnalysis? _analysis;
  bool _analyzing = false;

  // সাজেশন ট্যাব
  RecommendResult? _recommend;
  bool _recommending = false;

  @override
  void initState() {
    super.initState();
    _loadProfile();
  }

  @override
  void dispose() {
    _tabs.dispose();
    for (final c in [_skillInput, _education, _experience, _age, _jobDescription]) {
      c.dispose();
    }
    super.dispose();
  }

  // ---------------- প্রোফাইল ----------------

  Future<void> _loadProfile() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final raw = prefs.getString(_prefsKey);
      if (raw == null || !mounted) return;
      final p = CandidateProfile.fromJson(jsonDecode(raw));
      setState(() {
        _skills
          ..clear()
          ..addAll(p.skills);
        _education.text = p.education ?? '';
        _experience.text = p.experience ?? '';
        _age.text = p.age?.toString() ?? '';
        _profileExpanded = _skills.isEmpty; // আগে সেভ করা থাকলে গুটিয়ে রাখা
      });
    } catch (_) {
      // পুরনো/ভাঙা ডেটা থাকলে নতুন করে শুরু
    }
  }

  CandidateProfile _profile() => CandidateProfile(
        skills: List.of(_skills),
        education: _education.text.trim(),
        experience: _experience.text.trim(),
        age: int.tryParse(_age.text.trim()),
      );

  Future<void> _saveProfile() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_prefsKey, jsonEncode(_profile().toJson()));
  }

  void _addSkills(String input) {
    // কমা দিয়ে একসাথে কয়েকটা স্কিল পেস্ট করা যায়
    final parts = input.split(RegExp(r'[,،;\n]')).map((s) => s.trim()).where((s) => s.isNotEmpty);
    setState(() {
      for (final s in parts) {
        if (!_skills.any((e) => e.toLowerCase() == s.toLowerCase())) _skills.add(s);
      }
      _skillInput.clear();
    });
  }

  bool _ensureProfile() {
    if (_skillInput.text.trim().isNotEmpty) _addSkills(_skillInput.text);
    if (_skills.isEmpty) {
      setState(() => _profileExpanded = true);
      _snack("অন্তত একটা স্কিল যোগ করুন");
      return false;
    }
    return true;
  }

  void _snack(String msg) => ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(msg)));

  String _err(Object e) => "ত্রুটি: ${e.toString().replaceFirst('Exception: ', '')}";

  // ---------------- অ্যাকশন ----------------

  Future<void> _runRecommend() async {
    if (!_ensureProfile()) return;
    FocusScope.of(context).unfocus();
    setState(() {
      _recommending = true;
      _profileExpanded = false;
    });
    try {
      await _saveProfile();
      final result = await _api.recommendJobs(_profile());
      if (mounted) setState(() => _recommend = result);
    } catch (e) {
      if (mounted) _snack(_err(e));
    } finally {
      if (mounted) setState(() => _recommending = false);
    }
  }

  Future<void> _runAnalyze() async {
    if (!_ensureProfile()) return;
    final jd = _jobDescription.text.trim();
    if (_circularId == null && jd.isEmpty) {
      _snack("সার্কুলার বেছে নিন অথবা জব ডেসক্রিপশন দিন");
      return;
    }
    FocusScope.of(context).unfocus();
    setState(() {
      _analyzing = true;
      _profileExpanded = false;
    });
    try {
      await _saveProfile();
      final result = await _api.analyzeJobMatch(
        _profile(),
        circularId: _circularId,
        jobDescription: jd.isEmpty ? null : jd,
      );
      if (mounted) setState(() => _analysis = result);
    } catch (e) {
      if (mounted) _snack(_err(e));
    } finally {
      if (mounted) setState(() => _analyzing = false);
    }
  }

  /// সাজেশন তালিকা থেকে একটা চাকরিতে ট্যাপ করলে স্কিল গ্যাপ ট্যাবে গিয়ে বিশ্লেষণ
  void _analyzeRecommended(RecommendedJob job) {
    setState(() {
      _circularId = job.circularId;
      _circularTitle = job.title;
      _jobDescription.clear();
      _analysis = null;
    });
    _tabs.animateTo(JobMatchScreen.tabSkillGap);
    _runAnalyze();
  }

  // ---------------- UI ----------------

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text("জব ম্যাচিং"),
        bottom: TabBar(
          controller: _tabs,
          tabs: const [Tab(text: "আমার জন্য চাকরি"), Tab(text: "স্কিল গ্যাপ")],
        ),
      ),
      body: TabBarView(
        controller: _tabs,
        children: [_buildRecommendTab(), _buildSkillGapTab()],
      ),
    );
  }

  Widget _page(List<Widget> children) => Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 760),
          child: ListView(padding: const EdgeInsets.all(16), children: children),
        ),
      );

  Widget _buildProfileCard() {
    return Card(
      elevation: 0,
      margin: EdgeInsets.zero,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
        side: BorderSide(color: Colors.grey.shade200),
      ),
      child: ExpansionTile(
        key: ValueKey(_profileExpanded), // বাইরে থেকে খোলা/বন্ধ করা যায়
        initiallyExpanded: _profileExpanded,
        onExpansionChanged: (v) => _profileExpanded = v,
        shape: const Border(),
        leading: const Icon(Icons.person_outline),
        title: const Text("আপনার প্রোফাইল", style: TextStyle(fontWeight: FontWeight.w600)),
        subtitle: Text(
          _skills.isEmpty ? "স্কিল যোগ করুন" : _skills.join(", "),
          maxLines: 1,
          overflow: TextOverflow.ellipsis,
        ),
        childrenPadding: const EdgeInsets.fromLTRB(16, 0, 16, 16),
        children: [
          TextField(
            controller: _skillInput,
            decoration: InputDecoration(
              labelText: "স্কিল",
              hintText: "যেমন: MS Excel, Accounting (Enter চাপুন)",
              border: const OutlineInputBorder(),
              suffixIcon: IconButton(
                tooltip: "স্কিল যোগ করুন",
                icon: const Icon(Icons.add),
                onPressed: () => _addSkills(_skillInput.text),
              ),
            ),
            onSubmitted: _addSkills,
          ),
          if (_skills.isNotEmpty)
            Padding(
              padding: const EdgeInsets.only(top: 8),
              child: Align(
                alignment: Alignment.centerLeft,
                child: Wrap(
                  spacing: 6,
                  runSpacing: 6,
                  children: [
                    for (final s in _skills)
                      InputChip(label: Text(s), onDeleted: () => setState(() => _skills.remove(s))),
                  ],
                ),
              ),
            ),
          const SizedBox(height: 12),
          TextField(
            controller: _education,
            decoration: const InputDecoration(
              labelText: "শিক্ষাগত যোগ্যতা",
              hintText: "যেমন: BBA (Finance), CGPA 3.2",
              border: OutlineInputBorder(),
            ),
          ),
          const SizedBox(height: 12),
          Row(
            children: [
              Expanded(
                flex: 3,
                child: TextField(
                  controller: _experience,
                  decoration: const InputDecoration(
                    labelText: "অভিজ্ঞতা",
                    hintText: "যেমন: ১ বছর সেলস",
                    border: OutlineInputBorder(),
                  ),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: TextField(
                  controller: _age,
                  keyboardType: TextInputType.number,
                  decoration: const InputDecoration(labelText: "বয়স", border: OutlineInputBorder()),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _actionButton({required String label, required IconData icon, required bool busy, required VoidCallback onPressed}) {
    return FilledButton.icon(
      onPressed: busy ? null : onPressed,
      icon: busy
          ? const SizedBox(
              width: 18,
              height: 18,
              child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
            )
          : Icon(icon),
      label: Text(busy ? "AI বিশ্লেষণ করছে..." : label),
      style: FilledButton.styleFrom(minimumSize: const Size.fromHeight(50)),
    );
  }

  // ---------- ট্যাব ০: সাজেশন ----------

  Widget _buildRecommendTab() {
    final r = _recommend;
    return _page([
      _buildProfileCard(),
      const SizedBox(height: 16),
      _actionButton(
        label: "উপযুক্ত চাকরি খুঁজুন",
        icon: Icons.travel_explore_rounded,
        busy: _recommending,
        onPressed: _runRecommend,
      ),
      if (r != null) ...[
        const SizedBox(height: 20),
        if (r.jobs.isEmpty)
          _EmptyNote(
            r.considered == 0
                ? "এই মুহূর্তে কোনো চালু সার্কুলার নেই।"
                : "${r.considered}টা সার্কুলারের মধ্যে আপনার প্রোফাইলের সাথে মেলে এমন কিছু পাওয়া যায়নি।",
          )
        else ...[
          Text(
            "${r.considered}টা চালু সার্কুলারের মধ্যে আপনার জন্য সেরা ${r.jobs.length}টা",
            style: const TextStyle(color: Colors.black54),
          ),
          const SizedBox(height: 8),
          for (final job in r.jobs) _RecommendedJobCard(job: job, onTap: () => _analyzeRecommended(job)),
        ],
      ],
    ]);
  }

  // ---------- ট্যাব ১: স্কিল গ্যাপ ----------

  Widget _buildSkillGapTab() {
    final a = _analysis;
    return _page([
      _buildProfileCard(),
      const SizedBox(height: 16),
      const Text("কোন চাকরির সাথে মেলাবেন?", style: TextStyle(fontWeight: FontWeight.w600)),
      const SizedBox(height: 8),
      if (_circularId != null)
        Card(
          elevation: 0,
          margin: EdgeInsets.zero,
          color: Theme.of(context).colorScheme.primary.withValues(alpha: 0.06),
          child: ListTile(
            leading: const Icon(Icons.article_outlined),
            title: Text(_circularTitle ?? "সার্কুলার #$_circularId", maxLines: 2, overflow: TextOverflow.ellipsis),
            trailing: IconButton(
              tooltip: "সার্কুলার বাদ দিন",
              icon: const Icon(Icons.close),
              onPressed: () => setState(() {
                _circularId = null;
                _circularTitle = null;
                _analysis = null;
              }),
            ),
          ),
        )
      else
        TextField(
          controller: _jobDescription,
          maxLines: 5,
          decoration: const InputDecoration(
            labelText: "জব ডেসক্রিপশন / সার্কুলারের চাহিদা",
            hintText: "সার্কুলারে যোগ্যতা, দায়িত্ব, বয়সসীমা যা লেখা আছে তা পেস্ট করুন",
            border: OutlineInputBorder(),
            alignLabelWithHint: true,
          ),
        ),
      const SizedBox(height: 16),
      _actionButton(
        label: "স্কিল গ্যাপ বিশ্লেষণ করুন",
        icon: Icons.analytics_outlined,
        busy: _analyzing,
        onPressed: _runAnalyze,
      ),
      if (a != null) ...[
        const SizedBox(height: 20),
        _AnalysisView(
          analysis: a,
          onOpenCircular: a.circularId == null
              ? null
              : () => Navigator.push(
                    context,
                    MaterialPageRoute(builder: (_) => CircularDetailScreen(circularId: a.circularId!)),
                  ),
        ),
      ],
    ]);
  }
}

// ---------------- ছোট উইজেট ----------------

Color _scoreColor(int score) {
  if (score >= 70) return Colors.green.shade700;
  if (score >= 45) return Colors.orange.shade800;
  return Colors.red.shade700;
}

class _EmptyNote extends StatelessWidget {
  final String text;
  const _EmptyNote(this.text);

  @override
  Widget build(BuildContext context) => Padding(
        padding: const EdgeInsets.symmetric(vertical: 24),
        child: Text(text, textAlign: TextAlign.center, style: const TextStyle(color: Colors.black54)),
      );
}

class _RecommendedJobCard extends StatelessWidget {
  final RecommendedJob job;
  final VoidCallback onTap;
  const _RecommendedJobCard({required this.job, required this.onTap});

  @override
  Widget build(BuildContext context) {
    final color = _scoreColor(job.matchScore);
    final d = job.applicationDeadline;
    return Card(
      elevation: 0,
      margin: const EdgeInsets.only(bottom: 10),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
        side: BorderSide(color: Colors.grey.shade200),
      ),
      child: InkWell(
        borderRadius: BorderRadius.circular(12),
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.all(14),
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Container(
                width: 52,
                padding: const EdgeInsets.symmetric(vertical: 8),
                decoration: BoxDecoration(
                  color: color.withValues(alpha: 0.1),
                  borderRadius: BorderRadius.circular(10),
                ),
                child: Column(
                  children: [
                    Text("${job.matchScore}", style: TextStyle(color: color, fontWeight: FontWeight.bold, fontSize: 18)),
                    Text("মিল", style: TextStyle(color: color, fontSize: 11)),
                  ],
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(job.title, style: const TextStyle(fontWeight: FontWeight.w600, height: 1.35)),
                    if (job.organization != null || d != null)
                      Padding(
                        padding: const EdgeInsets.only(top: 2),
                        child: Text(
                          [
                            if (job.organization != null) job.organization!,
                            if (d != null) "শেষ তারিখ: ${d.day}/${d.month}/${d.year}",
                          ].join(" · "),
                          style: const TextStyle(color: Colors.black54, fontSize: 12.5),
                        ),
                      ),
                    const SizedBox(height: 6),
                    Text(job.reason, style: const TextStyle(height: 1.45, fontSize: 13.5)),
                    const SizedBox(height: 6),
                    Text(
                      "স্কিল গ্যাপ দেখুন →",
                      style: TextStyle(color: Theme.of(context).colorScheme.primary, fontSize: 13),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _AnalysisView extends StatelessWidget {
  final JobMatchAnalysis analysis;
  final VoidCallback? onOpenCircular;
  const _AnalysisView({required this.analysis, this.onOpenCircular});

  static const _eligibilityLabels = {
    "eligible": ("যোগ্য", Icons.check_circle_outline),
    "partially": ("আংশিক যোগ্য", Icons.remove_circle_outline),
    "not_eligible": ("যোগ্য নন", Icons.cancel_outlined),
    "unknown": ("শর্ত জানা নেই", Icons.help_outline),
  };

  static const _importance = {"high": "জরুরি", "medium": "মাঝারি", "low": "কম জরুরি"};

  @override
  Widget build(BuildContext context) {
    final a = analysis;
    final theme = Theme.of(context);
    final color = _scoreColor(a.matchScore);
    final (eligText, eligIcon) = _eligibilityLabels[a.eligibility] ?? ("অজানা", Icons.help_outline);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        if (!a.infoSufficient)
          Container(
            margin: const EdgeInsets.only(bottom: 12),
            padding: const EdgeInsets.all(10),
            decoration: BoxDecoration(color: const Color(0xFFFFF4CE), borderRadius: BorderRadius.circular(8)),
            child: const Text(
              "⚠️ এই সার্কুলারে যোগ্যতার বিস্তারিত তথ্য নেই, তাই বিশ্লেষণ নির্ভরযোগ্য নয়। "
              "মূল সার্কুলার দেখে জব ডেসক্রিপশন পেস্ট করে আবার যাচাই করুন।",
              style: TextStyle(color: Color(0xFF7A5B00), height: 1.45),
            ),
          ),
        Card(
          elevation: 0,
          margin: EdgeInsets.zero,
          color: theme.colorScheme.primary.withValues(alpha: 0.06),
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                if (a.jobTitle != null)
                  Padding(
                    padding: const EdgeInsets.only(bottom: 8),
                    child: Text(a.jobTitle!, style: const TextStyle(fontWeight: FontWeight.w600)),
                  ),
                Row(
                  crossAxisAlignment: CrossAxisAlignment.end,
                  children: [
                    // তথ্য কম হলে স্কোর বিভ্রান্তিকর — তাই সংখ্যা না দেখিয়ে লেখা
                    if (a.infoSufficient) ...[
                      Text(
                        "${a.matchScore}",
                        style: theme.textTheme.displaySmall?.copyWith(fontWeight: FontWeight.bold, color: color),
                      ),
                      const Padding(
                        padding: EdgeInsets.only(bottom: 6),
                        child: Text(" / 100 মিল", style: TextStyle(color: Colors.black54)),
                      ),
                    ] else
                      const Text("স্কোর: তথ্য অপর্যাপ্ত",
                          style: TextStyle(fontSize: 18, fontWeight: FontWeight.w600, color: Colors.black54)),
                    const Spacer(),
                    Chip(avatar: Icon(eligIcon, size: 18), label: Text(eligText)),
                  ],
                ),
                if (a.infoSufficient) ...[
                  const SizedBox(height: 8),
                  LinearProgressIndicator(
                    value: a.matchScore / 100,
                    minHeight: 6,
                    color: color,
                    borderRadius: BorderRadius.circular(3),
                  ),
                ],
                const SizedBox(height: 12),
                Text(a.verdict, style: const TextStyle(height: 1.5)),
              ],
            ),
          ),
        ),
        if (a.matchedSkills.isNotEmpty) ...[
          const _SectionTitle("যা মিলেছে"),
          Wrap(
            spacing: 6,
            runSpacing: 6,
            children: [
              for (final s in a.matchedSkills)
                Chip(
                  avatar: Icon(Icons.check, size: 16, color: Colors.green.shade700),
                  label: Text(s),
                  visualDensity: VisualDensity.compact,
                ),
            ],
          ),
        ],
        if (a.missingSkills.isNotEmpty) ...[
          const _SectionTitle("স্কিল গ্যাপ — যা শিখতে হবে"),
          for (final m in a.missingSkills)
            Card(
              elevation: 0,
              margin: const EdgeInsets.only(bottom: 8),
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(10),
                side: BorderSide(color: Colors.grey.shade200),
              ),
              child: Padding(
                padding: const EdgeInsets.all(12),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Expanded(child: Text(m.skill, style: const TextStyle(fontWeight: FontWeight.w600))),
                        _ImportanceBadge(level: m.importance, label: _importance[m.importance] ?? m.importance),
                      ],
                    ),
                    const SizedBox(height: 6),
                    Text(m.howToLearn, style: const TextStyle(height: 1.45, color: Colors.black87)),
                  ],
                ),
              ),
            ),
        ],
        if (a.strengths.isNotEmpty) ...[
          const _SectionTitle("আপনার শক্তির দিক"),
          for (final s in a.strengths) _Bullet(s, Icons.star_outline, Colors.green.shade700),
        ],
        if (a.actionPlan.isNotEmpty) ...[
          const _SectionTitle("আবেদনের আগে করণীয়"),
          for (var i = 0; i < a.actionPlan.length; i++)
            _Bullet(a.actionPlan[i].replaceFirst(RegExp(r'^[০-৯0-9]+[.)]\s*'), ''), null, null, number: i + 1),
        ],
        if (onOpenCircular != null) ...[
          const SizedBox(height: 12),
          OutlinedButton.icon(
            onPressed: onOpenCircular,
            icon: const Icon(Icons.article_outlined),
            label: const Text("সার্কুলার দেখুন"),
            style: OutlinedButton.styleFrom(minimumSize: const Size.fromHeight(48)),
          ),
        ],
      ],
    );
  }
}

class _SectionTitle extends StatelessWidget {
  final String text;
  const _SectionTitle(this.text);

  @override
  Widget build(BuildContext context) => Padding(
        padding: const EdgeInsets.only(top: 20, bottom: 8),
        child: Text(text, style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 15)),
      );
}

class _ImportanceBadge extends StatelessWidget {
  final String level;
  final String label;
  const _ImportanceBadge({required this.level, required this.label});

  @override
  Widget build(BuildContext context) {
    final color = switch (level) {
      "high" => Colors.red.shade700,
      "medium" => Colors.orange.shade800,
      _ => Colors.blueGrey,
    };
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
      decoration: BoxDecoration(color: color.withValues(alpha: 0.1), borderRadius: BorderRadius.circular(12)),
      child: Text(label, style: TextStyle(color: color, fontSize: 12, fontWeight: FontWeight.w600)),
    );
  }
}

class _Bullet extends StatelessWidget {
  final String text;
  final IconData? icon;
  final Color? color;
  final int? number;
  const _Bullet(this.text, this.icon, this.color, {this.number});

  @override
  Widget build(BuildContext context) => Padding(
        padding: const EdgeInsets.only(bottom: 6),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            SizedBox(
              width: 22,
              child: number != null
                  ? Text("$number.", style: const TextStyle(fontWeight: FontWeight.w600))
                  : Icon(icon, size: 17, color: color),
            ),
            const SizedBox(width: 4),
            Expanded(child: Text(text, style: const TextStyle(height: 1.45))),
          ],
        ),
      );
}
