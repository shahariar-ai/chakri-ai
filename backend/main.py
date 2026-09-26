"""
চাকরি AI - Backend API
Phase 1: AI Resume/CV Builder

চালানোর নিয়ম:
    pip install -r requirements.txt
    uvicorn main:app --reload

এনভায়রনমেন্ট ভ্যারিয়েবল দরকার:
    ANTHROPIC_API_KEY অথবা GEMINI_API_KEY (.env ফাইলে)
"""

import os
import json
import re
from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List, Optional
from dotenv import load_dotenv
import anthropic

from pdf_export import text_to_pdf
from routers import circulars, questions, notifications, admin, interview, payments, job_match

load_dotenv()

app = FastAPI(title="চাকরি AI - Backend API", version="0.2.0")

# CORS - শুধু ব্রাউজার (Flutter web/admin পেজ) এর ক্ষেত্রে লাগে; Android/iOS/Windows নেটিভ অ্যাপ
# CORS চেক করে না, তাই মোবাইল অ্যাপের রিকোয়েস্ট সবসময় allow।
# CORS_ORIGINS="https://a.com,https://b.com" দিয়ে নির্দিষ্ট ডোমেইনে সীমিত করা যায়, না দিলে সব অরিজিন।
# অ্যাপ cookie ব্যবহার করে না (admin-এ X-Admin-Key হেডার), তাই allow_credentials=False —
# "*" অরিজিনের সাথে credentials=True দেওয়া CORS স্পেক অনুযায়ী অবৈধ।
_cors_origins = [o.strip() for o in os.getenv("CORS_ORIGINS", "*").split(",") if o.strip()] or ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ডেটাবেস স্কিমা এখন Alembic migration দিয়ে ম্যানেজ করা হয় (Base.metadata.create_all() না)।
# সার্ভার চালানোর আগে: alembic upgrade head

# নতুন রাউটার যুক্ত করা হলো: সার্কুলার, প্রশ্নব্যাংক, স্টাডি মেটেরিয়াল, নোটিফিকেশন
app.include_router(circulars.router)
app.include_router(questions.router)
app.include_router(questions.study_router)
app.include_router(notifications.router)
app.include_router(admin.router)
app.include_router(interview.router)
app.include_router(payments.router)
app.include_router(job_match.router)

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


# ---------- Data Models ----------

class Education(BaseModel):
    institution: str
    degree: str
    field: str
    passing_year: str
    result: Optional[str] = None


class Experience(BaseModel):
    company: str
    position: str
    duration: str
    responsibilities: str


class ResumeRequest(BaseModel):
    full_name: str
    email: str
    phone: str
    address: Optional[str] = None
    target_position: str = Field(..., description="যে পদের জন্য আবেদন করছেন")
    summary_points: Optional[str] = Field(
        None, description="ইউজার নিজে সম্পর্কে যা লিখতে চান (bullet/free text)"
    )
    education: List[Education]
    experience: List[Experience] = []
    skills: List[str]
    language: str = Field("bn", description="'bn' অথবা 'en'")


class ResumeResponse(BaseModel):
    resume_text: str
    ats_score_tips: List[str]


class PdfExportRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=20000)


class CoverLetterRequest(BaseModel):
    resume_summary: str
    job_description: str
    company_name: str
    target_position: str
    language: str = "bn"


# ---------- Helper ----------

# অ্যাপ (SelectableText) ও PDF (pw.Text) দুটোই প্লেইন টেক্সট দেখায় — Markdown চিহ্ন থাকলে হুবহু দেখা যায়
PLAIN_TEXT_RULE = "Markdown ব্যবহার কোরো না (#, **, __, ---, টেবিল নয়) — সাধারণ প্লেইন টেক্সট দাও; হেডিং আলাদা লাইনে লিখো।"


def strip_markdown(text: str) -> str:
    """prompt মানা না হলেও নিশ্চিতভাবে Markdown চিহ্ন সরানো (হেডিং #, বোল্ড **/__, --- লাইন)।"""
    text = re.sub(r"^\s{0,3}#{1,6}\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"(\*\*|__)(.+?)\1", r"\2", text)
    text = re.sub(r"^\s*([-*_]\s*){3,}$", "", text, flags=re.MULTILINE)
    text = re.sub(r"\n{3,}", "\n\n", text)  # মুছে ফেলা লাইনের কারণে বাড়তি ফাঁকা লাইন
    return text.strip()


def build_resume_prompt(data: ResumeRequest) -> str:
    lang_instruction = (
        "রেজাল্ট বাংলা ভাষায় লিখো, পেশাদার এবং ATS-friendly।"
        if data.language == "bn"
        else "Write the result in professional English, ATS-friendly."
    )

    edu_text = "\n".join(
        f"- {e.degree} in {e.field}, {e.institution} ({e.passing_year}) Result: {e.result or 'N/A'}"
        for e in data.education
    )
    exp_text = "\n".join(
        f"- {e.position} at {e.company} ({e.duration}): {e.responsibilities}"
        for e in data.experience
    ) or "কোনো পূর্ব অভিজ্ঞতা নেই / No prior experience"

    return f"""তুমি একজন প্রফেশনাল রিজিউম রাইটার। নিচের তথ্য দিয়ে একটি সম্পূর্ণ, সুসংগঠিত, ATS-friendly রিজিউম তৈরি করো।

নাম: {data.full_name}
ইমেইল: {data.email}
ফোন: {data.phone}
ঠিকানা: {data.address or ''}
টার্গেট পদ: {data.target_position}

ব্যবহারকারীর নিজের কথা (সারমর্মে ব্যবহার করো): {data.summary_points or 'নেই'}

শিক্ষাগত যোগ্যতা:
{edu_text}

অভিজ্ঞতা:
{exp_text}

স্কিল: {', '.join(data.skills)}

নির্দেশনা:
1. {lang_instruction}
2. একটি ৩-৪ লাইনের Professional Summary দিয়ে শুরু করো যা টার্গেট পদের সাথে সামঞ্জস্যপূর্ণ।
3. Section গুলো স্পষ্ট হেডিং সহ সাজাও: Summary, Skills, Experience, Education।
4. Experience অংশে action verbs ব্যবহার করো এবং যতটা সম্ভব measurable achievement যোগ করো।
5. শুধু রিজিউমের টেক্সট আউটপুট দাও, কোনো অতিরিক্ত ব্যাখ্যা নয়।
6. {PLAIN_TEXT_RULE}
"""


# ---------- Endpoints ----------

@app.get("/")
def health_check():
    return {"status": "ok", "service": "চাকরি AI backend"}


@app.get("/api/health")
def health_check_detailed():
    """ডিপ্লয় যাচাইয়ের জন্য: ডেটাবেস কানেকশন ও দরকারি কনফিগ ঠিক আছে কিনা (সিক্রেট ফাঁস করে না)।"""
    from sqlalchemy import text
    from database import engine

    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        db_status = "ok"
    except Exception as e:  # noqa: BLE001
        db_status = f"error: {type(e).__name__}"

    body = {
        "status": "ok" if db_status == "ok" else "degraded",
        "database": db_status,
        "database_engine": engine.dialect.name,  # "postgresql" হলে Render DB-তে কানেক্টেড
        "ai_configured": bool(os.getenv("ANTHROPIC_API_KEY")),
    }
    return JSONResponse(body, status_code=200 if db_status == "ok" else 503)


@app.post("/api/resume/generate", response_model=ResumeResponse)
def generate_resume(data: ResumeRequest):
    if not os.getenv("ANTHROPIC_API_KEY"):
        raise HTTPException(status_code=500, detail="ANTHROPIC_API_KEY সেট করা নেই (.env ফাইল দেখুন)")

    prompt = build_resume_prompt(data)

    try:
        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}],
        )
        resume_text = strip_markdown(message.content[0].text)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"AI generation failed: {str(e)}")

    ats_tips = [
        "চাকরির বিজ্ঞাপনের keyword গুলো রিজিউমে ব্যবহার করুন",
        "ফাইল ফরম্যাট .docx বা সাধারণ .pdf রাখুন (কোনো জটিল টেবিল/গ্রাফিক্স নয়)",
        "স্ট্যান্ডার্ড হেডিং ব্যবহার করুন (Experience, Education, Skills)",
    ]

    return ResumeResponse(resume_text=resume_text, ats_score_tips=ats_tips)


@app.post("/api/resume/pdf")
def export_resume_pdf(data: PdfExportRequest):
    """রিজিউম/কভার লেটার টেক্সট -> PDF (বাংলা সঠিকভাবে shape করা; Flutter-এর pdf প্যাকেজ তা পারে না)।"""
    return Response(
        content=text_to_pdf(data.text),
        media_type="application/pdf",
        headers={"Content-Disposition": 'inline; filename="resume.pdf"'},
    )


@app.post("/api/cover-letter/generate")
def generate_cover_letter(data: CoverLetterRequest):
    if not os.getenv("ANTHROPIC_API_KEY"):
        raise HTTPException(status_code=500, detail="ANTHROPIC_API_KEY সেট করা নেই")

    lang_instruction = "বাংলায় লিখো" if data.language == "bn" else "Write in English"

    prompt = f"""তুমি একজন প্রফেশনাল কভার লেটার রাইটার। নিচের তথ্য দিয়ে একটি কভার লেটার লিখো।

আবেদনকারীর রিজিউম সারমর্ম: {data.resume_summary}
কোম্পানি: {data.company_name}
পদ: {data.target_position}
জব ডেসক্রিপশন: {data.job_description}

নির্দেশনা: {lang_instruction}। ৩-৪ প্যারাগ্রাফ, প্রফেশনাল টোন, নির্দিষ্ট জব ডেসক্রিপশনের সাথে সামঞ্জস্যপূর্ণ করে লিখো।
শুধু কভার লেটারের টেক্সট দাও। {PLAIN_TEXT_RULE}
"""
    try:
        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1200,
            messages=[{"role": "user", "content": prompt}],
        )
        return {"cover_letter": strip_markdown(message.content[0].text)}
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"AI generation failed: {str(e)}")
