"""
ডেটাবেস কানেকশন সেটআপ।
DATABASE_URL environment variable থেকে কানেকশন নেওয়া হয় (প্রোডাকশনে Render-এর PostgreSQL)।
না দিলে লোকাল ডেভেলপমেন্টের জন্য SQLite ফলব্যাক।
"""
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

load_dotenv()

SQLITE_FALLBACK_URL = "sqlite:///./chakri_ai.db"


def get_database_url() -> str:
    """DATABASE_URL পড়ে SQLAlchemy-বান্ধব রূপে ফেরত দেয় (alembic/env.py-ও এটা ব্যবহার করে)।"""
    url = os.getenv("DATABASE_URL", "").strip() or SQLITE_FALLBACK_URL
    # কিছু হোস্ট (Heroku, পুরনো Render) "postgres://" দেয় — SQLAlchemy 2.0 শুধু "postgresql://" চেনে
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://"):]
    return url


DATABASE_URL = get_database_url()

if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    # pool_pre_ping: Render ফ্রি DB idle কানেকশন কেটে দিলে পরের রিকোয়েস্টে যেন এরর না আসে
    engine = create_engine(DATABASE_URL, pool_pre_ping=True, pool_recycle=300)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
