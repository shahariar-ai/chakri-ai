"""
মূল ডেটাবেস মডেল:
- Organization: যে প্রতিষ্ঠান নিয়োগ দিচ্ছে (সরকারি/বেসরকারি)
- JobCircular: চাকরির সার্কুলার
- Subject: প্রশ্নের বিষয় (বাংলা, ইংরেজি, গণিত, সাধারণ জ্ঞান, ইত্যাদি)
- ExamQuestion: প্রশ্ন ব্যাংক
- StudyMaterial: বিষয়ভিত্তিক পড়ার কনটেন্ট
- DeviceToken: পুশ নোটিফিকেশনের জন্য FCM টোকেন
"""
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, ForeignKey, Boolean, Enum as SqlEnum
)
from sqlalchemy.orm import relationship
from database import Base
import enum


class OrgType(str, enum.Enum):
    government = "government"
    semi_government = "semi_government"
    private = "private"
    bank = "bank"
    ngo = "ngo"


class Organization(Base):
    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    name_bn = Column(String(255))
    org_type = Column(SqlEnum(OrgType), default=OrgType.government)
    website = Column(String(500))

    circulars = relationship("JobCircular", back_populates="organization")


class JobCircular(Base):
    __tablename__ = "job_circulars"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"))
    post_names = Column(Text)  # একাধিক পদ হলে কমা-সেপারেটেড
    vacancy_count = Column(String(50))
    qualification = Column(Text)
    age_limit = Column(String(100))
    salary_range = Column(String(200))
    application_start = Column(DateTime, nullable=True)
    application_deadline = Column(DateTime, nullable=True, index=True)
    exam_date = Column(DateTime, nullable=True)
    source_url = Column(String(1000))
    circular_image_url = Column(String(1000))  # অনেক সার্কুলার ছবি/PDF আকারে থাকে
    full_text = Column(Text)  # scraped raw text (OCR/parsed)
    category = Column(String(100))  # e.g. "Bank Job", "BCS", "Primary Teacher"
    scraped_from = Column(String(100))  # কোন সোর্স থেকে এসেছে
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    notified = Column(Boolean, default=False)  # push notification পাঠানো হয়েছে কিনা

    organization = relationship("Organization", back_populates="circulars")


class Subject(Base):
    __tablename__ = "subjects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), nullable=False, unique=True)  # e.g. বাংলা, ইংরেজি, গণিত, সাধারণ জ্ঞান
    description = Column(Text)

    questions = relationship("ExamQuestion", back_populates="subject")
    study_materials = relationship("StudyMaterial", back_populates="subject")


class ExamQuestion(Base):
    __tablename__ = "exam_questions"

    id = Column(Integer, primary_key=True, index=True)
    subject_id = Column(Integer, ForeignKey("subjects.id"))
    exam_name = Column(String(300))  # e.g. "৪৫তম BCS", "সোনালী ব্যাংক সিনিয়র অফিসার ২০২৩"
    exam_year = Column(Integer, index=True)
    organization_name = Column(String(255))  # কোন প্রতিষ্ঠানের পরীক্ষা
    question_text = Column(Text, nullable=False)
    option_a = Column(String(500))
    option_b = Column(String(500))
    option_c = Column(String(500))
    option_d = Column(String(500))
    correct_answer = Column(String(10))  # "A" / "B" / "C" / "D" অথবা লিখিত উত্তর
    explanation = Column(Text, nullable=True)
    difficulty = Column(String(20), default="medium")  # easy/medium/hard
    source = Column(String(200))  # ডেটা কোথা থেকে এসেছে (manual/scraped)
    created_at = Column(DateTime, default=datetime.utcnow)

    subject = relationship("Subject", back_populates="questions")


class StudyMaterial(Base):
    __tablename__ = "study_materials"

    id = Column(Integer, primary_key=True, index=True)
    subject_id = Column(Integer, ForeignKey("subjects.id"))
    title = Column(String(300), nullable=False)
    content = Column(Text, nullable=False)  # markdown/rich text
    topic_tags = Column(String(300))  # কমা-সেপারেটেড ট্যাগ
    created_at = Column(DateTime, default=datetime.utcnow)

    subject = relationship("Subject", back_populates="study_materials")


class DeviceToken(Base):
    """পুশ নোটিফিকেশনের জন্য ব্যবহারকারীর ডিভাইস টোকেন (Firebase Cloud Messaging)"""
    __tablename__ = "device_tokens"

    id = Column(Integer, primary_key=True, index=True)
    token = Column(String(500), unique=True, nullable=False)
    platform = Column(String(20), default="android")
    # ব্যবহারকারীর আগ্রহের ক্যাটাগরি (ঐচ্ছিক ফিল্টারিং-এর জন্য) - কমা সেপারেটেড
    preferred_categories = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_active = Column(DateTime, default=datetime.utcnow)


class PaymentStatus(str, enum.Enum):
    pending = "pending"
    completed = "completed"
    failed = "failed"
    cancelled = "cancelled"


class Payment(Base):
    """
    প্রিমিয়াম সাবস্ক্রিপশনের পেমেন্ট (bKash/Nagad)।
    আলাদা Subscription টেবিল নেই — completed পেমেন্টগুলো থেকেই মেয়াদ হিসাব করা হয়।
    subscriber_id: অ্যাপ প্রথমবার চালু হলে যে random ID বানায় (এখনো user login নেই)।
    """
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    subscriber_id = Column(String(64), nullable=False, index=True)
    plan_code = Column(String(32), nullable=False)
    amount = Column(Integer, nullable=False)  # টাকা (BDT), পূর্ণসংখ্যা
    provider = Column(String(16), nullable=False)  # bkash | nagad | mock
    status = Column(SqlEnum(PaymentStatus), default=PaymentStatus.pending, nullable=False, index=True)
    provider_payment_id = Column(String(128), index=True)  # bKash paymentID
    trx_id = Column(String(64))  # সফল হলে প্রোভাইডারের ট্রানজেকশন আইডি
    failure_reason = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
