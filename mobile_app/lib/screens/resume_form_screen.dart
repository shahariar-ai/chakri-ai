import 'package:flutter/material.dart';
import '../models/resume_models.dart';
import '../services/api_service.dart';
import 'resume_preview_screen.dart';

class ResumeFormScreen extends StatefulWidget {
  const ResumeFormScreen({super.key});

  @override
  State<ResumeFormScreen> createState() => _ResumeFormScreenState();
}

class _ResumeFormScreenState extends State<ResumeFormScreen> {
  final _formKey = GlobalKey<FormState>();
  final _data = ResumeFormData();
  final _api = ApiService();

  final _skillsController = TextEditingController();
  bool _loading = false;

  // ডাইনামিক এডুকেশন/এক্সপেরিয়েন্স এন্ট্রির জন্য কন্ট্রোলার গ্রুপ
  final List<Map<String, TextEditingController>> _eduControllers = [];
  final List<Map<String, TextEditingController>> _expControllers = [];

  @override
  void initState() {
    super.initState();
    _addEducation();
  }

  void _addEducation() {
    setState(() {
      _eduControllers.add({
        "institution": TextEditingController(),
        "degree": TextEditingController(),
        "field": TextEditingController(),
        "passingYear": TextEditingController(),
        "result": TextEditingController(),
      });
    });
  }

  void _addExperience() {
    setState(() {
      _expControllers.add({
        "company": TextEditingController(),
        "position": TextEditingController(),
        "duration": TextEditingController(),
        "responsibilities": TextEditingController(),
      });
    });
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;
    _formKey.currentState!.save();

    _data.education = _eduControllers
        .where((c) => c["institution"]!.text.isNotEmpty)
        .map((c) => Education(
              institution: c["institution"]!.text,
              degree: c["degree"]!.text,
              field: c["field"]!.text,
              passingYear: c["passingYear"]!.text,
              result: c["result"]!.text,
            ))
        .toList();

    _data.experience = _expControllers
        .where((c) => c["company"]!.text.isNotEmpty)
        .map((c) => WorkExperience(
              company: c["company"]!.text,
              position: c["position"]!.text,
              duration: c["duration"]!.text,
              responsibilities: c["responsibilities"]!.text,
            ))
        .toList();

    _data.skills = _skillsController.text
        .split(',')
        .map((s) => s.trim())
        .where((s) => s.isNotEmpty)
        .toList();

    if (_data.education.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text("অন্তত একটি শিক্ষাগত যোগ্যতা দিন")),
      );
      return;
    }

    setState(() => _loading = true);
    try {
      final result = await _api.generateResume(_data);
      if (!mounted) return;
      Navigator.push(
        context,
        MaterialPageRoute(builder: (_) => ResumePreviewScreen(result: result)),
      );
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text("ত্রুটি: ${e.toString()}")),
      );
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text("রিজিউম তথ্য দিন")),
      body: Form(
        key: _formKey,
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            _sectionTitle("ব্যক্তিগত তথ্য"),
            _textField("পুরো নাম", (v) => _data.fullName = v ?? '', required: true),
            _textField("ইমেইল", (v) => _data.email = v ?? '', required: true),
            _textField("ফোন নম্বর", (v) => _data.phone = v ?? '', required: true),
            _textField("ঠিকানা (ঐচ্ছিক)", (v) => _data.address = v ?? ''),
            _textField(
              "টার্গেট পদ (যে চাকরির জন্য আবেদন করছেন)",
              (v) => _data.targetPosition = v ?? '',
              required: true,
            ),
            _textField(
              "নিজের সম্পর্কে সংক্ষেপে (ঐচ্ছিক)",
              (v) => _data.summaryPoints = v ?? '',
              maxLines: 3,
            ),
            const SizedBox(height: 12),
            _sectionTitle("শিক্ষাগত যোগ্যতা"),
            ..._eduControllers.asMap().entries.map((e) => _educationBlock(e.key, e.value)),
            TextButton.icon(
              onPressed: _addEducation,
              icon: const Icon(Icons.add),
              label: const Text("আরেকটি শিক্ষাগত যোগ্যতা যোগ করুন"),
            ),
            const SizedBox(height: 12),
            _sectionTitle("কর্ম অভিজ্ঞতা (থাকলে)"),
            ..._expControllers.asMap().entries.map((e) => _experienceBlock(e.key, e.value)),
            TextButton.icon(
              onPressed: _addExperience,
              icon: const Icon(Icons.add),
              label: const Text("অভিজ্ঞতা যোগ করুন"),
            ),
            const SizedBox(height: 12),
            _sectionTitle("স্কিল"),
            TextFormField(
              controller: _skillsController,
              decoration: const InputDecoration(
                hintText: "যেমন: Python, MS Excel, যোগাযোগ দক্ষতা (কমা দিয়ে আলাদা করুন)",
                border: OutlineInputBorder(),
              ),
              maxLines: 2,
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
              label: Text(_loading ? "তৈরি হচ্ছে..." : "AI দিয়ে রিজিউম তৈরি করুন"),
              style: FilledButton.styleFrom(
                minimumSize: const Size.fromHeight(50),
              ),
            ),
            const SizedBox(height: 24),
          ],
        ),
      ),
    );
  }

  Widget _sectionTitle(String text) => Padding(
        padding: const EdgeInsets.symmetric(vertical: 10),
        child: Text(
          text,
          style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
        ),
      );

  Widget _textField(
    String label,
    void Function(String?) onSaved, {
    bool required = false,
    int maxLines = 1,
  }) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: TextFormField(
        maxLines: maxLines,
        decoration: InputDecoration(
          labelText: label,
          border: const OutlineInputBorder(),
        ),
        validator: required
            ? (v) => (v == null || v.trim().isEmpty) ? "এই তথ্যটি দিতে হবে" : null
            : null,
        onSaved: onSaved,
      ),
    );
  }

  Widget _educationBlock(int index, Map<String, TextEditingController> c) {
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          children: [
            TextFormField(
              controller: c["institution"],
              decoration: const InputDecoration(labelText: "প্রতিষ্ঠানের নাম"),
            ),
            TextFormField(
              controller: c["degree"],
              decoration: const InputDecoration(labelText: "ডিগ্রি (যেমন: BSc, HSC)"),
            ),
            TextFormField(
              controller: c["field"],
              decoration: const InputDecoration(labelText: "বিষয়"),
            ),
            Row(
              children: [
                Expanded(
                  child: TextFormField(
                    controller: c["passingYear"],
                    decoration: const InputDecoration(labelText: "পাসের বছর"),
                  ),
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: TextFormField(
                    controller: c["result"],
                    decoration: const InputDecoration(labelText: "রেজাল্ট (ঐচ্ছিক)"),
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _experienceBlock(int index, Map<String, TextEditingController> c) {
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          children: [
            TextFormField(
              controller: c["company"],
              decoration: const InputDecoration(labelText: "কোম্পানির নাম"),
            ),
            TextFormField(
              controller: c["position"],
              decoration: const InputDecoration(labelText: "পদবি"),
            ),
            TextFormField(
              controller: c["duration"],
              decoration: const InputDecoration(labelText: "সময়কাল (যেমন: জান ২০২৩ - বর্তমান)"),
            ),
            TextFormField(
              controller: c["responsibilities"],
              decoration: const InputDecoration(labelText: "দায়িত্ব ও অর্জন"),
              maxLines: 3,
            ),
          ],
        ),
      ),
    );
  }
}
