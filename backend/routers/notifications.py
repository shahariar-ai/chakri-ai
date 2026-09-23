from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime

from database import get_db
import models
import schemas

router = APIRouter(prefix="/api/notifications", tags=["Notifications"])


@router.post("/register-device")
def register_device(data: schemas.DeviceTokenRegister, db: Session = Depends(get_db)):
    """Flutter অ্যাপ থেকে FCM ডিভাইস টোকেন রেজিস্টার করার এন্ডপয়েন্ট"""
    existing = db.query(models.DeviceToken).filter(models.DeviceToken.token == data.token).first()
    if existing:
        existing.preferred_categories = data.preferred_categories
        existing.last_active = datetime.utcnow()
        db.commit()
        return {"status": "updated"}

    device = models.DeviceToken(
        token=data.token,
        platform=data.platform,
        preferred_categories=data.preferred_categories,
    )
    db.add(device)
    db.commit()
    return {"status": "registered"}


@router.delete("/unregister-device/{token}")
def unregister_device(token: str, db: Session = Depends(get_db)):
    device = db.query(models.DeviceToken).filter(models.DeviceToken.token == token).first()
    if device:
        db.delete(device)
        db.commit()
    return {"status": "removed"}
