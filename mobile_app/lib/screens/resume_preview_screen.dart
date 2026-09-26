import 'package:flutter/material.dart';
import 'package:printing/printing.dart';
import '../models/resume_models.dart';
import '../services/api_service.dart';

class ResumePreviewScreen extends StatefulWidget {
  final ResumeResult result;
  const ResumePreviewScreen({super.key, required this.result});

  @override
  State<ResumePreviewScreen> createState() => _ResumePreviewScreenState();
}

class _ResumePreviewScreenState extends State<ResumePreviewScreen> {
  final _api = ApiService();
  bool _exporting = false;

  // PDF ব্যাকএন্ড থেকে আনা হয় — Flutter-এর pdf প্যাকেজে বাংলা যুক্তাক্ষর ভেঙে যায়
  Future<void> _exportPdf() async {
    if (_exporting) return;
    setState(() => _exporting = true);
    try {
      final bytes = await _api.exportResumePdf(widget.result.resumeText);
      await Printing.layoutPdf(onLayout: (_) async => bytes, name: 'resume.pdf');
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(e.toString().replaceFirst('Exception: ', ''))),
      );
    } finally {
      if (mounted) setState(() => _exporting = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final result = widget.result;
    return Scaffold(
      appBar: AppBar(
        title: const Text("আপনার রিজিউম"),
        actions: [
          IconButton(
            onPressed: _exporting ? null : _exportPdf,
            icon: const Icon(Icons.picture_as_pdf_outlined),
            tooltip: "PDF ডাউনলোড",
          ),
        ],
      ),
      body: ListView(
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
              result.resumeText,
              style: const TextStyle(fontSize: 14, height: 1.6),
            ),
          ),
          const SizedBox(height: 20),
          const Text(
            "ATS Score বাড়ানোর টিপস",
            style: TextStyle(fontWeight: FontWeight.bold, fontSize: 15),
          ),
          const SizedBox(height: 8),
          ...result.atsTips.map(
            (tip) => Padding(
              padding: const EdgeInsets.only(bottom: 6),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Icon(Icons.check_circle_outline, size: 18, color: Colors.green),
                  const SizedBox(width: 8),
                  Expanded(child: Text(tip)),
                ],
              ),
            ),
          ),
          const SizedBox(height: 24),
          FilledButton.icon(
            onPressed: _exporting ? null : _exportPdf,
            icon: _exporting
                ? const SizedBox(
                    width: 18,
                    height: 18,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  )
                : const Icon(Icons.download_rounded),
            label: Text(_exporting ? "PDF তৈরি হচ্ছে..." : "PDF হিসেবে ডাউনলোড করুন"),
            style: FilledButton.styleFrom(minimumSize: const Size.fromHeight(50)),
          ),
        ],
      ),
    );
  }
}
