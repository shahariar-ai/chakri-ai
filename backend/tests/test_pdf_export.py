"""Resume PDF export টেস্ট — বাংলা shaping (HarfBuzz) ঠিকমতো হচ্ছে কিনা।"""
import pytest

from pdf_export import text_to_pdf

pymupdf = pytest.importorskip("pymupdf")  # PDF পড়ে টেক্সট/ফন্ট যাচাইয়ের জন্য (dev-only)

SAMPLE = "রাকিব হাসান\nসারসংক্ষেপ\nব্যাংকিং ক্ষেত্রে অভিজ্ঞতা\n- Senior Officer (2019 - বর্তমান)\nSkills\n- MS Excel"


def _open(data: bytes):
    return pymupdf.open(stream=data, filetype="pdf")


def test_pdf_embeds_bangla_font_and_keeps_english_text():
    doc = _open(text_to_pdf(SAMPLE))
    fonts = {f[3] for f in doc[0].get_fonts()}
    assert any("HindSiliguri" in f for f in fonts), fonts
    text = doc[0].get_text()
    assert "Senior Officer (2019 -" in text and "• MS Excel" in text  # "- " বুলেট -> •


def test_bangla_is_shaped_not_raw_codepoints():
    # shaping হলে 'ক্ষ' যুক্তাক্ষর একটা glyph হয় — কাঁচা codepoint-প্রতি-glyph (Flutter pdf-এর মত) হলে হতো না
    doc = _open(text_to_pdf("ক্ষ"))
    # texttrace: (unicode, glyph_id, ...) — একই glyph-এর বাকি অক্ষরে glyph_id -1
    # footer-এর পেজ নম্বর বাদ দিতে শুধু প্রথম লাইনের (17pt) glyph
    glyphs = [c[1] for b in doc[0].get_texttrace() if b["size"] > 15 for c in b["chars"] if c[1] != -1]
    assert len(glyphs) == 1


def test_long_text_spans_multiple_pages():
    body = "\n".join(f"- লাইন {i}: অভিজ্ঞতা ও দক্ষতা" for i in range(120))
    assert _open(text_to_pdf("নাম\n" + body)).page_count >= 2


def test_pdf_endpoint(client):
    r = client.post("/api/resume/pdf", json={"text": SAMPLE})
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/pdf"
    assert r.content.startswith(b"%PDF")


@pytest.mark.parametrize("body", [{"text": ""}, {}, {"text": "x" * 20001}])
def test_pdf_endpoint_validation(client, body):
    assert client.post("/api/resume/pdf", json=body).status_code == 422


@pytest.mark.parametrize("line, expected", [
    ("Skills", True), ("CORE SKILLS", True), ("দক্ষতা:", True), ("VOLUNTEER WORK", True),
    ("MS Excel", False), ("BBA (2023)", False), ("- MS WORD", False), ("রাকিব হাসান", False),
])
def test_heading_detection(line, expected):
    from pdf_export import _is_heading
    assert _is_heading(line) is expected
