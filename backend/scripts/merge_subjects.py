"""
কাছাকাছি নামের duplicate Subject গুলোকে একটা canonical Subject-এ merge করার স্ক্রিপ্ট।
প্রশ্ন ও স্টাডি ম্যাটেরিয়াল canonical subject-এ সরানো হয়, তারপর পুরনো subject মুছে ফেলা হয়।
canonical subject-এ হুবহু একই question_text/title আগে থেকে থাকলে সরানো রো-টা মুছে ফেলা হয়
(import-এর duplicate check-এর মতোই)।

চালানোর নিয়ম:
    cd backend
    python scripts/merge_subjects.py            # শুধু রিপোর্ট দেখাবে (dry run)
    python scripts/merge_subjects.py --apply    # ডেটাবেসে পরিবর্তন সেভ করবে
"""
import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import SessionLocal
import models

# পুরনো নাম -> canonical নাম
SUBJECT_MERGES = {
    "বাংলা": "বাংলা ব্যাকরণ ও সাহিত্য",
    "ইংরেজি": "ইংরেজি গ্রামার ও Vocabulary",
    "সাধারণ জ্ঞান": "সাধারণ জ্ঞান (বাংলাদেশ বিষয়াবলি)",
    "বিজ্ঞান": "বিজ্ঞান ও প্রযুক্তি",
    "গণিত": "সাধারণ গণিত",
}

# merge-এর আগে ভুল subject-এ থাকা নির্দিষ্ট প্রশ্ন সঠিক subject-এ সরানো (question_text-এর অংশ -> subject নাম)
QUESTION_MOVES = {
    "জাতিসংঘের নিরাপত্তা পরিষদে মোট সদস্য সংখ্যা": "আন্তর্জাতিক বিষয়াবলি ও কারেন্ট অ্যাফেয়ার্স",
    "বিশ্ব বাণিজ্য সংস্থা (WTO)-এর সদর দপ্তর": "আন্তর্জাতিক বিষয়াবলি ও কারেন্ট অ্যাফেয়ার্স",
}


def get_subject(db, name):
    return db.query(models.Subject).filter(models.Subject.name == name).first()


def move_question(db, q, target, stats):
    dup = (
        db.query(models.ExamQuestion)
        .filter(
            models.ExamQuestion.subject_id == target.id,
            models.ExamQuestion.question_text == q.question_text,
            models.ExamQuestion.id != q.id,
        )
        .first()
    )
    if dup:
        db.delete(q)
        stats["deleted_duplicates"] += 1
    else:
        q.subject_id = target.id
        stats["moved_questions"] += 1


def main():
    apply = "--apply" in sys.argv
    db = SessionLocal()
    stats = {"moved_questions": 0, "moved_materials": 0, "deleted_duplicates": 0, "deleted_subjects": 0}

    try:
        for fragment, target_name in QUESTION_MOVES.items():
            target = get_subject(db, target_name)
            q = db.query(models.ExamQuestion).filter(models.ExamQuestion.question_text.contains(fragment)).first()
            if not target or not q:
                print(f"  [skip] পাওয়া যায়নি: {fragment}")
                continue
            if q.subject_id != target.id:
                print(f"  প্রশ্ন সরানো হচ্ছে -> {target_name}: {q.question_text[:50]}...")
                move_question(db, q, target, stats)
        db.flush()

        for old_name, target_name in SUBJECT_MERGES.items():
            old = get_subject(db, old_name)
            target = get_subject(db, target_name)
            if not old:
                print(f"  [skip] '{old_name}' নেই (আগেই merge হয়ে থাকতে পারে)")
                continue
            if not target:
                print(f"  [skip] canonical '{target_name}' নেই")
                continue

            print(f"'{old_name}' -> '{target_name}'")
            for q in list(old.questions):
                move_question(db, q, target, stats)

            for m in list(old.study_materials):
                dup = (
                    db.query(models.StudyMaterial)
                    .filter(models.StudyMaterial.subject_id == target.id, models.StudyMaterial.title == m.title)
                    .first()
                )
                if dup:
                    db.delete(m)
                    stats["deleted_duplicates"] += 1
                else:
                    m.subject_id = target.id
                    stats["moved_materials"] += 1

            if not target.description and old.description:
                target.description = old.description
            db.flush()
            db.expire(old)
            db.delete(old)
            stats["deleted_subjects"] += 1

        if apply:
            db.commit()
        else:
            db.rollback()
    finally:
        db.close()

    print(f"\n{'APPLIED' if apply else 'DRY RUN (সেভ হয়নি, --apply দিন)'}: {stats}")


if __name__ == "__main__":
    main()
