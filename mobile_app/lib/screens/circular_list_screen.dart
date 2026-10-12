import 'package:flutter/material.dart';
import '../widgets/info_note.dart';
import '../models/circular_models.dart';
import '../services/api_service.dart';
import 'circular_detail_screen.dart';

class CircularListScreen extends StatefulWidget {
  const CircularListScreen({super.key});

  @override
  State<CircularListScreen> createState() => _CircularListScreenState();
}

class _CircularListScreenState extends State<CircularListScreen> {
  final _api = ApiService();
  final _searchController = TextEditingController();

  List<JobCircular> _circulars = [];
  List<String> _categories = [];
  String? _selectedCategory;
  bool _loading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _loadCategories();
    _loadCirculars();
  }

  Future<void> _loadCategories() async {
    final cats = await _api.getCircularCategories();
    if (mounted) setState(() => _categories = cats);
  }

  Future<void> _loadCirculars() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final result = await _api.getCirculars(
        category: _selectedCategory,
        search: _searchController.text.trim(),
      );
      setState(() => _circulars = result);
    } catch (e) {
      setState(() => _error = e.toString().replaceFirst('Exception: ', ''));
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text("চাকরির সার্কুলার")),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 12, 16, 8),
            child: TextField(
              controller: _searchController,
              decoration: InputDecoration(
                hintText: "পদের নাম বা প্রতিষ্ঠান খুঁজুন",
                prefixIcon: const Icon(Icons.search),
                border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                filled: true,
                fillColor: Colors.white,
              ),
              onSubmitted: (_) => _loadCirculars(),
            ),
          ),
          if (_categories.isNotEmpty)
            SizedBox(
              height: 40,
              child: ListView(
                scrollDirection: Axis.horizontal,
                padding: const EdgeInsets.symmetric(horizontal: 16),
                children: [
                  _categoryChip(null, "সব"),
                  ..._categories.map((c) => _categoryChip(c, c)),
                ],
              ),
            ),
          const SizedBox(height: 8),
          const InfoNote("সার্কুলারের তথ্য সরকারি ও বেসরকারি অফিসিয়াল সাইট (যেমন bpsc.gov.bd) থেকে সংগৃহীত। আবেদনের আগে অবশ্যই মূল অফিসিয়াল বিজ্ঞপ্তি যাচাই করুন।"),
          Expanded(child: _buildBody()),
        ],
      ),
    );
  }

  Widget _categoryChip(String? value, String label) {
    final selected = _selectedCategory == value;
    return Padding(
      padding: const EdgeInsets.only(right: 8),
      child: ChoiceChip(
        label: Text(label),
        selected: selected,
        onSelected: (_) {
          setState(() => _selectedCategory = value);
          _loadCirculars();
        },
      ),
    );
  }

  Widget _buildBody() {
    if (_loading) return const Center(child: CircularProgressIndicator());

    if (_error != null) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Icon(Icons.wifi_off_rounded, size: 40, color: Colors.grey),
              const SizedBox(height: 8),
              Text(_error!, textAlign: TextAlign.center),
              const SizedBox(height: 12),
              OutlinedButton(onPressed: _loadCirculars, child: const Text("আবার চেষ্টা করুন")),
            ],
          ),
        ),
      );
    }

    if (_circulars.isEmpty) {
      return const Center(child: Text("কোনো সার্কুলার পাওয়া যায়নি"));
    }

    return RefreshIndicator(
      onRefresh: _loadCirculars,
      child: ListView.builder(
        padding: const EdgeInsets.fromLTRB(16, 0, 16, 16),
        itemCount: _circulars.length,
        itemBuilder: (context, index) => _CircularCard(circular: _circulars[index]),
      ),
    );
  }
}

class _CircularCard extends StatelessWidget {
  final JobCircular circular;
  const _CircularCard({required this.circular});

  @override
  Widget build(BuildContext context) {
    final daysLeft = circular.daysLeft;
    Color badgeColor = Colors.grey;
    String? badgeText;
    if (daysLeft != null) {
      if (daysLeft < 0) {
        badgeColor = Colors.grey;
        badgeText = "মেয়াদ শেষ";
      } else if (daysLeft <= 3) {
        badgeColor = Colors.red;
        badgeText = "আর $daysLeft দিন বাকি";
      } else {
        badgeColor = Colors.green;
        badgeText = "আর $daysLeft দিন বাকি";
      }
    }

    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      elevation: 0,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(14),
        side: BorderSide(color: Colors.grey.shade200),
      ),
      child: InkWell(
        borderRadius: BorderRadius.circular(14),
        onTap: () => Navigator.push(
          context,
          MaterialPageRoute(builder: (_) => CircularDetailScreen(circularId: circular.id)),
        ),
        child: Padding(
          padding: const EdgeInsets.all(14),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              if (circular.category != null)
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                  decoration: BoxDecoration(
                    color: Colors.blue.shade50,
                    borderRadius: BorderRadius.circular(6),
                  ),
                  child: Text(
                    circular.category!,
                    style: TextStyle(fontSize: 11, color: Colors.blue.shade700),
                  ),
                ),
              const SizedBox(height: 6),
              Text(
                circular.title,
                style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 15),
                maxLines: 2,
                overflow: TextOverflow.ellipsis,
              ),
              if (circular.organization?.name != null) ...[
                const SizedBox(height: 4),
                Text(
                  circular.organization!.name,
                  style: const TextStyle(color: Colors.black54, fontSize: 13),
                ),
              ],
              if (badgeText != null) ...[
                const SizedBox(height: 8),
                Row(
                  children: [
                    Icon(Icons.access_time_rounded, size: 14, color: badgeColor),
                    const SizedBox(width: 4),
                    Text(badgeText, style: TextStyle(fontSize: 12, color: badgeColor)),
                  ],
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }
}
