"""
Claude API দিয়ে দ্বিতীয় ব্যাচের BCS/সরকারি চাকরি পরীক্ষার MCQ প্রশ্ন generate করার স্ক্রিপ্ট।
আগের generate_questions.py-এর প্রম্পট স্টাইল অনুসরণ করে, কিন্তু বিষয়প্রতি ২৫টা করে প্রশ্ন
(টোকেন-লিমিট এড়াতে প্রতি সাবজেক্ট ৩টা চাঙ্কে - ১০+১০+৫ - জেনারেট হয়)।

চালানোর নিয়ম:
    cd backend
    python scripts/generate_questions_batch2.py

আউটপুট: admin bulk-import ফরম্যাটে generated_questions_batch2.json
"""
import json
import os
import sys

from dotenv import load_dotenv
import anthropic

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

QUESTIONS_PER_SUBJECT = 25
CHUNK_SIZES = [10, 10, 5]
SUBJECTS = [
    "বাংলা ব্যাকরণ ও সাহিত্য",
    "ইংরেজি গ্রামার ও Vocabulary",
    "সাধারণ গণিত",
    "সাধারণ জ্ঞান (বাংলাদেশ বিষয়াবলি)",
    "আন্তর্জাতিক বিষয়াবলি ও কারেন্ট অ্যাফেয়ার্স",
    "বিজ্ঞান ও প্রযুক্তি",
    "কম্পিউটার ও তথ্যপ্রযুক্তি",
]

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

usage_totals = {"input_tokens": 0, "output_tokens": 0}


def build_prompt(subject: str, n: int, avoid: list[str]) -> str:
    avoid_block = ""
    if avoid:
        avoid_list = "\n".join(f"- {q}" for q in avoid)
        avoid_block = f"\nনিচের প্রশ্নগুলো ইতিমধ্যে ব্যবহৃত হয়েছে, এগুলোর পুনরাবৃত্তি বা প্যারাফ্রেজ কোরো না:\n{avoid_list}\n"

    return f"""তুমি বাংলাদেশ সরকারি চাকরি (BCS ও অন্যান্য সরকারি নিয়োগ পরীক্ষা) প্রিলিমিনারির একজন
প্রশ্ন প্রণেতা। "{subject}" বিষয়ে {n}টা মৌলিক MCQ প্রশ্ন বানাও।

নিয়ম:
- প্রশ্নগুলো বাংলাদেশের সরকারি চাকরি পরীক্ষার (BCS প্রিলি মানের) সিলেবাস অনুযায়ী হতে হবে, খুব সহজ বা অস্পষ্ট নয়
- প্রতিটা প্রশ্নে ৪টা option (ক, খ, গ, ঘ) থাকবে, একটাই সঠিক উত্তর
- প্রশ্ন ও option বাংলায় লিখো (ইংরেজি/কম্পিউটার-সম্পর্কিত বিষয় হলে প্রশ্নের নির্দেশনা বাংলায়, কিন্তু ইংরেজি ভাষাগত/টেকনিক্যাল অংশ ইংরেজিতেই থাকবে)
- একই প্রশ্ন দুইবার দিও না, বিষয়ের বিভিন্ন উপ-টপিক থেকে বৈচিত্র্য রাখো
- এটা মৌলিক (original) প্রশ্ন হতে হবে, কোনো নির্দিষ্ট ওয়েবসাইট বা বইয়ের প্রশ্ন হুবহু কপি নয়
- correct_answer অবশ্যই factually সঠিক হতে হবে - গাণিতিক প্রশ্নে হিসাব ভালোভাবে যাচাই করে নিও
- প্রতিটা প্রশ্নের জন্য একটা সংক্ষিপ্ত explanation দাও যা correct_answer-কে যুক্তি দিয়ে সমর্থন করে
{avoid_block}
আউটপুট **শুধু** একটা valid JSON array দাও, অন্য কোনো টেক্সট নয়। প্রতিটা আইটেমের ফরম্যাট:
{{
  "question_text": "...",
  "option_a": "...",
  "option_b": "...",
  "option_c": "...",
  "option_d": "...",
  "correct_answer": "A",
  "explanation": "..."
}}
correct_answer অবশ্যই "A", "B", "C", অথবা "D" এর একটা হতে হবে (option_a=A, option_b=B, ...)।
"""


def generate_chunk(subject: str, n: int, avoid: list[str]) -> list[dict]:
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=6000,
        messages=[{"role": "user", "content": build_prompt(subject, n, avoid)}],
    )
    usage_totals["input_tokens"] += message.usage.input_tokens
    usage_totals["output_tokens"] += message.usage.output_tokens

    raw = message.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.strip("`")
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()
    return json.loads(raw)


def generate_for_subject(subject: str) -> list[dict]:
    all_items = []
    seen_texts = []
    for chunk_n in CHUNK_SIZES:
        items = generate_chunk(subject, chunk_n, seen_texts)
        all_items.extend(items)
        seen_texts.extend(item["question_text"] for item in items)

    rows = []
    for item in all_items:
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
            "explanation": item.get("explanation"),
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
        rows = generate_for_subject(subject)
        print(f"  -> {len(rows)}টা প্রশ্ন পাওয়া গেছে")
        all_rows.extend(rows)

    out_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "generated_questions_batch2.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(all_rows, f, ensure_ascii=False, indent=2)

    print(f"\nমোট {len(all_rows)}টা প্রশ্ন সেভ হয়েছে: {out_path}")
    print(f"টোকেন ব্যবহার -> input: {usage_totals['input_tokens']}, output: {usage_totals['output_tokens']}")


if __name__ == "__main__":
    main()
