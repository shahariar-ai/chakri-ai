import 'package:flutter/material.dart';
import '../models/question_models.dart';
import '../services/api_service.dart';
import 'study_material_detail_screen.dart';

class QuestionListScreen extends StatelessWidget {
  final Subject subject;
  const QuestionListScreen({super.key, required this.subject});

  @override
  Widget build(BuildContext context) {
    return DefaultTabController(
      length: 2,
      child: Scaffold(
        appBar: AppBar(
          title: Text(subject.name),
          bottom: const TabBar(
            tabs: [
              Tab(text: "প্রশ্নব্যাংক"),
              Tab(text: "পড়ার উপকরণ"),
            ],
          ),
        ),
        body: TabBarView(
          children: [
            _QuestionBankTab(subject: subject),
            _StudyMaterialTab(subject: subject),
          ],
        ),
      ),
    );
  }
}

class _QuestionBankTab extends StatefulWidget {
  final Subject subject;
  const _QuestionBankTab({required this.subject});

  @override
  State<_QuestionBankTab> createState() => _QuestionBankTabState();
}

class _QuestionBankTabState extends State<_QuestionBankTab> {
  static const _pageSize = 30;

  final _api = ApiService();
  List<ExamQuestion> _questions = [];
  bool _loading = true;
  bool _loadingMore = false;
  // শেষ পেজে _pageSize-এর কম প্রশ্ন এলে ধরে নেওয়া হয় আর নেই
  bool _hasMore = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final result = await _api.getQuestions(subjectId: widget.subject.id, limit: _pageSize);
      setState(() {
        _questions = result;
        _hasMore = result.length == _pageSize;
      });
    } catch (e) {
      setState(() => _error = e.toString());
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _loadMore() async {
    setState(() => _loadingMore = true);
    try {
      final result = await _api.getQuestions(
        subjectId: widget.subject.id,
        skip: _questions.length,
        limit: _pageSize,
      );
      setState(() {
        _questions.addAll(result);
        _hasMore = result.length == _pageSize;
      });
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(e.toString())));
    } finally {
      if (mounted) setState(() => _loadingMore = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_loading) return const Center(child: CircularProgressIndicator());
    if (_error != null) {
      return Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(_error!),
            const SizedBox(height: 8),
            OutlinedButton(onPressed: _load, child: const Text("আবার চেষ্টা করুন")),
          ],
        ),
      );
    }
    if (_questions.isEmpty) {
      return const Center(child: Text("এই বিষয়ে এখনো কোনো প্রশ্ন যোগ করা হয়নি"));
    }
    return ListView.builder(
      padding: const EdgeInsets.all(16),
      itemCount: _questions.length + (_hasMore ? 1 : 0),
      itemBuilder: (context, index) {
        if (index == _questions.length) {
          return Padding(
            padding: const EdgeInsets.symmetric(vertical: 8),
            child: Center(
              child: _loadingMore
                  ? const CircularProgressIndicator()
                  : OutlinedButton(onPressed: _loadMore, child: const Text("আরো প্রশ্ন দেখুন")),
            ),
          );
        }
        return _QuestionCard(question: _questions[index], index: index + 1);
      },
    );
  }
}

class _QuestionCard extends StatefulWidget {
  final ExamQuestion question;
  final int index;
  const _QuestionCard({required this.question, required this.index});

  @override
  State<_QuestionCard> createState() => _QuestionCardState();
}

class _QuestionCardState extends State<_QuestionCard> {
  bool _showAnswer = false;

  @override
  Widget build(BuildContext context) {
    final q = widget.question;
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      elevation: 0,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
        side: BorderSide(color: Colors.grey.shade200),
      ),
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            if (q.examName != null || q.examYear != null)
              Padding(
                padding: const EdgeInsets.only(bottom: 6),
                child: Text(
                  [q.examName, q.examYear?.toString()].where((s) => s != null).join(' • '),
                  style: TextStyle(fontSize: 12, color: Colors.grey.shade600),
                ),
              ),
            Text(
              "${widget.index}. ${q.questionText}",
              style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w500),
            ),
            const SizedBox(height: 10),
            ...q.options.map((opt) {
              final isCorrect = _showAnswer && opt.key == q.correctAnswer;
              return Padding(
                padding: const EdgeInsets.symmetric(vertical: 3),
                child: Row(
                  children: [
                    CircleAvatar(
                      radius: 12,
                      backgroundColor: isCorrect ? Colors.green : Colors.grey.shade200,
                      child: Text(
                        opt.key,
                        style: TextStyle(
                          fontSize: 11,
                          color: isCorrect ? Colors.white : Colors.black87,
                        ),
                      ),
                    ),
                    const SizedBox(width: 10),
                    Expanded(
                      child: Text(
                        opt.value,
                        style: TextStyle(
                          fontWeight: isCorrect ? FontWeight.bold : FontWeight.normal,
                          color: isCorrect ? Colors.green.shade800 : Colors.black87,
                        ),
                      ),
                    ),
                  ],
                ),
              );
            }),
            const SizedBox(height: 6),
            if (!_showAnswer)
              TextButton(
                onPressed: () => setState(() => _showAnswer = true),
                child: const Text("উত্তর দেখুন"),
              )
            else if (q.explanation != null && q.explanation!.isNotEmpty)
              Container(
                margin: const EdgeInsets.only(top: 4),
                padding: const EdgeInsets.all(10),
                decoration: BoxDecoration(
                  color: Colors.green.shade50,
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Text(
                  "ব্যাখ্যা: ${q.explanation}",
                  style: TextStyle(fontSize: 13, color: Colors.green.shade900),
                ),
              ),
          ],
        ),
      ),
    );
  }
}

class _StudyMaterialTab extends StatefulWidget {
  final Subject subject;
  const _StudyMaterialTab({required this.subject});

  @override
  State<_StudyMaterialTab> createState() => _StudyMaterialTabState();
}

class _StudyMaterialTabState extends State<_StudyMaterialTab> {
  final _api = ApiService();
  List<StudyMaterial> _materials = [];
  bool _loading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final result = await _api.getStudyMaterials(subjectId: widget.subject.id);
      setState(() => _materials = result);
    } catch (e) {
      setState(() => _error = e.toString());
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_loading) return const Center(child: CircularProgressIndicator());
    if (_error != null) {
      return Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(_error!),
            const SizedBox(height: 8),
            OutlinedButton(onPressed: _load, child: const Text("আবার চেষ্টা করুন")),
          ],
        ),
      );
    }
    if (_materials.isEmpty) {
      return const Center(child: Text("এই বিষয়ে এখনো কোনো পড়ার উপকরণ যোগ করা হয়নি"));
    }
    return ListView.builder(
      padding: const EdgeInsets.all(16),
      itemCount: _materials.length,
      itemBuilder: (context, index) => _StudyMaterialCard(
        material: _materials[index],
        subjectName: widget.subject.name,
      ),
    );
  }
}

class _StudyMaterialCard extends StatelessWidget {
  final StudyMaterial material;
  final String subjectName;
  const _StudyMaterialCard({required this.material, required this.subjectName});

  @override
  Widget build(BuildContext context) {
    final tags = material.tags;

    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      elevation: 0,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
        side: BorderSide(color: Colors.grey.shade200),
      ),
      child: InkWell(
        borderRadius: BorderRadius.circular(12),
        onTap: () => Navigator.push(
          context,
          MaterialPageRoute(
            builder: (_) => StudyMaterialDetailScreen(material: material, subjectName: subjectName),
          ),
        ),
        child: Padding(
          padding: const EdgeInsets.all(14),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Expanded(
                    child: Text(
                      material.title,
                      style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w600),
                    ),
                  ),
                  const Icon(Icons.chevron_right_rounded, color: Colors.grey),
                ],
              ),
              const SizedBox(height: 6),
              // পুরো লেখা ডিটেইল স্ক্রিনে, এখানে শুধু প্রিভিউ
              Text(
                material.content,
                maxLines: 2,
                overflow: TextOverflow.ellipsis,
                style: TextStyle(fontSize: 13, color: Colors.grey.shade700),
              ),
              if (tags.isNotEmpty) ...[
                const SizedBox(height: 8),
                Wrap(
                  spacing: 6,
                  runSpacing: 6,
                  children: tags
                      .map((tag) => Chip(
                            label: Text(tag, style: const TextStyle(fontSize: 11)),
                            padding: EdgeInsets.zero,
                            visualDensity: VisualDensity.compact,
                            materialTapTargetSize: MaterialTapTargetSize.shrinkWrap,
                            backgroundColor: Colors.grey.shade100,
                          ))
                      .toList(),
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }
}
