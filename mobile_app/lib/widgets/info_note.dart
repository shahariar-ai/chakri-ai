import 'package:flutter/material.dart';

/// ছোট তথ্য/সতর্কতা বক্স (disclaimer, সোর্স উল্লেখ ইত্যাদির জন্য)
class InfoNote extends StatelessWidget {
  final String text;
  final IconData icon;
  const InfoNote(this.text, {super.key, this.icon = Icons.info_outline_rounded});

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.fromLTRB(16, 4, 16, 8),
      padding: const EdgeInsets.all(10),
      decoration: BoxDecoration(
        color: const Color(0xFFFFF8E1),
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: const Color(0xFFFFE082)),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(icon, size: 18, color: Colors.orange.shade800),
          const SizedBox(width: 8),
          Expanded(child: Text(text, style: const TextStyle(fontSize: 12.5, height: 1.4))),
        ],
      ),
    );
  }
}
