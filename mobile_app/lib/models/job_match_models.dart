// Job Matching / Skill Gap-এর ডেটা মডেল (backend: /api/job-match/*)

/// ইউজারের প্রোফাইল — shared_preferences-এ সেভ থাকে, যাতে প্রতিবার লিখতে না হয়
class CandidateProfile {
  final List<String> skills;
  final String? education;
  final String? experience;
  final int? age;

  CandidateProfile({required this.skills, this.education, this.experience, this.age});

  bool get isComplete => skills.isNotEmpty;

  Map<String, dynamic> toJson() => {
        "skills": skills,
        if (education != null && education!.isNotEmpty) "education": education,
        if (experience != null && experience!.isNotEmpty) "experience": experience,
        if (age != null) "age": age,
      };

  factory CandidateProfile.fromJson(Map<String, dynamic> json) => CandidateProfile(
        skills: List<String>.from(json['skills'] ?? []),
        education: json['education'],
        experience: json['experience'],
        age: json['age'],
      );
}

class MissingSkill {
  final String skill;
  final String importance; // high | medium | low
  final String howToLearn;

  MissingSkill({required this.skill, required this.importance, required this.howToLearn});

  factory MissingSkill.fromJson(Map<String, dynamic> json) => MissingSkill(
        skill: json['skill'],
        importance: json['importance'],
        howToLearn: json['how_to_learn'] ?? '',
      );
}

class JobMatchAnalysis {
  final int? circularId;
  final String? jobTitle;
  final int matchScore; // 0-100
  final String eligibility; // eligible | partially | not_eligible | unknown
  final bool infoSufficient;
  final String verdict;
  final List<String> matchedSkills;
  final List<MissingSkill> missingSkills;
  final List<String> strengths;
  final List<String> actionPlan;

  JobMatchAnalysis({
    this.circularId,
    this.jobTitle,
    required this.matchScore,
    required this.eligibility,
    required this.infoSufficient,
    required this.verdict,
    required this.matchedSkills,
    required this.missingSkills,
    required this.strengths,
    required this.actionPlan,
  });

  factory JobMatchAnalysis.fromJson(Map<String, dynamic> json) => JobMatchAnalysis(
        circularId: json['circular_id'],
        jobTitle: json['job_title'],
        matchScore: json['match_score'],
        eligibility: json['eligibility'],
        infoSufficient: json['info_sufficient'] ?? true,
        verdict: json['verdict'] ?? '',
        matchedSkills: List<String>.from(json['matched_skills'] ?? []),
        missingSkills: (json['missing_skills'] as List? ?? []).map((e) => MissingSkill.fromJson(e)).toList(),
        strengths: List<String>.from(json['strengths'] ?? []),
        actionPlan: List<String>.from(json['action_plan'] ?? []),
      );
}

class RecommendedJob {
  final int circularId;
  final String title;
  final String? organization;
  final String? category;
  final DateTime? applicationDeadline;
  final int matchScore;
  final String reason;

  RecommendedJob({
    required this.circularId,
    required this.title,
    this.organization,
    this.category,
    this.applicationDeadline,
    required this.matchScore,
    required this.reason,
  });

  factory RecommendedJob.fromJson(Map<String, dynamic> json) => RecommendedJob(
        circularId: json['circular_id'],
        title: json['title'],
        organization: json['organization'],
        category: json['category'],
        applicationDeadline:
            json['application_deadline'] != null ? DateTime.parse(json['application_deadline']) : null,
        matchScore: json['match_score'],
        reason: json['reason'] ?? '',
      );
}

class RecommendResult {
  final int considered;
  final List<RecommendedJob> jobs;

  RecommendResult({required this.considered, required this.jobs});

  factory RecommendResult.fromJson(Map<String, dynamic> json) => RecommendResult(
        considered: json['considered'],
        jobs: (json['jobs'] as List).map((e) => RecommendedJob.fromJson(e)).toList(),
      );
}
