// Mock Interview Coach-এর ডেটা মডেল (backend: /api/interview/turn)

class InterviewSetup {
  final String targetPosition;
  final String interviewType; // govt_viva | bank | private
  final String language; // bn | en
  final int totalQuestions;
  final String? candidateBackground;

  InterviewSetup({
    required this.targetPosition,
    this.interviewType = "private",
    this.language = "bn",
    this.totalQuestions = 5,
    this.candidateBackground,
  });

  Map<String, dynamic> toJson() => {
        "target_position": targetPosition,
        "interview_type": interviewType,
        "language": language,
        "total_questions": totalQuestions,
        if (candidateBackground != null && candidateBackground!.isNotEmpty)
          "candidate_background": candidateBackground,
      };
}

class AnswerFeedback {
  final int score; // 0-10
  final List<String> strengths;
  final List<String> improvements;
  final String sampleAnswer;

  AnswerFeedback({
    required this.score,
    required this.strengths,
    required this.improvements,
    required this.sampleAnswer,
  });

  factory AnswerFeedback.fromJson(Map<String, dynamic> json) => AnswerFeedback(
        score: json['score'],
        strengths: List<String>.from(json['strengths'] ?? []),
        improvements: List<String>.from(json['improvements'] ?? []),
        sampleAnswer: json['sample_answer'] ?? '',
      );
}

class InterviewSummary {
  final int overallScore; // 0-100
  final String verdict;
  final List<String> strengths;
  final List<String> improvements;

  InterviewSummary({
    required this.overallScore,
    required this.verdict,
    required this.strengths,
    required this.improvements,
  });

  factory InterviewSummary.fromJson(Map<String, dynamic> json) => InterviewSummary(
        overallScore: json['overall_score'],
        verdict: json['verdict'] ?? '',
        strengths: List<String>.from(json['strengths'] ?? []),
        improvements: List<String>.from(json['improvements'] ?? []),
      );
}

/// একটা প্রশ্ন, প্রার্থীর উত্তর, আর সেই উত্তরের ফিডব্যাক (পরের টার্নে আসে)
class InterviewTurn {
  final String question;
  String? answer;
  AnswerFeedback? feedback;

  InterviewTurn({required this.question, this.answer, this.feedback});
}

class InterviewTurnResult {
  final int questionNumber;
  final AnswerFeedback? feedback;
  final String? nextQuestion;
  final bool finished;
  final InterviewSummary? summary;

  InterviewTurnResult({
    required this.questionNumber,
    this.feedback,
    this.nextQuestion,
    required this.finished,
    this.summary,
  });

  factory InterviewTurnResult.fromJson(Map<String, dynamic> json) => InterviewTurnResult(
        questionNumber: json['question_number'],
        feedback: json['feedback'] != null ? AnswerFeedback.fromJson(json['feedback']) : null,
        nextQuestion: json['next_question'],
        finished: json['finished'] ?? false,
        summary: json['summary'] != null ? InterviewSummary.fromJson(json['summary']) : null,
      );
}
