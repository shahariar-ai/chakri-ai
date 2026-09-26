"""
লোকাল SQLite ডেটাবেসের সব ডেটা (প্রশ্ন, সার্কুলার, স্টাডি ম্যাটেরিয়াল, পেমেন্ট ইত্যাদি)
PostgreSQL-এ (যেমন Render-এর DB) কপি করার স্ক্রিপ্ট। একবারই চালানোর জন্য।

শর্ত:
  - টার্গেট DB-তে আগে migration চালানো থাকতে হবে (Render-এ start command নিজেই
    `alembic upgrade head` চালায়, তাই প্রথম ডিপ্লয়ের পরে এটা হয়ে যায়)
  - টার্গেট টেবিলগুলো খালি থাকতে হবে (দুবার চালিয়ে ডুপ্লিকেট হওয়া ঠেকাতে)
  - পুরো কপি এক ট্রানজেকশনে — কোনো রো-তে এরর হলে কিছুই সেভ হবে না

চালানোর নিয়ম (PowerShell):
    cd backend
    $env:TARGET_DATABASE_URL="postgresql://user:pass@host/dbname"   # Render-এর External Database URL
    python scripts/copy_sqlite_to_postgres.py                  # শুধু রিপোর্ট (dry run)
    python scripts/copy_sqlite_to_postgres.py --apply          # আসলে কপি করবে
    python scripts/copy_sqlite_to_postgres.py --source other.db --apply
"""
import argparse
import os
import sys

for _stream in (sys.stdout, sys.stderr):  # sys.exit()-এর বার্তা stderr-এ যায়
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, func, inspect, select, text  # noqa: E402

import models  # noqa: E402  - সব টেবিল Base.metadata-তে রেজিস্টার হয়
from database import Base  # noqa: E402


def normalize_pg_url(url: str) -> str:
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://"):]
    return url


def main():
    parser = argparse.ArgumentParser(description="SQLite -> PostgreSQL ডেটা কপি")
    parser.add_argument("--source", default="chakri_ai.db", help="SQLite ফাইলের পাথ (ডিফল্ট: chakri_ai.db)")
    parser.add_argument("--apply", action="store_true", help="না দিলে শুধু রিপোর্ট দেখাবে")
    args = parser.parse_args()

    target_url = normalize_pg_url(os.getenv("TARGET_DATABASE_URL", "").strip())
    if not target_url.startswith("postgresql"):
        sys.exit("TARGET_DATABASE_URL environment variable-এ PostgreSQL URL দিন (postgresql://...)")
    if not os.path.exists(args.source):
        sys.exit(f"SQLite ফাইল পাওয়া যায়নি: {args.source}")

    src = create_engine(f"sqlite:///{args.source}")
    dst = create_engine(target_url)

    dst_tables = set(inspect(dst).get_table_names())
    if "alembic_version" not in dst_tables:
        sys.exit("টার্গেট DB-তে migration চালানো হয়নি — আগে `alembic upgrade head` চালান (বা একবার ডিপ্লয় করুন)")

    # ForeignKey অনুযায়ী সাজানো (organizations, subjects আগে; job_circulars, exam_questions পরে)
    tables = [t for t in Base.metadata.sorted_tables if t.name in dst_tables]
    src_tables = set(inspect(src).get_table_names())

    with src.connect() as s, dst.begin() as d:
        plan = []
        for table in tables:
            if table.name not in src_tables:
                print(f"  {table.name:20} SQLite-এ টেবিল নেই, বাদ")
                continue
            rows = [dict(r._mapping) for r in s.execute(select(table))]
            existing = d.execute(select(func.count()).select_from(table)).scalar()
            if existing:
                sys.exit(f"টার্গেট টেবিল {table.name}-এ আগে থেকেই {existing}টা রো আছে — খালি DB-তেই শুধু কপি করা যায়")
            plan.append((table, rows))
            print(f"  {table.name:20} {len(rows):5} রো")

        if not args.apply:
            print("\nDry run — কিছু লেখা হয়নি। কপি করতে --apply দিন।")
            return

        for table, rows in plan:
            if rows:
                d.execute(table.insert(), rows)
            # id নিজে বসানো হয়েছে, তাই PostgreSQL-এর auto-increment sequence-কে max(id)-এ এগিয়ে দিতে হবে,
            # নইলে পরের নতুন রো "duplicate key" এরর দেবে
            if "id" in table.c:
                d.execute(text(
                    f"SELECT setval(pg_get_serial_sequence('{table.name}', 'id'), "
                    f"COALESCE((SELECT MAX(id) FROM {table.name}), 0) + 1, false)"
                ))

    print("\n✅ কপি সম্পূর্ণ।")


if __name__ == "__main__":
    main()
