"""
অ্যাডমিন এন্ডপয়েন্ট: ExamQuestion ও StudyMaterial-এ CSV/JSON ফাইল থেকে
বাল্ক ডেটা import করার জন্য।

ফরম্যাট (CSV হেডার / JSON key একই নাম ব্যবহার করে):
    প্রশ্ন (questions/import):
        subject_name, exam_name, exam_year, organization_name, question_text,
        option_a, option_b, option_c, option_d, correct_answer, explanation,
        difficulty, source
        - আবশ্যক: subject_name, question_text, অন্তত option_a ও option_b, correct_answer
        - correct_answer: A/B/C/D (বা ক/খ/গ/ঘ) অথবা কোনো অপশনের হুবহু টেক্সট — সেভ হয় A-D অক্ষরে
        - subject_name আগে থেকে না থাকলে নতুন Subject অটো তৈরি হয়ে যাবে
          (পুরনো ছোট নাম যেমন "বাংলা" হলে subject_aliases.py অনুযায়ী canonical নামে যায়)

    স্টাডি ম্যাটেরিয়াল (study-materials/import):
        subject_name, title, content, topic_tags
        - আবশ্যক: subject_name, title, content

টেমপ্লেট CSV পেতে: GET /api/admin/questions/import/template
                    GET /api/admin/study-materials/import/template

সুরক্ষা: প্রতিটা রিকোয়েস্টে X-Admin-Key হেডারে .env এর ADMIN_API_KEY মিলতে হবে।
"""
import csv
import io
import json
import os
from typing import List, Optional, Tuple

from fastapi import APIRouter, Depends, File, Header, HTTPException, Query, UploadFile
from fastapi.responses import PlainTextResponse
from pydantic import ValidationError
from sqlalchemy.orm import Session

from database import get_db
import models
from subject_aliases import canonical_subject_name
import schemas

router = APIRouter(prefix="/api/admin", tags=["Admin - Bulk Import"])


def verify_admin_key(x_admin_key: Optional[str] = Header(None)):
    expected = os.getenv("ADMIN_API_KEY")
    if not expected:
        raise HTTPException(status_code=500, detail="ADMIN_API_KEY সার্ভারে সেট করা নেই (.env দেখুন)")
    if x_admin_key != expected:
        raise HTTPException(status_code=401, detail="অবৈধ অ্যাডমিন কী (X-Admin-Key হেডার দিন)")


def get_or_create_subject(db: Session, name: str) -> models.Subject:
    # "বাংলা"-র মতো পুরনো ছোট নাম merge-করা canonical নামে বদলে নেওয়া হয়
    name = canonical_subject_name(name)
    subject = db.query(models.Subject).filter(models.Subject.name == name).first()
    if subject:
        return subject
    subject = models.Subject(name=name)
    db.add(subject)
    db.flush()  # id পাওয়ার জন্য কমিট ছাড়াই flush
    return subject


def _parse_rows(file: UploadFile, raw: bytes) -> Tuple[List[dict], bool]:
    """ফাইল এক্সটেনশন দেখে CSV/JSON পার্স করে (rows, is_csv) রিটার্ন করে।
    utf-8-sig ব্যবহার করা হয় কারণ Excel থেকে এক্সপোর্ট করা CSV-তে প্রায়ই BOM থাকে।"""
    filename = (file.filename or "").lower()
    text = raw.decode("utf-8-sig")

    if filename.endswith(".json"):
        data = json.loads(text)
        if not isinstance(data, list):
            raise HTTPException(status_code=400, detail="JSON ফাইলের রুট অবশ্যই একটা array (list) হতে হবে")
        return data, False

    if filename.endswith(".csv"):
        reader = csv.DictReader(io.StringIO(text))
        return list(reader), True

    raise HTTPException(status_code=400, detail="ফাইলের এক্সটেনশন অবশ্যই .csv অথবা .json হতে হবে")


def _clean_row(row: dict) -> dict:
    """CSV-তে খালি স্ট্রিং আসে, JSON-এ None থাকে - দুটোকেই None বানানো হয় এবং
    স্ট্রিং ভ্যালু trim করা হয়, যাতে required-field ভ্যালিডেশন ভুল ফেল না করে।"""
    cleaned = {}
    for k, v in row.items():
        if isinstance(v, str):
            v = v.strip()
            cleaned[k] = v if v != "" else None
        else:
            cleaned[k] = v
    return cleaned


@router.post("/questions/import")
async def import_questions(
    file: UploadFile = File(...),
    dry_run: bool = Query(False, description="true দিলে ডেটাবেসে সেভ হবে না, শুধু যাচাই করে রিপোর্ট দেখাবে"),
    db: Session = Depends(get_db),
    _: None = Depends(verify_admin_key),
):
    raw = await file.read()
    rows, is_csv = _parse_rows(file, raw)
    start = 2 if is_csv else 1  # CSV-তে হেডার লাইন ১, তাই প্রথম ডেটা রো লাইন ২

    inserted = 0
    skipped_duplicates = 0
    errors = []

    for idx, raw_row in enumerate(rows, start=start):
        row = _clean_row(raw_row)
        try:
            parsed = schemas.ExamQuestionImportRow(**row)
        except ValidationError as e:
            errors.append({"row": idx, "reason": e.errors()[0]["msg"].removeprefix("Value error, "), "data": row})
            continue

        subject = get_or_create_subject(db, parsed.subject_name)

        existing = (
            db.query(models.ExamQuestion)
            .filter(
                models.ExamQuestion.subject_id == subject.id,
                models.ExamQuestion.question_text == parsed.question_text,
            )
            .first()
        )
        if existing:
            skipped_duplicates += 1
            continue

        db.add(models.ExamQuestion(
            subject_id=subject.id,
            exam_name=parsed.exam_name,
            exam_year=parsed.exam_year,
            organization_name=parsed.organization_name,
            question_text=parsed.question_text,
            option_a=parsed.option_a,
            option_b=parsed.option_b,
            option_c=parsed.option_c,
            option_d=parsed.option_d,
            correct_answer=parsed.correct_answer,
            explanation=parsed.explanation,
            difficulty=parsed.difficulty,
            source=parsed.source,
        ))
        inserted += 1

    if dry_run:
        db.rollback()
    else:
        db.commit()

    return {
        "total_rows": len(rows),
        "inserted": 0 if dry_run else inserted,
        "would_insert": inserted if dry_run else None,
        "skipped_duplicates": skipped_duplicates,
        "errors": errors,
        "dry_run": dry_run,
    }


@router.post("/study-materials/import")
async def import_study_materials(
    file: UploadFile = File(...),
    dry_run: bool = Query(False, description="true দিলে ডেটাবেসে সেভ হবে না, শুধু যাচাই করে রিপোর্ট দেখাবে"),
    db: Session = Depends(get_db),
    _: None = Depends(verify_admin_key),
):
    raw = await file.read()
    rows, is_csv = _parse_rows(file, raw)
    start = 2 if is_csv else 1

    inserted = 0
    skipped_duplicates = 0
    errors = []

    for idx, raw_row in enumerate(rows, start=start):
        row = _clean_row(raw_row)
        try:
            parsed = schemas.StudyMaterialImportRow(**row)
        except ValidationError as e:
            errors.append({"row": idx, "reason": e.errors()[0]["msg"].removeprefix("Value error, "), "data": row})
            continue

        subject = get_or_create_subject(db, parsed.subject_name)

        existing = (
            db.query(models.StudyMaterial)
            .filter(
                models.StudyMaterial.subject_id == subject.id,
                models.StudyMaterial.title == parsed.title,
            )
            .first()
        )
        if existing:
            skipped_duplicates += 1
            continue

        db.add(models.StudyMaterial(
            subject_id=subject.id,
            title=parsed.title,
            content=parsed.content,
            topic_tags=parsed.topic_tags,
        ))
        inserted += 1

    if dry_run:
        db.rollback()
    else:
        db.commit()

    return {
        "total_rows": len(rows),
        "inserted": 0 if dry_run else inserted,
        "would_insert": inserted if dry_run else None,
        "skipped_duplicates": skipped_duplicates,
        "errors": errors,
        "dry_run": dry_run,
    }


QUESTION_TEMPLATE_CSV = (
    "subject_name,exam_name,exam_year,organization_name,question_text,"
    "option_a,option_b,option_c,option_d,correct_answer,explanation,difficulty,source\n"
    "বাংলা ব্যাকরণ ও সাহিত্য,৪৫তম BCS প্রিলি,2023,বাংলাদেশ সরকারী কর্ম কমিশন,"
    "\"'সমুদ্র' শব্দের সন্ধি বিচ্ছেদ কোনটি?\","
    "সম+উদ্র,সমু+দ্র,সম্+উদ্র,সমুদ+র,A,"
    "\"সম + উদ্র = সমুদ্র (ব্যঞ্জনসন্ধি)\",medium,manual\n"
)

STUDY_MATERIAL_TEMPLATE_CSV = (
    "subject_name,title,content,topic_tags\n"
    "সাধারণ গণিত,লসাগু ও গসাগু,\"লসাগু (LCM) ও গসাগু (GCD) নির্ণয়ের নিয়ম...\",\"গণিত,সংখ্যাতত্ত্ব\"\n"
)


@router.get("/questions/import/template", response_class=PlainTextResponse)
def question_import_template():
    return PlainTextResponse(content=QUESTION_TEMPLATE_CSV, media_type="text/csv")


@router.get("/study-materials/import/template", response_class=PlainTextResponse)
def study_material_import_template():
    return PlainTextResponse(content=STUDY_MATERIAL_TEMPLATE_CSV, media_type="text/csv")
