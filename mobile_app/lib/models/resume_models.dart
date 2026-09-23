class Education {
  String institution;
  String degree;
  String field;
  String passingYear;
  String? result;

  Education({
    required this.institution,
    required this.degree,
    required this.field,
    required this.passingYear,
    this.result,
  });

  Map<String, dynamic> toJson() => {
        "institution": institution,
        "degree": degree,
        "field": field,
        "passing_year": passingYear,
        "result": result,
      };
}

class WorkExperience {
  String company;
  String position;
  String duration;
  String responsibilities;

  WorkExperience({
    required this.company,
    required this.position,
    required this.duration,
    required this.responsibilities,
  });

  Map<String, dynamic> toJson() => {
        "company": company,
        "position": position,
        "duration": duration,
        "responsibilities": responsibilities,
      };
}

class ResumeFormData {
  String fullName = "";
  String email = "";
  String phone = "";
  String address = "";
  String targetPosition = "";
  String summaryPoints = "";
  List<Education> education = [];
  List<WorkExperience> experience = [];
  List<String> skills = [];
  String language = "bn"; // 'bn' or 'en'

  Map<String, dynamic> toJson() => {
        "full_name": fullName,
        "email": email,
        "phone": phone,
        "address": address,
        "target_position": targetPosition,
        "summary_points": summaryPoints,
        "education": education.map((e) => e.toJson()).toList(),
        "experience": experience.map((e) => e.toJson()).toList(),
        "skills": skills,
        "language": language,
      };
}

class ResumeResult {
  final String resumeText;
  final List<String> atsTips;

  ResumeResult({required this.resumeText, required this.atsTips});

  factory ResumeResult.fromJson(Map<String, dynamic> json) {
    return ResumeResult(
      resumeText: json['resume_text'] ?? '',
      atsTips: List<String>.from(json['ats_score_tips'] ?? []),
    );
  }
}
