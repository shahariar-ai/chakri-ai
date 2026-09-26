"""
Mock Interview Coach API।

Stateless ডিজাইন: সার্ভারে সেশন সেভ হয় না — অ্যাপ প্রতিবার এখন পর্যন্ত হওয়া
প্রশ্ন-উত্তরের পুরো history পাঠায়। প্রতি রিকোয়েস্টে AI:
  ১. শেষ উত্তরটা মূল্যায়ন করে (স্কোর + ফিডব্যাক),
  ২. পরের প্রশ্ন দেয়, অথবা সব প্রশ্ন শেষ হলে সামগ্রিক সারাংশ দেয়।
"""
from typing import List, Literal, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ai_json import call_json

router = APIRouter(prefix="/api/interview", tags=["Mock Interview"])

InterviewType = Literal["govt_viva", "bank", "private"]

INTERVIEW_TYPE_DESC = {
    "govt_viva": "বাংলাদেশের সরকারি চাকরির ভাইভা বোর্ড (BCS/PSC ধাঁচের) — মুক্তিযুদ্ধ, সংবিধান, "
                 "সাম্প্রতিক ঘটনা, নিজ জেলা, পদ-সংশ্লিষ্ট জ্ঞান ও ব্যক্তিগত প্রশ্ন",
    "bank": "বাংলাদেশের ব্যাংক (সরকারি/বেসরকারি) নিয়োগ ভাইভা — ব্যাংকিং বেসিক, অর্থনীতি, "
            "বাংলাদেশ ব্যাংকের নীতি, কাস্টমার সার্ভিস, আচরণগত প্রশ্ন",
    "private": "বেসরকারি কোম্পানির HR + টেকনিক্যাল ইন্টারভিউ — আত্মপরিচয়, পদ-সংশ্লিষ্ট দক্ষতা, "
               "আচরণগত (STAR) প্রশ্ন, বেতন প্রত্যাশা",
}


# ---------- Request / Response ----------

class InterviewTurn(BaseModel):
    question: str
    answer: str


class InterviewRequest(BaseModel):
    target_position: str = Field(..., description="যে পদের জন্য ইন্টারভিউ")
    interview_type: InterviewType = "private"
    language: Literal["bn", "en"] = "bn"
    total_questions: int = Field(5, ge=3, le=10)
    candidate_background: Optional[str] = Field(None, description="সংক্ষিপ্ত শিক্ষা/অভিজ্ঞতা")
    history: List[InterviewTurn] = []


class AnswerFeedback(BaseModel):
    score: int  # 0-10
    strengths: List[str]
    improvements: List[str]
    sample_answer: str


class InterviewSummary(BaseModel):
    overall_score: int  # 0-100
    verdict: str
    strengths: List[str]
    improvements: List[str]


class InterviewResponse(BaseModel):
    question_number: int          # পরের প্রশ্নের নম্বর (শেষ হলে total_questions)
    feedback: Optional[AnswerFeedback] = None   # শেষ উত্তরের মূল্যায়ন (প্রথম টার্নে null)
    next_question: Optional[str] = None
    finished: bool = False
    summary: Optional[InterviewSummary] = None


# ---------- AI JSON schema ----------

_FEEDBACK_SCHEMA = {
    "type": "object",
    "properties": {
        "score": {"type": "integer", "description": "0 থেকে 10"},
        "strengths": {"type": "array", "items": {"type": "string"}},
        "improvements": {"type": "array", "items": {"type": "string"}},
        "sample_answer": {"type": "string"},
    },
    "required": ["score", "strengths", "improvements", "sample_answer"],
    "additionalProperties": False,
}

_SUMMARY_SCHEMA = {
    "type": "object",
    "properties": {
        "overall_score": {"type": "integer", "description": "0 থেকে 100"},
        "verdict": {"type": "string"},
        "strengths": {"type": "array", "items": {"type": "string"}},
        "improvements": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["overall_score", "verdict", "strengths", "improvements"],
    "additionalProperties": False,
}


def _output_schema(has_answer: bool, finished: bool) -> dict:
    props, required = {}, []
    if has_answer:
        props["feedback"] = _FEEDBACK_SCHEMA
        required.append("feedback")
    if finished:
        props["summary"] = _SUMMARY_SCHEMA
        required.append("summary")
    else:
        props["next_question"] = {"type": "string"}
        required.append("next_question")
    return {"type": "object", "properties": props, "required": required, "additionalProperties": False}


def _build_prompt(data: InterviewRequest, finished: bool) -> str:
    lang = "সব লেখা বাংলায় দাও।" if data.language == "bn" else "Write everything in English."
    history_text = "\n\n".join(
        f"প্রশ্ন {i}: {t.question}\nউত্তর {i}: {t.answer}" for i, t in enumerate(data.history, 1)
    ) or "(এখনো কোনো প্রশ্ন করা হয়নি)"

    tasks = []
    if data.history:
        tasks.append(
            "feedback: শুধু শেষ উত্তরটার মূল্যায়ন — score (0-10), কী ভালো হয়েছে (strengths), "
            "কী উন্নতি দরকার (improvements, নির্দিষ্ট ও actionable), এবং একটা ছোট আদর্শ উত্তর (sample_answer)।"
        )
    if finished:
        tasks.append(
            "summary: পুরো ইন্টারভিউর সামগ্রিক মূল্যায়ন — overall_score (0-100), এক-দুই লাইনের verdict, "
            "মূল শক্তির দিক ও উন্নতির জায়গা।"
        )
    else:
        tasks.append(
            f"next_question: প্রশ্ন নম্বর {len(data.history) + 1} (মোট {data.total_questions}টার মধ্যে)। "
            "আগের প্রশ্নের পুনরাবৃত্তি কোরো না; প্রার্থীর আগের উত্তরের সূত্র ধরে follow-up করতে পারো। "
            "শুধু প্রশ্নটা লিখো, কোনো ভূমিকা নয়।"
        )

    return f"""তুমি একজন অভিজ্ঞ ইন্টারভিউয়ার ও ক্যারিয়ার কোচ। একজন বাংলাদেশি চাকরিপ্রার্থীর সাথে মক ইন্টারভিউ নিচ্ছ।

পদ: {data.target_position}
ইন্টারভিউর ধরন: {INTERVIEW_TYPE_DESC[data.interview_type]}
প্রার্থীর পটভূমি: {data.candidate_background or 'দেওয়া হয়নি'}

এখন পর্যন্ত ইন্টারভিউ:
{history_text}

তোমার কাজ:
- """ + "\n- ".join(tasks) + f"""

ফিডব্যাক সৎ কিন্তু উৎসাহব্যঞ্জক রাখো। {lang}"""


# ---------- Endpoint ----------

@router.post("/turn", response_model=InterviewResponse)
def interview_turn(data: InterviewRequest):
    """history খালি হলে প্রথম প্রশ্ন দেয়; নাহলে শেষ উত্তরের ফিডব্যাক + পরের প্রশ্ন/সারাংশ।"""
    if len(data.history) > data.total_questions:
        raise HTTPException(status_code=400, detail="history-তে total_questions-এর বেশি উত্তর আছে")
    if any(not t.answer.strip() for t in data.history):
        raise HTTPException(status_code=400, detail="খালি উত্তর পাঠানো যাবে না")

    finished = len(data.history) == data.total_questions
    out = call_json(_build_prompt(data, finished), _output_schema(bool(data.history), finished))

    feedback = out.get("feedback")
    if feedback:
        feedback["score"] = max(0, min(10, feedback["score"]))
    summary = out.get("summary")
    if summary:
        summary["overall_score"] = max(0, min(100, summary["overall_score"]))

    return InterviewResponse(
        question_number=min(len(data.history) + 1, data.total_questions),
        feedback=feedback,
        next_question=out.get("next_question"),
        finished=finished,
        summary=summary,
    )
