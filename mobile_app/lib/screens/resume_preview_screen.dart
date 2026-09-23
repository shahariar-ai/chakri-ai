import 'package:flutter/material.dart';
import 'package:pdf/pdf.dart';
import 'package:pdf/widgets.dart' as pw;
import 'package:printing/printing.dart';
import '../models/resume_models.dart';

class ResumePreviewScreen extends StatelessWidget {
  final ResumeResult result;
  const ResumePreviewScreen({super.key, required this.result});

  Future<void> _exportPdf() async {
    final doc = pw.Document();
    doc.addPage(
      pw.Page(
        pageFormat: PdfPageFormat.a4,
        build: (context) => pw.Padding(
          padding: const pw.EdgeInsets.all(24),
          child: pw.Text(
            result.resumeText,
            style: const pw.TextStyle(fontSize: 11, lineSpacing: 3),
          ),
        ),
      ),
    );
    await Printing.layoutPdf(onLayout: (format) async => doc.save());
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text("আপনার রিজিউম"),
        actions: [
          IconButton(
            onPressed: _exportPdf,
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
            onPressed: _exportPdf,
            icon: const Icon(Icons.download_rounded),
            label: const Text("PDF হিসেবে ডাউনলোড করুন"),
            style: FilledButton.styleFrom(minimumSize: const Size.fromHeight(50)),
          ),
        ],
      ),
    );
  }
}
