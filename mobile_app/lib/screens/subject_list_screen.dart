import 'package:flutter/material.dart';
import '../models/question_models.dart';
import '../services/api_service.dart';
import 'question_list_screen.dart';

class SubjectListScreen extends StatefulWidget {
  const SubjectListScreen({super.key});

  @override
  State<SubjectListScreen> createState() => _SubjectListScreenState();
}

class _SubjectListScreenState extends State<SubjectListScreen> {
  final _api = ApiService();
  List<Subject> _subjects = [];
  bool _loading = true;
  String? _error;

  // subject নামের মধ্যে keyword খুঁজে আইকন বাছাই (নাম হুবহু না মিললেও কাজ করে,
  // যেমন "বাংলা ব্যাকরণ ও সাহিত্য")। ক্রম গুরুত্বপূর্ণ - আগে যেটা মেলে সেটাই নেওয়া হয়।
  static const _iconKeywords = <String, IconData>{
    'আন্তর্জাতিক': Icons.public_rounded,
    'কম্পিউটার': Icons.computer_rounded,
    'বাংলা ব্যাকরণ': Icons.menu_book_rounded,
    'ইংরেজি': Icons.language_rounded,
    'গণিত': Icons.calculate_rounded,
    'সাধারণ জ্ঞান': Icons.flag_rounded,
    'বিজ্ঞান': Icons.science_rounded,
    'বাংলা': Icons.menu_book_rounded,
  };

  IconData _iconFor(String name) {
    for (final entry in _iconKeywords.entries) {
      if (name.contains(entry.key)) return entry.value;
    }
    return Icons.book_outlined;
  }

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
      final result = await _api.getSubjects();
      setState(() => _subjects = result);
    } catch (e) {
      setState(() => _error = e.toString().replaceFirst('Exception: ', ''));
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text("প্রশ্নব্যাংক ও স্টাডি")),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : _error != null
              ? Center(
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Text(_error!),
                      const SizedBox(height: 8),
                      OutlinedButton(onPressed: _load, child: const Text("আবার চেষ্টা করুন")),
                    ],
                  ),
                )
              : _subjects.isEmpty
                  ? const Center(child: Text("এখনো কোনো বিষয় যোগ করা হয়নি"))
                  : GridView.builder(
                      padding: const EdgeInsets.all(16),
                      gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                        crossAxisCount: 2,
                        mainAxisSpacing: 12,
                        crossAxisSpacing: 12,
                        childAspectRatio: 1.3,
                      ),
                      itemCount: _subjects.length,
                      itemBuilder: (context, index) {
                        final subject = _subjects[index];
                        return _SubjectCard(
                          subject: subject,
                          icon: _iconFor(subject.name),
                          onTap: () => Navigator.push(
                            context,
                            MaterialPageRoute(
                              builder: (_) => QuestionListScreen(subject: subject),
                            ),
                          ),
                        );
                      },
                    ),
    );
  }
}

class _SubjectCard extends StatelessWidget {
  final Subject subject;
  final IconData icon;
  final VoidCallback onTap;

  const _SubjectCard({required this.subject, required this.icon, required this.onTap});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Card(
      elevation: 0,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(14),
        side: BorderSide(color: Colors.grey.shade200),
      ),
      child: InkWell(
        borderRadius: BorderRadius.circular(14),
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.all(14),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(icon, color: theme.colorScheme.primary, size: 28),
              const SizedBox(height: 10),
              Text(
                subject.name,
                maxLines: 3,
                overflow: TextOverflow.ellipsis,
                style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 14, height: 1.3),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
