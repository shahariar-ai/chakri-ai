class Organization {
  final int id;
  final String name;
  final String? nameBn;
  final String orgType;
  final String? website;

  Organization({
    required this.id,
    required this.name,
    this.nameBn,
    required this.orgType,
    this.website,
  });

  factory Organization.fromJson(Map<String, dynamic> json) => Organization(
        id: json['id'],
        name: json['name'] ?? '',
        nameBn: json['name_bn'],
        orgType: json['org_type'] ?? '',
        website: json['website'],
      );
}

class JobCircular {
  final int id;
  final String title;
  final String? postNames;
  final String? vacancyCount;
  final String? qualification;
  final String? ageLimit;
  final String? salaryRange;
  final DateTime? applicationDeadline;
  final DateTime? examDate;
  final String? sourceUrl;
  final String? circularImageUrl;
  final String? category;
  final bool isActive;
  final DateTime createdAt;
  final Organization? organization;

  JobCircular({
    required this.id,
    required this.title,
    this.postNames,
    this.vacancyCount,
    this.qualification,
    this.ageLimit,
    this.salaryRange,
    this.applicationDeadline,
    this.examDate,
    this.sourceUrl,
    this.circularImageUrl,
    this.category,
    required this.isActive,
    required this.createdAt,
    this.organization,
  });

  factory JobCircular.fromJson(Map<String, dynamic> json) => JobCircular(
        id: json['id'],
        title: json['title'] ?? '',
        postNames: json['post_names'],
        vacancyCount: json['vacancy_count'],
        qualification: json['qualification'],
        ageLimit: json['age_limit'],
        salaryRange: json['salary_range'],
        applicationDeadline: json['application_deadline'] != null
            ? DateTime.tryParse(json['application_deadline'])
            : null,
        examDate: json['exam_date'] != null ? DateTime.tryParse(json['exam_date']) : null,
        sourceUrl: json['source_url'],
        circularImageUrl: json['circular_image_url'],
        category: json['category'],
        isActive: json['is_active'] ?? true,
        createdAt: DateTime.tryParse(json['created_at'] ?? '') ?? DateTime.now(),
        organization:
            json['organization'] != null ? Organization.fromJson(json['organization']) : null,
      );

  /// ডেডলাইন শেষ হতে কত দিন বাকি (নেগেটিভ মানে পার হয়ে গেছে)
  int? get daysLeft {
    if (applicationDeadline == null) return null;
    return applicationDeadline!.difference(DateTime.now()).inDays;
  }
}
