import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';
import '../models/payment_models.dart';
import '../services/api_service.dart';
import '../services/subscriber_id.dart';

/// প্রিমিয়াম সাবস্ক্রিপশন কেনার স্ক্রিন।
/// পেমেন্ট ফ্লো: প্ল্যান + প্রোভাইডার বাছাই -> ব্রাউজারে bKash পেজ -> অ্যাপে ফিরলে স্ট্যাটাস চেক।
class PremiumScreen extends StatefulWidget {
  /// টেস্টে ব্রাউজার খোলার বদলে অন্য কিছু করতে চাইলে
  final Future<bool> Function(Uri url)? launcher;
  final String? subscriberIdOverride;

  const PremiumScreen({super.key, this.launcher, this.subscriberIdOverride});

  @override
  State<PremiumScreen> createState() => _PremiumScreenState();
}

class _PremiumScreenState extends State<PremiumScreen> with WidgetsBindingObserver {
  final _api = ApiService();

  String? _subscriberId;
  PlansInfo? _plans;
  SubscriptionStatus? _status;
  String? _error;
  bool _loading = true;

  String? _selectedPlan;
  String? _selectedProvider;
  int? _pendingPaymentId; // ব্রাউজারে পাঠানো পেমেন্ট, যার ফলাফল এখনো জানা নেই
  bool _busy = false;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    _load();
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    super.dispose();
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    // ব্রাউজার থেকে অ্যাপে ফিরলে নিজে থেকেই পেমেন্ট চেক
    if (state == AppLifecycleState.resumed && _pendingPaymentId != null && !_busy) {
      _checkPayment();
    }
  }

  Future<void> _load() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final id = widget.subscriberIdOverride ?? await SubscriberId.get();
      final results = await Future.wait([_api.getPlans(), _api.getSubscriptionStatus(id)]);
      if (!mounted) return;
      final plans = results[0] as PlansInfo;
      setState(() {
        _subscriberId = id;
        _plans = plans;
        _status = results[1] as SubscriptionStatus;
        _selectedPlan ??= plans.plans.isNotEmpty ? plans.plans.first.code : null;
        _selectedProvider ??= plans.providers.where((p) => p.available).map((p) => p.code).firstOrNull;
      });
    } catch (e) {
      if (mounted) setState(() => _error = e.toString().replaceFirst('Exception: ', ''));
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  void _snack(String msg) => ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(msg)));

  Future<void> _pay() async {
    if (_selectedPlan == null || _selectedProvider == null) return;
    setState(() => _busy = true);
    try {
      final created = await _api.createPayment(
        subscriberId: _subscriberId!,
        planCode: _selectedPlan!,
        provider: _selectedProvider!,
      );
      final launch = widget.launcher ?? (uri) => launchUrl(uri, mode: LaunchMode.externalApplication);
      final opened = await launch(Uri.parse(created.redirectUrl));
      if (!mounted) return;
      setState(() => _pendingPaymentId = created.paymentId);
      if (!opened) _snack("পেমেন্ট পেজ খোলা যায়নি");
    } catch (e) {
      if (mounted) _snack("ত্রুটি: ${e.toString().replaceFirst('Exception: ', '')}");
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _checkPayment() async {
    final id = _pendingPaymentId;
    if (id == null) return;
    setState(() => _busy = true);
    try {
      final payment = await _api.getPayment(id, _subscriberId!);
      if (!mounted) return;
      switch (payment.status) {
        case "completed":
          setState(() => _pendingPaymentId = null);
          _snack(payment.isTest
              ? "টেস্ট পেমেন্ট সফল! প্রিমিয়াম চালু হয়েছে 🎉"
              : "পেমেন্ট সফল! প্রিমিয়াম চালু হয়েছে 🎉");
          await _load();
        case "pending":
          _snack("পেমেন্ট এখনো সম্পন্ন হয়নি। পেমেন্ট শেষ করে আবার চেক করুন।");
        default:
          setState(() => _pendingPaymentId = null);
          _snack("পেমেন্ট সম্পন্ন হয়নি (বাতিল/ব্যর্থ)। কোনো টাকা কাটা হয়নি।");
      }
    } catch (e) {
      if (mounted) _snack("ত্রুটি: ${e.toString().replaceFirst('Exception: ', '')}");
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text("প্রিমিয়াম")),
      body: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 760),
          child: _buildBody(),
        ),
      ),
    );
  }

  Widget _buildBody() {
    if (_loading) return const Center(child: CircularProgressIndicator());
    if (_error != null) {
      return Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(_error!, textAlign: TextAlign.center),
            const SizedBox(height: 12),
            OutlinedButton(onPressed: _load, child: const Text("আবার চেষ্টা করুন")),
          ],
        ),
      );
    }

    final theme = Theme.of(context);
    final plans = _plans!;
    final status = _status!;
    final testMode = plans.providers.any((p) => p.isTest);

    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        if (testMode)
          Container(
            margin: const EdgeInsets.only(bottom: 12),
            padding: const EdgeInsets.all(10),
            decoration: BoxDecoration(
              color: const Color(0xFFFFF4CE),
              borderRadius: BorderRadius.circular(8),
            ),
            child: const Text(
              "🧪 টেস্ট মোড: পেমেন্ট সিমুলেটেড, কোনো আসল টাকা কাটা হবে না।",
              style: TextStyle(color: Color(0xFF7A5B00)),
            ),
          ),
        if (status.isPremium)
          Card(
            elevation: 0,
            color: theme.colorScheme.primary.withValues(alpha: 0.08),
            child: ListTile(
              leading: Icon(Icons.workspace_premium_rounded, color: theme.colorScheme.primary),
              title: const Text("আপনি প্রিমিয়াম সদস্য", style: TextStyle(fontWeight: FontWeight.w600)),
              subtitle: Text("মেয়াদ: ${_formatDate(status.expiresAt!)} পর্যন্ত\nএখন কিনলে মেয়াদের সাথে যোগ হবে"),
              isThreeLine: true,
            ),
          )
        else
          Text(
            "প্রিমিয়াম নিয়ে সব AI ফিচার সীমাহীনভাবে ব্যবহার করুন।",
            style: theme.textTheme.bodyLarge?.copyWith(color: Colors.black54),
          ),
        const SizedBox(height: 16),
        const Text("প্ল্যান বেছে নিন", style: TextStyle(fontWeight: FontWeight.w600)),
        const SizedBox(height: 8),
        RadioGroup<String>(
          groupValue: _selectedPlan,
          onChanged: (v) => setState(() => _selectedPlan = v),
          child: Column(
            children: [
              for (final p in plans.plans)
                Card(
                  elevation: 0,
                  margin: const EdgeInsets.only(bottom: 8),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12),
                    side: BorderSide(
                      color: _selectedPlan == p.code ? theme.colorScheme.primary : Colors.grey.shade200,
                      width: _selectedPlan == p.code ? 1.5 : 1,
                    ),
                  ),
                  child: RadioListTile<String>(
                    value: p.code,
                    title: Text(p.name, style: const TextStyle(fontWeight: FontWeight.w600)),
                    subtitle: Text("${p.days} দিন"),
                    secondary: Text("৳${p.amount}", style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold)),
                  ),
                ),
            ],
          ),
        ),
        const SizedBox(height: 16),
        const Text("পেমেন্ট মাধ্যম", style: TextStyle(fontWeight: FontWeight.w600)),
        const SizedBox(height: 8),
        Wrap(
          spacing: 8,
          runSpacing: 8,
          children: [
            for (final prov in plans.providers)
              ChoiceChip(
                label: Text(!prov.available
                    ? "${prov.name} (শীঘ্রই)"
                    : prov.isTest
                        ? "${prov.name} (টেস্ট)"
                        : prov.name),
                selected: _selectedProvider == prov.code,
                onSelected: prov.available ? (_) => setState(() => _selectedProvider = prov.code) : null,
              ),
          ],
        ),
        const SizedBox(height: 24),
        if (_pendingPaymentId != null) ...[
          Text(
            "পেমেন্ট পেজে কাজ শেষ করে অ্যাপে ফিরে আসুন, তারপর নিচের বাটন চাপুন।",
            style: theme.textTheme.bodyMedium?.copyWith(color: Colors.black54),
          ),
          const SizedBox(height: 8),
          FilledButton.icon(
            onPressed: _busy ? null : _checkPayment,
            icon: const Icon(Icons.refresh_rounded),
            label: const Text("পেমেন্ট স্ট্যাটাস চেক করুন"),
            style: FilledButton.styleFrom(minimumSize: const Size.fromHeight(50)),
          ),
          const SizedBox(height: 8),
        ],
        OutlinedButton.icon(
          onPressed: (_busy || _selectedProvider == null) ? null : _pay,
          icon: const Icon(Icons.payment_rounded),
          label: Text(_selectedProvider == null ? "পেমেন্ট শীঘ্রই চালু হবে" : "পেমেন্ট করুন"),
          style: OutlinedButton.styleFrom(minimumSize: const Size.fromHeight(50)),
        ),
      ],
    );
  }

  String _formatDate(DateTime d) {
    final local = d.toLocal();
    return "${local.day.toString().padLeft(2, '0')}/${local.month.toString().padLeft(2, '0')}/${local.year}";
  }
}
