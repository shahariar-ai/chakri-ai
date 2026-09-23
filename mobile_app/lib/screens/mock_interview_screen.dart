import 'package:flutter/material.dart';
import '../models/interview_models.dart';
import '../services/api_service.dart';

/// AI মক ইন্টারভিউ কোচ।
/// ধাপ: সেটআপ ফর্ম -> একটা একটা করে প্রশ্ন ও উত্তর (প্রতি উত্তরে ফিডব্যাক) -> সামগ্রিক সারাংশ।
class MockInterviewScreen extends StatefulWidget {
  const MockInterviewScreen({super.key});

  @override
  State<MockInterviewScreen> createState() => _MockInterviewScreenState();
}

class _MockInterviewScreenState extends State<MockInterviewScreen> {
  final _api = ApiService();
  final _formKey = GlobalKey<FormState>();
  final _positionController = TextEditingController();
  final _backgroundController = TextEditingController();
  final _answerController = TextEditingController();
  final _scrollController = ScrollController();

  String _interviewType = "private";
  String _language = "bn";
  int _totalQuestions = 5;

  InterviewSetup? _setup; // null = এখনো সেটআপ ফর্মে আছি
  final List<InterviewTurn> _turns = [];
  InterviewSummary? _summary;
  bool _loading = false;

  static const _typeLabels = {
    "private": "বেসরকারি চাকরি",
    "bank": "ব্যাংক",
    "govt_viva": "সরকারি ভাইভা",
  };

  @override
  void dispose() {
    _positionController.dispose();
    _backgroundController.dispose();
    _answerController.dispose();
    _scrollController.dispose();
    super.dispose();
  }

  void _showError(Object e) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text("ত্রুটি: ${e.toString().replaceFirst('Exception: ', '')}")),
    );
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeOut,
        );
      }
    });
  }

  Future<void> _start() async {
    if (!_formKey.currentState!.validate()) return;
    FocusScope.of(context).unfocus();

    final setup = InterviewSetup(
      targetPosition: _positionController.text.trim(),
      interviewType: _interviewType,
      language: _language,
      totalQuestions: _totalQuestions,
      candidateBackground: _backgroundController.text.trim(),
    );
    setState(() => _loading = true);
    try {
      final result = await _api.interviewTurn(setup, const []);
      if (!mounted) return;
      setState(() {
        _setup = setup;
        _turns
          ..clear()
          ..add(InterviewTurn(question: result.nextQuestion ?? ''));
        _summary = null;
      });
    } catch (e) {
      if (mounted) _showError(e);
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _submitAnswer() async {
    final answer = _answerController.text.trim();
    if (answer.isEmpty) return;
    FocusScope.of(context).unfocus();

    final current = _turns.last;
    setState(() {
      current.answer = answer;
      _loading = true;
    });
    _scrollToBottom();
    try {
      final result = await _api.interviewTurn(_setup!, _turns);
      if (!mounted) return;
      setState(() {
        current.feedback = result.feedback;
        if (result.finished) {
          _summary = result.summary;
        } else {
          _turns.add(InterviewTurn(question: result.nextQuestion ?? ''));
        }
        _answerController.clear();
      });
      _scrollToBottom();
    } catch (e) {
      // উত্তর ফেরত নিয়ে আসা হয় যাতে ইউজার আবার পাঠাতে পারেন
      if (mounted) {
        setState(() => current.answer = null);
        _showError(e);
      }
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  void _restart() {
    setState(() {
      _setup = null;
      _turns.clear();
      _summary = null;
      _answerController.clear();
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text("মক ইন্টারভিউ কোচ"),
        actions: [
          if (_setup != null)
            IconButton(
              tooltip: "নতুন ইন্টারভিউ",
              icon: const Icon(Icons.restart_alt_rounded),
              onPressed: _loading ? null : _restart,
            ),
        ],
      ),
      body: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 760),
          child: _setup == null ? _buildSetupForm() : _buildInterview(),
        ),
      ),
    );
  }

  // ---------------- সেটআপ ফর্ম ----------------

  Widget _buildSetupForm() {
    return Form(
      key: _formKey,
      child: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Text(
            "পদ ও ইন্টারভিউর ধরন বেছে নিন। AI একজন ইন্টারভিউয়ারের মতো একটা একটা করে প্রশ্ন করবে, "
            "আর প্রতিটা উত্তরের পর স্কোর ও পরামর্শ দেবে।",
            style: Theme.of(context).textTheme.bodyMedium?.copyWith(color: Colors.black54),
          ),
          const SizedBox(height: 16),
          TextFormField(
            controller: _positionController,
            decoration: const InputDecoration(
              labelText: "যে পদের জন্য প্রস্তুতি নিচ্ছেন",
              hintText: "যেমন: সিনিয়র অফিসার, জুনিয়র সফটওয়্যার ইঞ্জিনিয়ার",
              border: OutlineInputBorder(),
            ),
            validator: (v) => (v == null || v.trim().isEmpty) ? "এই তথ্যটি দিতে হবে" : null,
          ),
          const SizedBox(height: 16),
          const Text("ইন্টারভিউর ধরন", style: TextStyle(fontWeight: FontWeight.w600)),
          const SizedBox(height: 8),
          SegmentedButton<String>(
            segments: [
              for (final e in _typeLabels.entries) ButtonSegment(value: e.key, label: Text(e.value)),
            ],
            selected: {_interviewType},
            onSelectionChanged: (s) => setState(() => _interviewType = s.first),
          ),
          const SizedBox(height: 16),
          const Text("প্রশ্নের সংখ্যা", style: TextStyle(fontWeight: FontWeight.w600)),
          const SizedBox(height: 8),
          SegmentedButton<int>(
            segments: const [
              ButtonSegment(value: 3, label: Text("৩টি")),
              ButtonSegment(value: 5, label: Text("৫টি")),
              ButtonSegment(value: 7, label: Text("৭টি")),
            ],
            selected: {_totalQuestions},
            onSelectionChanged: (s) => setState(() => _totalQuestions = s.first),
          ),
          const SizedBox(height: 16),
          const Text("ভাষা", style: TextStyle(fontWeight: FontWeight.w600)),
          const SizedBox(height: 8),
          SegmentedButton<String>(
            segments: const [
              ButtonSegment(value: "bn", label: Text("বাংলা")),
              ButtonSegment(value: "en", label: Text("English")),
            ],
            selected: {_language},
            onSelectionChanged: (s) => setState(() => _language = s.first),
          ),
          const SizedBox(height: 16),
          TextFormField(
            controller: _backgroundController,
            maxLines: 3,
            decoration: const InputDecoration(
              labelText: "আপনার সংক্ষিপ্ত পরিচিতি (ঐচ্ছিক)",
              hintText: "যেমন: BBA (Finance), ১ বছর সেলস অভিজ্ঞতা",
              border: OutlineInputBorder(),
              alignLabelWithHint: true,
            ),
          ),
          const SizedBox(height: 24),
          FilledButton.icon(
            onPressed: _loading ? null : _start,
            icon: _loading ? const _ButtonSpinner() : const Icon(Icons.play_arrow_rounded),
            label: Text(_loading ? "প্রস্তুত হচ্ছে..." : "ইন্টারভিউ শুরু করুন"),
            style: FilledButton.styleFrom(minimumSize: const Size.fromHeight(50)),
          ),
        ],
      ),
    );
  }

  // ---------------- ইন্টারভিউ চলাকালীন ----------------

  Widget _buildInterview() {
    final waitingForAnswer = _summary == null && _turns.isNotEmpty && _turns.last.answer == null;

    return Column(
      children: [
        Expanded(
          child: ListView(
            controller: _scrollController,
            padding: const EdgeInsets.all(16),
            children: [
              for (var i = 0; i < _turns.length; i++) _TurnCard(
                number: i + 1,
                total: _setup!.totalQuestions,
                turn: _turns[i],
              ),
              if (_loading)
                const Padding(
                  padding: EdgeInsets.all(16),
                  child: Center(child: CircularProgressIndicator()),
                ),
              if (_summary != null) ...[
                _SummaryCard(summary: _summary!),
                const SizedBox(height: 12),
                FilledButton.icon(
                  onPressed: _restart,
                  icon: const Icon(Icons.restart_alt_rounded),
                  label: const Text("নতুন ইন্টারভিউ দিন"),
                  style: FilledButton.styleFrom(minimumSize: const Size.fromHeight(48)),
                ),
              ],
            ],
          ),
        ),
        if (waitingForAnswer) _buildAnswerBox(),
      ],
    );
  }

  Widget _buildAnswerBox() {
    return SafeArea(
      top: false,
      child: Container(
        padding: const EdgeInsets.fromLTRB(12, 8, 8, 8),
        decoration: BoxDecoration(
          color: Colors.white,
          border: Border(top: BorderSide(color: Colors.grey.shade200)),
        ),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.end,
          children: [
            Expanded(
              child: TextField(
                controller: _answerController,
                minLines: 1,
                maxLines: 5,
                enabled: !_loading,
                decoration: const InputDecoration(
                  hintText: "আপনার উত্তর লিখুন...",
                  border: OutlineInputBorder(),
                  isDense: true,
                ),
              ),
            ),
            const SizedBox(width: 8),
            IconButton.filled(
              tooltip: "উত্তর পাঠান",
              onPressed: _loading ? null : _submitAnswer,
              icon: const Icon(Icons.send_rounded),
            ),
          ],
        ),
      ),
    );
  }
}

class _ButtonSpinner extends StatelessWidget {
  const _ButtonSpinner();

  @override
  Widget build(BuildContext context) => const SizedBox(
        width: 18,
        height: 18,
        child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
      );
}

/// একটা প্রশ্ন + উত্তর + ফিডব্যাক
class _TurnCard extends StatelessWidget {
  final int number;
  final int total;
  final InterviewTurn turn;

  const _TurnCard({required this.number, required this.total, required this.turn});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Padding(
      padding: const EdgeInsets.only(bottom: 16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Text(
            "প্রশ্ন $number / $total",
            style: theme.textTheme.labelMedium?.copyWith(color: theme.colorScheme.primary),
          ),
          const SizedBox(height: 4),
          Container(
            padding: const EdgeInsets.all(14),
            decoration: BoxDecoration(
              color: Colors.white,
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: Colors.grey.shade200),
            ),
            child: Text(turn.question, style: const TextStyle(fontSize: 15.5, height: 1.5)),
          ),
          if (turn.answer != null) ...[
            const SizedBox(height: 8),
            Align(
              alignment: Alignment.centerRight,
              child: Container(
                constraints: const BoxConstraints(maxWidth: 560),
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: theme.colorScheme.primary.withValues(alpha: 0.08),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Text(turn.answer!, style: const TextStyle(height: 1.5)),
              ),
            ),
          ],
          if (turn.feedback != null) ...[
            const SizedBox(height: 8),
            _FeedbackCard(feedback: turn.feedback!),
          ],
        ],
      ),
    );
  }
}

class _FeedbackCard extends StatelessWidget {
  final AnswerFeedback feedback;
  const _FeedbackCard({required this.feedback});

  Color _scoreColor(int score) {
    if (score >= 8) return Colors.green.shade700;
    if (score >= 5) return Colors.orange.shade800;
    return Colors.red.shade700;
  }

  @override
  Widget build(BuildContext context) {
    final color = _scoreColor(feedback.score);
    return Card(
      elevation: 0,
      margin: EdgeInsets.zero,
      color: const Color(0xFFFBFBF6),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
        side: BorderSide(color: Colors.grey.shade200),
      ),
      child: Padding(
        padding: const EdgeInsets.fromLTRB(14, 12, 14, 4),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const Icon(Icons.insights_rounded, size: 18),
                const SizedBox(width: 6),
                const Text("ফিডব্যাক", style: TextStyle(fontWeight: FontWeight.w600)),
                const Spacer(),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 3),
                  decoration: BoxDecoration(
                    color: color.withValues(alpha: 0.1),
                    borderRadius: BorderRadius.circular(20),
                  ),
                  child: Text(
                    "স্কোর: ${feedback.score}/10",
                    style: TextStyle(color: color, fontWeight: FontWeight.w600),
                  ),
                ),
              ],
            ),
            _BulletList(title: "ভালো দিক", items: feedback.strengths, icon: Icons.check_circle_outline, color: Colors.green.shade700),
            _BulletList(title: "যা উন্নত করা দরকার", items: feedback.improvements, icon: Icons.lightbulb_outline, color: Colors.orange.shade800),
            Theme(
              // ExpansionTile-এর ডিফল্ট divider লাইন লুকানো
              data: Theme.of(context).copyWith(dividerColor: Colors.transparent),
              child: ExpansionTile(
                tilePadding: EdgeInsets.zero,
                title: const Text("আদর্শ উত্তরের নমুনা", style: TextStyle(fontSize: 14, fontWeight: FontWeight.w600)),
                childrenPadding: const EdgeInsets.only(bottom: 12),
                children: [SelectableText(feedback.sampleAnswer, style: const TextStyle(height: 1.6))],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _SummaryCard extends StatelessWidget {
  final InterviewSummary summary;
  const _SummaryCard({required this.summary});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Card(
      elevation: 0,
      margin: EdgeInsets.zero,
      color: theme.colorScheme.primary.withValues(alpha: 0.06),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text("ইন্টারভিউ শেষ! সামগ্রিক ফলাফল", style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold)),
            const SizedBox(height: 12),
            Row(
              children: [
                Text(
                  "${summary.overallScore}",
                  style: theme.textTheme.displaySmall?.copyWith(
                    fontWeight: FontWeight.bold,
                    color: theme.colorScheme.primary,
                  ),
                ),
                const Text(" / 100", style: TextStyle(color: Colors.black54)),
              ],
            ),
            const SizedBox(height: 8),
            LinearProgressIndicator(
              value: summary.overallScore / 100,
              minHeight: 6,
              borderRadius: BorderRadius.circular(3),
            ),
            const SizedBox(height: 12),
            Text(summary.verdict, style: const TextStyle(height: 1.5)),
            _BulletList(title: "আপনার শক্তির দিক", items: summary.strengths, icon: Icons.check_circle_outline, color: Colors.green.shade700),
            _BulletList(title: "পরবর্তী প্রস্তুতির জন্য", items: summary.improvements, icon: Icons.lightbulb_outline, color: Colors.orange.shade800),
          ],
        ),
      ),
    );
  }
}

class _BulletList extends StatelessWidget {
  final String title;
  final List<String> items;
  final IconData icon;
  final Color color;

  const _BulletList({required this.title, required this.items, required this.icon, required this.color});

  @override
  Widget build(BuildContext context) {
    if (items.isEmpty) return const SizedBox.shrink();
    return Padding(
      padding: const EdgeInsets.only(top: 10),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(title, style: TextStyle(fontWeight: FontWeight.w600, color: color, fontSize: 13.5)),
          const SizedBox(height: 4),
          for (final item in items)
            Padding(
              padding: const EdgeInsets.only(bottom: 4),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Padding(
                    padding: const EdgeInsets.only(top: 2),
                    child: Icon(icon, size: 16, color: color),
                  ),
                  const SizedBox(width: 6),
                  Expanded(child: Text(item, style: const TextStyle(height: 1.45))),
                ],
              ),
            ),
        ],
      ),
    );
  }
}
