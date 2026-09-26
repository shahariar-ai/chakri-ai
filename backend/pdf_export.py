"""
Resume/Cover letter টেক্সট -> PDF।

কেন ব্যাকএন্ডে: Flutter-এর `pdf` প্যাকেজ বাংলা shaping করে না — যুক্তাক্ষর ভেঙে যায়,
ি/ে-কার অক্ষরের পরে বসে। fpdf2 + uharfbuzz (HarfBuzz) দিয়ে সঠিক বাংলা রেন্ডার হয়,
আর টেক্সট সিলেক্টেবল থাকে (ATS সফটওয়্যার PDF থেকে টেক্সট পড়তে পারে)।

ফন্ট: backend/fonts/Hind Siliguri (SIL OFL, লাইসেন্স fonts/OFL-HindSiliguri.txt) — একই ফন্টে বাংলা ও ইংরেজি দুটোই আছে।
দুই ফন্ট (Noto Sans Bengali + Noto Sans fallback) দিয়ে চেষ্টা করা হয়েছিল: fpdf2-এর fallback লাইন ইংরেজি চিহ্ন দিয়ে
শুরু হলে ("- ঋণ...") বাংলা অংশ হারায়, আর write() দিয়ে ফন্ট বদলালে র‍্যাপ শব্দের মাঝখানে ভাঙে।
"""

import os
import re

from fpdf import FPDF

FONT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")

# এই নামের লাইন হেডিং ধরা হবে (বোল্ড) — AI প্লেইন টেক্সটে হেডিং আলাদা লাইনে দেয়
SECTION_HEADINGS = {
    "summary", "professional summary", "career objective", "objective", "skills", "key skills",
    "experience", "work experience", "professional experience", "education", "educational qualification",
    "certifications", "training", "languages", "references", "personal information", "contact",
    "core skills", "technical skills", "projects", "academic projects", "achievements", "awards",
    "additional information", "career summary", "personal details", "declaration",
    "অতিরিক্ত তথ্য", "প্রকল্প", "অর্জন", "কারিগরি দক্ষতা",
    "সারসংক্ষেপ", "পেশাগত সারসংক্ষেপ", "ক্যারিয়ার উদ্দেশ্য", "উদ্দেশ্য", "দক্ষতা", "মূল দক্ষতা",
    "অভিজ্ঞতা", "কর্ম অভিজ্ঞতা", "কাজের অভিজ্ঞতা", "পেশাগত অভিজ্ঞতা", "শিক্ষা", "শিক্ষাগত যোগ্যতা",
    "প্রশিক্ষণ", "ভাষা", "রেফারেন্স", "ব্যক্তিগত তথ্য", "যোগাযোগ",
}


def _is_heading(line: str) -> bool:
    stripped = re.sub(r"[:：\s]+$", "", line.strip())
    if stripped.lower() in SECTION_HEADINGS:
        return True
    # তালিকায় নেই এমন ছোট ALL-CAPS ইংরেজি লাইনও হেডিং (যেমন "VOLUNTEER WORK")
    return 3 <= len(stripped) <= 40 and stripped.isupper() and re.fullmatch(r"[A-Z][A-Z &/()-]*", stripped) is not None


class _PDF(FPDF):
    def footer(self):
        self.set_y(-12)
        self.set_font("body", size=8)
        self.set_text_color(150)
        self.cell(0, 6, str(self.page_no()), align="C")


def text_to_pdf(text: str) -> bytes:
    """প্রথম লাইন (নাম) বড় করে, সেকশন হেডিং বোল্ড করে A4 PDF বানায়।"""
    pdf = _PDF(format="A4")
    pdf.set_margins(18, 16, 18)
    pdf.set_auto_page_break(True, margin=16)
    pdf.add_font("body", "", os.path.join(FONT_DIR, "HindSiliguri-Regular.ttf"))
    pdf.add_font("body", "B", os.path.join(FONT_DIR, "HindSiliguri-Bold.ttf"))
    # script না দিলে HarfBuzz লাইনের প্রথম অক্ষর দেখে script ধরে — ইংরেজি দিয়ে শুরু লাইনে বাংলা রেফ/যুক্তাক্ষর ভাঙে।
    # Bengali shaper ইংরেজি অক্ষর স্বাভাবিকভাবেই রাখে।
    pdf.set_text_shaping(use_shaping_engine=True, script="beng", language="ben")
    pdf.add_page()

    lines = text.strip().splitlines()
    for i, raw in enumerate(lines):
        line = raw.rstrip()
        if not line.strip():
            pdf.ln(3)
            continue
        if i == 0:
            pdf.set_font("body", "B", 17)
            pdf.multi_cell(0, 9, line.strip(), new_x="LMARGIN", new_y="NEXT")
            pdf.ln(1)
        elif _is_heading(line):
            pdf.ln(2)
            pdf.set_font("body", "B", 12.5)
            pdf.multi_cell(0, 7, line.strip(), new_x="LMARGIN", new_y="NEXT")
            # হেডিংয়ের নিচে পাতলা দাগ
            pdf.set_draw_color(180)
            pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
            pdf.ln(1.5)
        else:
            # "- " / "* " বুলেটকে আসল বুলেট চিহ্নে বদলানো
            line = re.sub(r"^(\s*)[-*]\s+", r"\1• ", line)
            pdf.set_font("body", "", 10.5)
            pdf.multi_cell(0, 6, line, new_x="LMARGIN", new_y="NEXT")
    return bytes(pdf.output())

