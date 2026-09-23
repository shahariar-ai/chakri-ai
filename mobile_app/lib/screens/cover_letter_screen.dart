import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../services/api_service.dart';

/// AI কভার লেটার জেনারেটর।
/// সার্কুলার ডিটেইল স্ক্রিন থেকে এলে কোম্পানি/পদ/জব ডেসক্রিপশন আগে থেকে ভরা থাকে।
class CoverLetterScreen extends StatefulWidget {
  final String? initialCompany;
  final String? initialPosition;
  final String? initialJobDescription;

  const CoverLetterScreen({
    super.key,
    this.initialCompany,
    this.initialPosition,
    this.initialJobDescription,
  });

  @override
  State<CoverLetterScreen> createState() => _CoverLetterScreenState();
}

class _CoverLetterScreenState extends State<CoverLetterScreen> {
  final _formKey = GlobalKey<FormState>();
  final _api = ApiService();

  late final _companyController = TextEditingController(text: widget.initialCompany);
  late final _positionController = TextEditingController(text: widget.initialPosition);
  late final _jobDescController = TextEditingController(text: widget.initialJobDescription);
  final _resumeSummaryController = TextEditingController();

  String _language = "bn";
  bool _loading = false;
  String? _result;

  @override
  void dispose() {
    _companyController.dispose();
    _positionController.dispose();
    _jobDescController.dispose();
    _resumeSummaryController.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;
    FocusScope.of(context).unfocus();

    setState(() => _loading = true);
    try {
      final letter = await _api.generateCoverLetter(
        resumeSummary: _resumeSummaryController.text.trim(),
        jobDescription: _jobDescController.text.trim(),
        companyName: _companyController.text.trim(),
        targetPosition: _positionController.text.trim(),
        language: _language,
      );
      if (!mounted) return;
      setState(() => _result = letter);
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text("ত্রুটি: ${e.toString().replaceFirst('Exception: ', '')}")),
      );
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _copy() async {
    await Clipboard.setData(ClipboardData(text: _result ?? ''));
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text("কভার লেটার কপি করা হয়েছে")),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text("কভার লেটার জেনারেটর")),
      body: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 760),
          child: _result == null ? _buildForm() : _buildResult(),
        ),
      ),
    );
  }

  Widget _buildForm() {
    return Form(
      key: _formKey,
      child: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          _field(_companyController, "প্রতিষ্ঠানের নাম", required: true),
          _field(_positionController, "যে পদে আবেদন করছেন", required: true),
          _field(
            _jobDescController,
            "জব ডেসক্রিপশন / সার্কুলারের চাহিদা",
            hint: "সার্কুলারে যোগ্যতা, দায়িত্ব যা লেখা আছে তা এখানে দিন",
            maxLines: 5,
            required: true,
          ),
          _field(
            _resumeSummaryController,
            "আপনার সংক্ষিপ্ত পরিচিতি",
            hint: "যেমন: BSc in CSE (2022), ২ বছর Python ডেভেলপার হিসেবে অভিজ্ঞতা, MS Excel-এ দক্ষ",
            maxLines: 4,
            required: true,
          ),
          const SizedBox(height: 4),
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
          const SizedBox(height: 24),
          FilledButton.icon(
            onPressed: _loading ? null : _submit,
            icon: _loading
                ? const SizedBox(
                    width: 18,
                    height: 18,
                    child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                  )
                : const Icon(Icons.auto_awesome),
            label: Text(_loading ? "তৈরি হচ্ছে..." : "AI দিয়ে কভার লেটার তৈরি করুন"),
            style: FilledButton.styleFrom(minimumSize: const Size.fromHeight(50)),
          ),
        ],
      ),
    );
  }

  Widget _buildResult() {
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        Container(
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(12),
            border: Border.all(color: Colors.grey.shade200),
          ),
          child: SelectableText(
            _result!,
            style: const TextStyle(fontSize: 15, height: 1.7),
          ),
        ),
        const SizedBox(height: 16),
        FilledButton.icon(
          onPressed: _copy,
          icon: const Icon(Icons.copy_rounded),
          label: const Text("কপি করুন"),
          style: FilledButton.styleFrom(minimumSize: const Size.fromHeight(48)),
        ),
        const SizedBox(height: 8),
        // ফর্মের তথ্য রেখে দেওয়া হয় যাতে একটু বদলে আবার জেনারেট করা যায়
        OutlinedButton.icon(
          onPressed: () => setState(() => _result = null),
          icon: const Icon(Icons.edit_outlined),
          label: const Text("তথ্য বদলে আবার তৈরি করুন"),
          style: OutlinedButton.styleFrom(minimumSize: const Size.fromHeight(48)),
        ),
      ],
    );
  }

  Widget _field(
    TextEditingController controller,
    String label, {
    String? hint,
    int maxLines = 1,
    bool required = false,
  }) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: TextFormField(
        controller: controller,
        maxLines: maxLines,
        decoration: InputDecoration(
          labelText: label,
          hintText: hint,
          border: const OutlineInputBorder(),
          alignLabelWithHint: maxLines > 1,
        ),
        validator: required
            ? (v) => (v == null || v.trim().isEmpty) ? "এই তথ্যটি দিতে হবে" : null
            : null,
      ),
    );
  }
}
