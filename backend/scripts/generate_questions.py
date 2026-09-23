"""
Claude API দিয়ে BCS-স্টাইল MCQ প্রশ্ন generate করার স্ক্রিপ্ট।

চালানোর নিয়ম:
    cd backend
    python scripts/generate_questions.py

আউটপুট: admin bulk-import ফরম্যাটে (schemas.ExamQuestionImportRow) একটা JSON
ফাইল, review করার পর /api/admin/questions/import এ আপলোড করা যাবে।
"""
import json
import os
import sys

from dotenv import load_dotenv
import anthropic

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

QUESTIONS_PER_SUBJECT = 5
SUBJECTS = ["বাংলা ব্যাকরণ ও সাহিত্য", "ইংরেজি গ্রামার ও Vocabulary", "সাধারণ গণিত", "সাধারণ জ্ঞান (বাংলাদেশ বিষয়াবলি)", "বিজ্ঞান ও প্রযুক্তি"]

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


def build_prompt(subject: str, n: int) -> str:
    return f"""তুমি BCS প্রিলিমিনারি পরীক্ষার একজন প্রশ্ন প্রণেতা। "{subject}" বিষয়ে {n}টা
মৌলিক BCS-স্টাইল MCQ প্রশ্ন বানাও।

নিয়ম:
- প্রশ্নগুলো বাংলাদেশের BCS প্রিলি সিলেবাসের মান অনুযায়ী হতে হবে, খুব সহজ বা অস্পষ্ট নয়
- প্রতিটা প্রশ্নে ৪টা option (ক, খ, গ, ঘ) থাকবে, একটাই সঠিক উত্তর
- প্রশ্ন ও option বাংলায় লিখো (ইংরেজি বিষয় হলে প্রশ্নের নির্দেশনা বাংলায়, কিন্তু ইংরেজি ভাষাগত অংশ ইংরেজিতেই থাকবে)
- একই প্রশ্ন দুইবার দিও না, বিষয়ের বিভিন্ন উপ-টপিক থেকে বৈচিত্র্য রাখো
- এটা মৌলিক (original) প্রশ্ন হতে হবে, কোনো নির্দিষ্ট ওয়েবসাইট বা বইয়ের প্রশ্ন হুবহু কপি নয়

আউটপুট **শুধু** একটা valid JSON array দাও, অন্য কোনো টেক্সট নয়। প্রতিটা আইটেমের ফরম্যাট:
{{
  "question_text": "...",
  "option_a": "...",
  "option_b": "...",
  "option_c": "...",
  "option_d": "...",
  "correct_answer": "A"
}}
correct_answer অবশ্যই "A", "B", "C", অথবা "D" এর একটা হতে হবে (option_a=A, option_b=B, ...)।
"""


def generate_for_subject(subject: str, n: int) -> list[dict]:
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2000,
        messages=[{"role": "user", "content": build_prompt(subject, n)}],
    )
    raw = message.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.strip("`")
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()
    items = json.loads(raw)

    rows = []
    for item in items:
        rows.append({
            "subject_name": subject,
            "exam_name": None,
            "exam_year": None,
            "organization_name": None,
            "question_text": item["question_text"],
            "option_a": item["option_a"],
            "option_b": item["option_b"],
            "option_c": item["option_c"],
            "option_d": item["option_d"],
            "correct_answer": item["correct_answer"],
            "explanation": None,
            "difficulty": "medium",
            "source": "claude_ai_generated",
        })
    return rows


def main():
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("ANTHROPIC_API_KEY সেট করা নেই (.env দেখুন)")
        sys.exit(1)

    all_rows = []
    for subject in SUBJECTS:
        print(f"generating: {subject} ...")
        rows = generate_for_subject(subject, QUESTIONS_PER_SUBJECT)
        print(f"  -> {len(rows)}টা প্রশ্ন পাওয়া গেছে")
        all_rows.extend(rows)

    out_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "generated_questions_sample.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(all_rows, f, ensure_ascii=False, indent=2)

    print(f"\nমোট {len(all_rows)}টা প্রশ্ন সেভ হয়েছে: {out_path}")


if __name__ == "__main__":
    main()
