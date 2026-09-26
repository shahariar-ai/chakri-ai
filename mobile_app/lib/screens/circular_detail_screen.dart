import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';
import 'cover_letter_screen.dart';
import 'job_match_screen.dart';
import '../models/circular_models.dart';
import '../services/api_service.dart';

class CircularDetailScreen extends StatefulWidget {
  final int circularId;
  const CircularDetailScreen({super.key, required this.circularId});

  @override
  State<CircularDetailScreen> createState() => _CircularDetailScreenState();
}

class _CircularDetailScreenState extends State<CircularDetailScreen> {
  final _api = ApiService();
  JobCircular? _circular;
  bool _loading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    try {
      final result = await _api.getCircularDetail(widget.circularId);
      setState(() => _circular = result);
    } catch (e) {
      setState(() => _error = e.toString());
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _openSource() async {
    final url = _circular?.sourceUrl;
    if (url == null) return;
    final uri = Uri.parse(url);
    if (await canLaunchUrl(uri)) {
      await launchUrl(uri, mode: LaunchMode.externalApplication);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text("সার্কুলার বিস্তারিত")),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : _error != null
              ? Center(child: Text(_error!))
              : _buildDetail(),
    );
  }

  Widget _buildDetail() {
    final c = _circular!;
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        Text(c.title, style: const TextStyle(fontSize: 19, fontWeight: FontWeight.bold)),
        const SizedBox(height: 8),
        if (c.organization != null)
          Text(c.organization!.name, style: const TextStyle(fontSize: 15, color: Colors.black54)),
        const SizedBox(height: 16),
        _infoCard([
          if (c.postNames != null) _infoRow("পদের নাম", c.postNames!),
          if (c.vacancyCount != null) _infoRow("পদ সংখ্যা", c.vacancyCount!),
          if (c.qualification != null) _infoRow("যোগ্যতা", c.qualification!),
          if (c.ageLimit != null) _infoRow("বয়সসীমা", c.ageLimit!),
          if (c.salaryRange != null) _infoRow("বেতন", c.salaryRange!),
          if (c.applicationDeadline != null)
            _infoRow(
              "আবেদনের শেষ তারিখ",
              "${c.applicationDeadline!.day}/${c.applicationDeadline!.month}/${c.applicationDeadline!.year}",
              highlight: true,
            ),
          if (c.examDate != null)
            _infoRow(
              "পরীক্ষার তারিখ",
              "${c.examDate!.day}/${c.examDate!.month}/${c.examDate!.year}",
            ),
        ]),
        const SizedBox(height: 20),
        if (c.sourceUrl != null)
          FilledButton.icon(
            onPressed: _openSource,
            icon: const Icon(Icons.open_in_new_rounded),
            label: const Text("মূল সার্কুলার দেখুন"),
            style: FilledButton.styleFrom(minimumSize: const Size.fromHeight(48)),
          ),
        const SizedBox(height: 10),
        OutlinedButton.icon(
          onPressed: () => _openCoverLetter(c),
          icon: const Icon(Icons.mail_outline),
          label: const Text("এই পদের জন্য কভার লেটার লিখুন"),
          style: OutlinedButton.styleFrom(minimumSize: const Size.fromHeight(48)),
        ),
        const SizedBox(height: 10),
        OutlinedButton.icon(
          onPressed: () => Navigator.push(
            context,
            MaterialPageRoute(
              builder: (_) => JobMatchScreen(circularId: c.id, circularTitle: c.title),
            ),
          ),
          icon: const Icon(Icons.analytics_outlined),
          label: const Text("আমি কতটা উপযুক্ত? (স্কিল গ্যাপ)"),
          style: OutlinedButton.styleFrom(minimumSize: const Size.fromHeight(48)),
        ),
      ],
    );
  }

  // সার্কুলারের তথ্য দিয়ে কভার লেটার ফর্ম আগে থেকে ভরে দেওয়া
  void _openCoverLetter(JobCircular c) {
    final jobDesc = [
      if (c.postNames != null) "পদ: ${c.postNames}",
      if (c.qualification != null) "যোগ্যতা: ${c.qualification}",
      if (c.ageLimit != null) "বয়সসীমা: ${c.ageLimit}",
      if (c.salaryRange != null) "বেতন: ${c.salaryRange}",
    ].join("\n");
    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (_) => CoverLetterScreen(
          initialCompany: c.organization?.nameBn ?? c.organization?.name,
          initialPosition: c.postNames ?? c.title,
          initialJobDescription: jobDesc.isEmpty ? c.title : jobDesc,
        ),
      ),
    );
  }

  Widget _infoCard(List<Widget> rows) {
    final filtered = rows.where((w) => w is! SizedBox).toList();
    if (filtered.isEmpty) return const SizedBox.shrink();
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: Colors.grey.shade200),
      ),
      child: Column(children: filtered),
    );
  }

  Widget _infoRow(String label, String value, {bool highlight = false}) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 130,
            child: Text(label, style: const TextStyle(color: Colors.black54, fontSize: 13)),
          ),
          Expanded(
            child: Text(
              value,
              style: TextStyle(
                fontSize: 14,
                fontWeight: highlight ? FontWeight.bold : FontWeight.normal,
                color: highlight ? Colors.red : Colors.black87,
              ),
            ),
          ),
        ],
      ),
    );
  }
}
