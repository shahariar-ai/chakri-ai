from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_

from database import get_db
import models
import schemas

router = APIRouter(prefix="/api/circulars", tags=["Job Circulars"])


@router.get("/", response_model=List[schemas.JobCircularOut])
def list_circulars(
    db: Session = Depends(get_db),
    category: Optional[str] = None,
    org_type: Optional[str] = None,
    search: Optional[str] = None,
    active_only: bool = True,
    skip: int = 0,
    limit: int = 30,
):
    query = db.query(models.JobCircular)

    if active_only:
        query = query.filter(models.JobCircular.is_active == True)  # noqa: E712
    if category:
        query = query.filter(models.JobCircular.category == category)
    if search:
        like = f"%{search}%"
        query = query.filter(
            or_(
                models.JobCircular.title.ilike(like),
                models.JobCircular.post_names.ilike(like),
            )
        )
    if org_type:
        query = query.join(models.Organization).filter(
            models.Organization.org_type == org_type
        )

    query = query.order_by(models.JobCircular.created_at.desc())
    return query.offset(skip).limit(limit).all()


@router.get("/{circular_id}", response_model=schemas.JobCircularOut)
def get_circular(circular_id: int, db: Session = Depends(get_db)):
    circular = db.query(models.JobCircular).filter(models.JobCircular.id == circular_id).first()
    if not circular:
        raise HTTPException(status_code=404, detail="সার্কুলার পাওয়া যায়নি")
    return circular


@router.post("/", response_model=schemas.JobCircularOut)
def create_circular(data: schemas.JobCircularCreate, db: Session = Depends(get_db)):
    """
    নতুন সার্কুলার যোগ করার এন্ডপয়েন্ট।
    স্ক্র্যাপার এবং ম্যানুয়াল অ্যাডমিন এন্ট্রি — দুটোই এই এন্ডপয়েন্ট ব্যবহার করবে।
    """
    circular = models.JobCircular(**data.model_dump())
    db.add(circular)
    db.commit()
    db.refresh(circular)
    return circular


@router.get("/categories/list")
def list_categories(db: Session = Depends(get_db)):
    """UI ফিল্টার ড্রপডাউনের জন্য বিদ্যমান ক্যাটাগরি লিস্ট"""
    rows = db.query(models.JobCircular.category).distinct().all()
    return [r[0] for r in rows if r[0]]
