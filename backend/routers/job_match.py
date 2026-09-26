"""
Job Matching ও Skill Gap Analysis API (/api/job-match/*)।

- /analyze   : ইউজারের প্রোফাইল একটা নির্দিষ্ট চাকরির (সার্কুলার বা পেস্ট করা জব ডেসক্রিপশন) সাথে
               মিলিয়ে উপযুক্ততার স্কোর, মিল থাকা/ঘাটতি থাকা স্কিল ও শেখার পরিকল্পনা দেয় (Skill Gap)।
- /recommend : চালু থাকা সার্কুলারগুলো থেকে ইউজারের জন্য সবচেয়ে উপযুক্তগুলো বেছে দেয়।

সার্কুলারে অনেক সময় যোগ্যতার তথ্য থাকে না (যেমন BPSC নোটিশে শুধু শিরোনাম) — তখন AI-কে
আন্দাজে স্কোর না দিয়ে info_sufficient=false জানাতে বলা হয়।
"""
from datetime import datetime
from typing import List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, model_validator
from sqlalchemy import or_
from sqlalchemy.orm import Session

import models
from ai_json import call_json
from database import get_db

router = APIRouter(prefix="/api/job-match", tags=["Job Matching"])

RECOMMEND_POOL_SIZE = 25  # AI-কে একবারে সর্বোচ্চ কতগুলো সার্কুলার দেখানো হবে


# ---------- Request / Response ----------

class CandidateProfile(BaseModel):
    skills: List[str] = Field(..., min_length=1, max_length=40)
    education: Optional[str] = Field(None, description="যেমন: BBA (Finance), ঢাকা বিশ্ববিদ্যালয়, CGPA 3.5")
    experience: Optional[str] = Field(None, description="যেমন: ২ বছর সেলস অফিসার")
    resume_summary: Optional[str] = None
    age: Optional[int] = Field(None, ge=15, le=70)
    language: Literal["bn", "en"] = "bn"

    @model_validator(mode="after")
    def _clean_skills(self):
        self.skills = [s.strip() for s in self.skills if s.strip()]
        if not self.skills:
            raise ValueError("অন্তত একটা স্কিল দিতে হবে")
        return self


class AnalyzeRequest(CandidateProfile):
    circular_id: Optional[int] = None
    job_description: Optional[str] = Field(None, max_length=8000)

    @model_validator(mode="after")
    def _need_job(self):
        if not self.circular_id and not (self.job_description or "").strip():
            raise ValueError("circular_id অথবা job_description — যেকোনো একটা দিতে হবে")
        return self


class MissingSkill(BaseModel):
    skill: str
    importance: Literal["high", "medium", "low"]
    how_to_learn: str


class AnalyzeResponse(BaseModel):
    circular_id: Optional[int] = None
    job_title: Optional[str] = None
    match_score: int  # 0-100
    eligibility: Literal["eligible", "partially", "not_eligible", "unknown"]
    info_sufficient: bool  # চাকরির চাহিদা বোঝার মতো যথেষ্ট তথ্য ছিল কিনা
    verdict: str
    matched_skills: List[str]
    missing_skills: List[MissingSkill]
    strengths: List[str]
    action_plan: List[str]


class RecommendRequest(CandidateProfile):
    limit: int = Field(5, ge=1, le=10)
    category: Optional[str] = None


class RecommendedJob(BaseModel):
    circular_id: int
    title: str
    organization: Optional[str] = None
    category: Optional[str] = None
    application_deadline: Optional[datetime] = None
    match_score: int
    reason: str


class RecommendResponse(BaseModel):
    considered: int  # কতগুলো সার্কুলার যাচাই করা হয়েছে
    jobs: List[RecommendedJob]


# ---------- AI JSON schema ----------

_ANALYZE_SCHEMA = {
    "type": "object",
    "properties": {
        "match_score": {"type": "integer", "description": "0 থেকে 100"},
        "eligibility": {"type": "string", "enum": ["eligible", "partially", "not_eligible", "unknown"]},
        "info_sufficient": {"type": "boolean"},
        "verdict": {"type": "string"},
        "matched_skills": {"type": "array", "items": {"type": "string"}},
        "missing_skills": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "skill": {"type": "string"},
                    "importance": {"type": "string", "enum": ["high", "medium", "low"]},
                    "how_to_learn": {"type": "string"},
                },
                "required": ["skill", "importance", "how_to_learn"],
                "additionalProperties": False,
            },
        },
        "strengths": {"type": "array", "items": {"type": "string"}},
        "action_plan": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["match_score", "eligibility", "info_sufficient", "verdict", "matched_skills",
                 "missing_skills", "strengths", "action_plan"],
    "additionalProperties": False,
}

_RECOMMEND_SCHEMA = {
    "type": "object",
    "properties": {
        "matches": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "circular_id": {"type": "integer"},
                    "match_score": {"type": "integer", "description": "0 থেকে 100"},
                    "reason": {"type": "string"},
                },
                "required": ["circular_id", "match_score", "reason"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["matches"],
    "additionalProperties": False,
}


# ---------- Helpers ----------

def _profile_text(p: CandidateProfile) -> str:
    return "\n".join([
        f"স্কিল: {', '.join(p.skills)}",
        f"শিক্ষা: {p.education or 'দেওয়া হয়নি'}",
        f"অভিজ্ঞতা: {p.experience or 'দেওয়া হয়নি'}",
        f"বয়স: {p.age if p.age else 'দেওয়া হয়নি'}",
        f"রিজিউম সারাংশ: {p.resume_summary or 'দেওয়া হয়নি'}",
    ])


def _circular_text(c: models.JobCircular, max_full_text: int = 3000) -> str:
    org = c.organization.name_bn or c.organization.name if c.organization else None
    fields = [
        ("শিরোনাম", c.title),
        ("প্রতিষ্ঠান", org),
        ("পদ", c.post_names),
        ("ক্যাটাগরি", c.category),
        ("শিক্ষাগত যোগ্যতা", c.qualification),
        ("বয়সসীমা", c.age_limit),
        ("বেতন", c.salary_range),
        ("আবেদনের শেষ তারিখ", c.application_deadline.date().isoformat() if c.application_deadline else None),
        ("বিস্তারিত", (c.full_text or "")[:max_full_text] or None),
    ]
    return "\n".join(f"{k}: {v}" for k, v in fields if v)


def _lang(p: CandidateProfile) -> str:
    return "সব লেখা বাংলায় দাও।" if p.language == "bn" else "Write everything in English."


def _clamp(n: int) -> int:
    return max(0, min(100, n))


# ---------- Endpoints ----------

@router.post("/analyze", response_model=AnalyzeResponse)
def analyze(data: AnalyzeRequest, db: Session = Depends(get_db)):
    circular = None
    if data.circular_id:
        circular = db.get(models.JobCircular, data.circular_id)
        if not circular:
            raise HTTPException(status_code=404, detail="সার্কুলার পাওয়া যায়নি")
        job_text = _circular_text(circular)
        if data.job_description:
            job_text += f"\nঅতিরিক্ত তথ্য (ইউজারের দেওয়া): {data.job_description.strip()}"
    else:
        job_text = data.job_description.strip()

    prompt = f"""তুমি বাংলাদেশের চাকরির বাজার সম্পর্কে অভিজ্ঞ একজন ক্যারিয়ার কাউন্সেলর।
একজন চাকরিপ্রার্থীর প্রোফাইল একটা নির্দিষ্ট চাকরির সাথে মিলিয়ে দেখো তিনি কতটা উপযুক্ত।

## চাকরিপ্রার্থীর প্রোফাইল
{_profile_text(data)}

## চাকরির তথ্য
{job_text}

## নির্দেশনা
- match_score (0-100): প্রোফাইল চাকরির চাহিদার সাথে কতটা মেলে।
- eligibility: শিক্ষাগত যোগ্যতা/বয়স/অভিজ্ঞতার শর্ত পূরণ হয় কিনা। শর্ত জানা না গেলে "unknown"।
- info_sufficient: চাকরির চাহিদা বোঝার মতো যথেষ্ট তথ্য থাকলে true। শুধু শিরোনাম বা নোটিশ থাকলে false —
  তখন আন্দাজে উঁচু বা নিচু স্কোর দিও না, verdict-এ বলো পূর্ণ সার্কুলার দেখে আবার যাচাই করতে।
- matched_skills: প্রার্থীর যে স্কিলগুলো এই চাকরিতে কাজে লাগবে।
- missing_skills: চাকরিতে দরকার কিন্তু প্রার্থীর নেই এমন স্কিল — importance (high/medium/low) এবং
  বাংলাদেশে সহজলভ্য উপায়ে কীভাবে শেখা যায় (how_to_learn, নির্দিষ্ট ও বাস্তবসম্মত)।
  সরকারি চাকরি হলে লিখিত/MCQ পরীক্ষার বিষয়ও (বাংলা, ইংরেজি, গণিত, সাধারণ জ্ঞান) বিবেচনা করো।
- strengths: এই চাকরির জন্য প্রার্থীর শক্তির দিক।
- action_plan: আবেদনের আগে ধাপে ধাপে কী করা উচিত (৩-৫টা)।
- verdict: ১-২ লাইনে সৎ সারসংক্ষেপ।
{_lang(data)}"""

    out = call_json(prompt, _ANALYZE_SCHEMA)
    out["match_score"] = _clamp(out["match_score"])
    return AnalyzeResponse(
        circular_id=circular.id if circular else None,
        job_title=circular.title if circular else None,
        **out,
    )


@router.post("/recommend", response_model=RecommendResponse)
def recommend(data: RecommendRequest, db: Session = Depends(get_db)):
    query = db.query(models.JobCircular).filter(
        models.JobCircular.is_active.is_(True),
        or_(models.JobCircular.application_deadline.is_(None),
            models.JobCircular.application_deadline >= datetime.utcnow()),
    )
    if data.category:
        query = query.filter(models.JobCircular.category == data.category)
    circulars = query.order_by(models.JobCircular.created_at.desc()).limit(RECOMMEND_POOL_SIZE).all()
    if not circulars:
        return RecommendResponse(considered=0, jobs=[])

    by_id = {c.id: c for c in circulars}
    listing = "\n\n".join(f"[circular_id={c.id}]\n{_circular_text(c, max_full_text=400)}" for c in circulars)

    prompt = f"""তুমি বাংলাদেশের চাকরির বাজার সম্পর্কে অভিজ্ঞ একজন ক্যারিয়ার কাউন্সেলর।
নিচের সার্কুলারগুলোর মধ্যে কোনগুলো এই চাকরিপ্রার্থীর জন্য সবচেয়ে উপযুক্ত তা বেছে দাও।

## চাকরিপ্রার্থীর প্রোফাইল
{_profile_text(data)}

## সার্কুলার তালিকা
{listing}

## নির্দেশনা
- সবচেয়ে উপযুক্ত সর্বোচ্চ {data.limit}টা সার্কুলার matches-এ দাও, match_score (0-100) অনুযায়ী বড় থেকে ছোট।
- শুধু ওপরের তালিকায় থাকা circular_id ব্যবহার করো।
- যেগুলো আসলে নিয়োগ বিজ্ঞপ্তি নয় (যেমন যোগদান/ফলাফল/পরীক্ষার নোটিশ) সেগুলো বাদ দাও।
- reason: কেন উপযুক্ত — ১ লাইনে; তথ্য কম থাকলে সেটাও উল্লেখ করো।
- কোনোটাই উপযুক্ত না হলে matches খালি রাখো।
{_lang(data)}"""

    out = call_json(prompt, _RECOMMEND_SCHEMA)

    jobs, seen = [], set()
    for m in out["matches"]:
        c = by_id.get(m["circular_id"])
        if not c or c.id in seen:  # AI তালিকার বাইরের বা ডুপ্লিকেট id দিলে বাদ
            continue
        seen.add(c.id)
        jobs.append(RecommendedJob(
            circular_id=c.id,
            title=c.title,
            organization=(c.organization.name_bn or c.organization.name) if c.organization else None,
            category=c.category,
            application_deadline=c.application_deadline,
            match_score=_clamp(m["match_score"]),
            reason=m["reason"],
        ))
    jobs.sort(key=lambda j: j.match_score, reverse=True)
    return RecommendResponse(considered=len(circulars), jobs=jobs[:data.limit])
