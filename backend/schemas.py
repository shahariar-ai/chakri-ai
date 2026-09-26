from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, model_validator


# ---------- Organization ----------
class OrganizationOut(BaseModel):
    id: int
    name: str
    name_bn: Optional[str] = None
    org_type: str
    website: Optional[str] = None

    class Config:
        from_attributes = True


# ---------- Job Circular ----------
class JobCircularOut(BaseModel):
    id: int
    title: str
    post_names: Optional[str] = None
    vacancy_count: Optional[str] = None
    qualification: Optional[str] = None
    age_limit: Optional[str] = None
    salary_range: Optional[str] = None
    application_deadline: Optional[datetime] = None
    exam_date: Optional[datetime] = None
    source_url: Optional[str] = None
    circular_image_url: Optional[str] = None
    category: Optional[str] = None
    is_active: bool
    created_at: datetime
    organization: Optional[OrganizationOut] = None

    class Config:
        from_attributes = True


class JobCircularCreate(BaseModel):
    title: str
    organization_id: Optional[int] = None
    post_names: Optional[str] = None
    vacancy_count: Optional[str] = None
    qualification: Optional[str] = None
    age_limit: Optional[str] = None
    salary_range: Optional[str] = None
    application_start: Optional[datetime] = None
    application_deadline: Optional[datetime] = None
    exam_date: Optional[datetime] = None
    source_url: Optional[str] = None
    circular_image_url: Optional[str] = None
    full_text: Optional[str] = None
    category: Optional[str] = None
    scraped_from: Optional[str] = None


# ---------- Subject ----------
class SubjectOut(BaseModel):
    id: int
    name: str
    description: Optional[str] = None

    class Config:
        from_attributes = True


# ---------- Exam Question ----------
class ExamQuestionOut(BaseModel):
    id: int
    subject_id: int
    exam_name: Optional[str] = None
    exam_year: Optional[int] = None
    organization_name: Optional[str] = None
    question_text: str
    option_a: Optional[str] = None
    option_b: Optional[str] = None
    option_c: Optional[str] = None
    option_d: Optional[str] = None
    correct_answer: Optional[str] = None
    explanation: Optional[str] = None
    difficulty: str

    class Config:
        from_attributes = True


class ExamQuestionCreate(BaseModel):
    subject_id: int
    exam_name: Optional[str] = None
    exam_year: Optional[int] = None
    organization_name: Optional[str] = None
    question_text: str
    option_a: Optional[str] = None
    option_b: Optional[str] = None
    option_c: Optional[str] = None
    option_d: Optional[str] = None
    correct_answer: Optional[str] = None
    explanation: Optional[str] = None
    difficulty: str = "medium"
    source: Optional[str] = "manual"


# ---------- Study Material ----------
class StudyMaterialOut(BaseModel):
    id: int
    subject_id: int
    title: str
    content: str
    topic_tags: Optional[str] = None

    class Config:
        from_attributes = True


# ---------- Bulk Import (Admin) ----------
# CSV/JSON ইম্পোর্ট রো - subject_id এর বদলে subject_name নেয় (মানুষের জন্য সহজ,
# না থাকলে অ্যাডমিন রাউটার নিজে থেকে Subject বানিয়ে নেয়)
class ExamQuestionImportRow(BaseModel):
    subject_name: str
    exam_name: Optional[str] = None
    exam_year: Optional[int] = None
    organization_name: Optional[str] = None
    question_text: str
    option_a: Optional[str] = None
    option_b: Optional[str] = None
    option_c: Optional[str] = None
    option_d: Optional[str] = None
    correct_answer: Optional[str] = None
    explanation: Optional[str] = None
    difficulty: str = "medium"
    source: Optional[str] = "bulk_import"

    @model_validator(mode="after")
    def _normalize_answer(self):
        """অ্যাপ সঠিক উত্তর A/B/C/D অক্ষর দিয়ে চেনে — তাই অক্ষর, বাংলা বর্ণ বা অপশনের টেক্সট যা-ই আসুক অক্ষরে বদলানো।"""
        options = {k: v for k, v in zip("ABCD", (self.option_a, self.option_b, self.option_c, self.option_d)) if v}
        if len(options) < 2:
            raise ValueError("অন্তত দুটো অপশন (option_a, option_b) দিতে হবে")
        ans = (self.correct_answer or "").strip()
        if not ans:
            raise ValueError("correct_answer দিতে হবে")
        letter = {"ক": "A", "খ": "B", "গ": "C", "ঘ": "D"}.get(ans, ans.upper())
        if letter not in options:
            # অক্ষর না হলে অপশনের টেক্সটের সাথে মেলানো
            letter = next((k for k, v in options.items() if v.strip() == ans), None)
        if letter is None:
            raise ValueError(f"correct_answer '{ans}' কোনো অপশনের সাথে মেলে না")
        self.correct_answer = letter
        return self


class StudyMaterialImportRow(BaseModel):
    subject_name: str
    title: str
    content: str
    topic_tags: Optional[str] = None


# ---------- Device Token (notifications) ----------
class DeviceTokenRegister(BaseModel):
    token: str
    platform: str = "android"
    preferred_categories: Optional[str] = None
