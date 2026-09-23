class Subject {
  final int id;
  final String name;
  final String? description;

  Subject({required this.id, required this.name, this.description});

  factory Subject.fromJson(Map<String, dynamic> json) => Subject(
        id: json['id'],
        name: json['name'] ?? '',
        description: json['description'],
      );
}

class ExamQuestion {
  final int id;
  final int subjectId;
  final String? examName;
  final int? examYear;
  final String? organizationName;
  final String questionText;
  final String? optionA;
  final String? optionB;
  final String? optionC;
  final String? optionD;
  final String? correctAnswer;
  final String? explanation;
  final String difficulty;

  ExamQuestion({
    required this.id,
    required this.subjectId,
    this.examName,
    this.examYear,
    this.organizationName,
    required this.questionText,
    this.optionA,
    this.optionB,
    this.optionC,
    this.optionD,
    this.correctAnswer,
    this.explanation,
    required this.difficulty,
  });

  factory ExamQuestion.fromJson(Map<String, dynamic> json) => ExamQuestion(
        id: json['id'],
        subjectId: json['subject_id'],
        examName: json['exam_name'],
        examYear: json['exam_year'],
        organizationName: json['organization_name'],
        questionText: json['question_text'] ?? '',
        optionA: json['option_a'],
        optionB: json['option_b'],
        optionC: json['option_c'],
        optionD: json['option_d'],
        correctAnswer: json['correct_answer'],
        explanation: json['explanation'],
        difficulty: json['difficulty'] ?? 'medium',
      );

  List<MapEntry<String, String>> get options => [
        if (optionA != null && optionA!.isNotEmpty) MapEntry('A', optionA!),
        if (optionB != null && optionB!.isNotEmpty) MapEntry('B', optionB!),
        if (optionC != null && optionC!.isNotEmpty) MapEntry('C', optionC!),
        if (optionD != null && optionD!.isNotEmpty) MapEntry('D', optionD!),
      ];
}

class StudyMaterial {
  final int id;
  final int subjectId;
  final String title;
  final String content;
  final String? topicTags;

  StudyMaterial({
    required this.id,
    required this.subjectId,
    required this.title,
    required this.content,
    this.topicTags,
  });

  factory StudyMaterial.fromJson(Map<String, dynamic> json) => StudyMaterial(
        id: json['id'],
        subjectId: json['subject_id'],
        title: json['title'] ?? '',
        content: json['content'] ?? '',
        topicTags: json['topic_tags'],
      );

  // "গণিত, সংখ্যাতত্ত্ব" -> ["গণিত", "সংখ্যাতত্ত্ব"]
  List<String> get tags => (topicTags ?? '')
      .split(',')
      .map((t) => t.trim())
      .where((t) => t.isNotEmpty)
      .toList();
}
