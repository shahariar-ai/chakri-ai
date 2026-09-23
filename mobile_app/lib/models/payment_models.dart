// প্রিমিয়াম সাবস্ক্রিপশন ও পেমেন্টের ডেটা মডেল (backend: /api/payments/*)

class SubscriptionPlan {
  final String code;
  final String name;
  final int amount; // টাকা
  final int days;

  SubscriptionPlan({required this.code, required this.name, required this.amount, required this.days});

  factory SubscriptionPlan.fromJson(Map<String, dynamic> json) => SubscriptionPlan(
        code: json['code'],
        name: json['name'],
        amount: json['amount'],
        days: json['days'],
      );
}

class PaymentProvider {
  final String code; // bkash | nagad
  final String name;
  final String? mode; // live | mock (টেস্ট) | null (চালু নেই)

  PaymentProvider({required this.code, required this.name, this.mode});

  bool get available => mode != null;
  bool get isTest => mode == "mock";

  factory PaymentProvider.fromJson(Map<String, dynamic> json) =>
      PaymentProvider(code: json['code'], name: json['name'], mode: json['mode']);
}

class PlansInfo {
  final List<SubscriptionPlan> plans;
  final List<PaymentProvider> providers;

  PlansInfo({required this.plans, required this.providers});

  factory PlansInfo.fromJson(Map<String, dynamic> json) => PlansInfo(
        plans: (json['plans'] as List).map((e) => SubscriptionPlan.fromJson(e)).toList(),
        providers: (json['providers'] as List).map((e) => PaymentProvider.fromJson(e)).toList(),
      );
}

class SubscriptionStatus {
  final bool isPremium;
  final String? planCode;
  final DateTime? expiresAt;

  SubscriptionStatus({required this.isPremium, this.planCode, this.expiresAt});

  factory SubscriptionStatus.fromJson(Map<String, dynamic> json) => SubscriptionStatus(
        isPremium: json['is_premium'] ?? false,
        planCode: json['plan_code'],
        expiresAt: json['expires_at'] != null ? _parseUtc(json['expires_at']) : null,
      );
}

// ব্যাকএন্ড timezone ছাড়া UTC সময় পাঠায় — 'Z' না থাকলে যোগ করে UTC হিসেবে পড়া হয়
DateTime _parseUtc(String s) =>
    DateTime.parse(s.endsWith('Z') || s.contains('+') ? s : '${s}Z');

class PaymentInfo {
  final int id;
  final String status; // pending | completed | failed | cancelled
  final String? trxId;
  final bool isTest;

  PaymentInfo({required this.id, required this.status, this.trxId, this.isTest = false});

  factory PaymentInfo.fromJson(Map<String, dynamic> json) => PaymentInfo(
        id: json['id'],
        status: json['status'],
        trxId: json['trx_id'],
        isTest: json['is_test'] ?? false,
      );
}

class PaymentCreated {
  final int paymentId;
  final String redirectUrl;

  PaymentCreated({required this.paymentId, required this.redirectUrl});

  factory PaymentCreated.fromJson(Map<String, dynamic> json) =>
      PaymentCreated(paymentId: json['payment_id'], redirectUrl: json['redirect_url']);
}
