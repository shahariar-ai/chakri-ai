from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
import models
import schemas

router = APIRouter(prefix="/api/questions", tags=["Question Bank"])
study_router = APIRouter(prefix="/api/study", tags=["Study Material"])


# ---------- Subjects ----------
@router.get("/subjects", response_model=List[schemas.SubjectOut])
def list_subjects(db: Session = Depends(get_db)):
    return db.query(models.Subject).all()


@router.post("/subjects", response_model=schemas.SubjectOut)
def create_subject(name: str, description: Optional[str] = None, db: Session = Depends(get_db)):
    existing = db.query(models.Subject).filter(models.Subject.name == name).first()
    if existing:
        return existing
    subject = models.Subject(name=name, description=description)
    db.add(subject)
    db.commit()
    db.refresh(subject)
    return subject


# ---------- Questions ----------
@router.get("/", response_model=List[schemas.ExamQuestionOut])
def list_questions(
    db: Session = Depends(get_db),
    subject_id: Optional[int] = None,
    exam_year: Optional[int] = None,
    organization_name: Optional[str] = None,
    skip: int = 0,
    limit: int = 30,
):
    query = db.query(models.ExamQuestion)
    if subject_id:
        query = query.filter(models.ExamQuestion.subject_id == subject_id)
    if exam_year:
        query = query.filter(models.ExamQuestion.exam_year == exam_year)
    if organization_name:
        query = query.filter(models.ExamQuestion.organization_name.ilike(f"%{organization_name}%"))

    query = query.order_by(models.ExamQuestion.exam_year.desc())
    return query.offset(skip).limit(limit).all()


@router.post("/", response_model=schemas.ExamQuestionOut)
def create_question(data: schemas.ExamQuestionCreate, db: Session = Depends(get_db)):
    question = models.ExamQuestion(**data.model_dump())
    db.add(question)
    db.commit()
    db.refresh(question)
    return question


@router.post("/bulk", response_model=dict)
def bulk_create_questions(data: List[schemas.ExamQuestionCreate], db: Session = Depends(get_db)):
    """
    একসাথে অনেক প্রশ্ন ইম্পোর্ট করার জন্য (যেমন পুরনো প্রশ্নব্যাংক PDF থেকে পার্স করে বাল্ক আপলোড)
    """
    objs = [models.ExamQuestion(**item.model_dump()) for item in data]
    db.add_all(objs)
    db.commit()
    return {"inserted": len(objs)}


# ---------- Study Material ----------
@study_router.get("/", response_model=List[schemas.StudyMaterialOut])
def list_study_material(subject_id: Optional[int] = None, db: Session = Depends(get_db)):
    query = db.query(models.StudyMaterial)
    if subject_id:
        query = query.filter(models.StudyMaterial.subject_id == subject_id)
    return query.all()


@study_router.get("/{material_id}", response_model=schemas.StudyMaterialOut)
def get_study_material(material_id: int, db: Session = Depends(get_db)):
    material = db.query(models.StudyMaterial).filter(models.StudyMaterial.id == material_id).first()
    if not material:
        raise HTTPException(status_code=404, detail="কনটেন্ট পাওয়া যায়নি")
    return material
