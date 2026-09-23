import 'package:flutter/material.dart';
import '../models/question_models.dart';

/// একটা স্টাডি ম্যাটেরিয়াল পূর্ণ পৃষ্ঠায় পড়ার স্ক্রিন।
/// লেখা বড় হলে ExpansionTile-এ পড়া অসুবিধাজনক, তাই আলাদা স্ক্রিন।
class StudyMaterialDetailScreen extends StatefulWidget {
  final StudyMaterial material;
  final String subjectName;

  const StudyMaterialDetailScreen({
    super.key,
    required this.material,
    required this.subjectName,
  });

  @override
  State<StudyMaterialDetailScreen> createState() => _StudyMaterialDetailScreenState();
}

class _StudyMaterialDetailScreenState extends State<StudyMaterialDetailScreen> {
  // পড়ার সুবিধার জন্য ফন্ট সাইজ বাড়ানো/কমানো যায়
  double _fontSize = 16;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final m = widget.material;

    return Scaffold(
      appBar: AppBar(
        title: Text(widget.subjectName, overflow: TextOverflow.ellipsis),
        actions: [
          IconButton(
            tooltip: "লেখা ছোট করুন",
            icon: const Icon(Icons.text_decrease_rounded),
            onPressed: _fontSize > 12 ? () => setState(() => _fontSize -= 2) : null,
          ),
          IconButton(
            tooltip: "লেখা বড় করুন",
            icon: const Icon(Icons.text_increase_rounded),
            onPressed: _fontSize < 26 ? () => setState(() => _fontSize += 2) : null,
          ),
        ],
      ),
      body: Center(
        // ডেস্কটপ/চওড়া স্ক্রিনে লাইন খুব লম্বা না হওয়ার জন্য সর্বোচ্চ প্রস্থ সীমিত
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 760),
          child: ListView(
            padding: const EdgeInsets.fromLTRB(20, 16, 20, 32),
            children: [
              Text(
                m.title,
                style: theme.textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.bold),
              ),
              if (m.tags.isNotEmpty) ...[
                const SizedBox(height: 10),
                Wrap(
                  spacing: 6,
                  runSpacing: 6,
                  children: m.tags
                      .map((tag) => Chip(
                            label: Text(tag, style: const TextStyle(fontSize: 12)),
                            visualDensity: VisualDensity.compact,
                            backgroundColor: theme.colorScheme.primary.withValues(alpha: 0.08),
                            side: BorderSide.none,
                          ))
                      .toList(),
                ),
              ],
              const Divider(height: 32),
              SelectableText(
                m.content,
                style: TextStyle(fontSize: _fontSize, height: 1.7),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
