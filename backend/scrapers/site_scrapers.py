"""
সাইট-নির্দিষ্ট স্ক্র্যাপার।

⚠️ bdjobs.com নিয়ে গুরুত্বপূর্ণ নোট (২০২৬-০৯-১০ এ যাচাই করা):
bdjobs.com এর robots.txt (https://jobs.bdjobs.com/robots.txt) স্পষ্টভাবে বলছে:
    User-agent: *
    Disallow: /
শুধু Google, Bing, Yahoo, Facebook ও কিছু নির্দিষ্ট SEO টুল (Screaming Frog,
Visual SEO Studio) কে allow করা হয়েছে - আমাদের মতো জেনেরিক bot এর জন্য পুরো
সাইট Disallow। তাই এই ফাইলে bdjobs.com এর জন্য কোনো কার্যকর scraper লেখা হয়নি -
মালিকের সাথে আলোচনা করে এটা ইচ্ছাকৃতভাবে স্কিপ করা হয়েছে (robots.txt honor
করার সিদ্ধান্ত)। ভবিষ্যতে bdjobs.com এর official API/পার্টনারশিপ পাওয়া গেলে,
বা robots.txt বদলালে, তখন আবার বিবেচনা করা যেতে পারে।

✅ bpsc.gov.bd - এই সাইটে robots.txt নেই (৪০৪), তাই এটার জন্য আসল scraper
নিচে লেখা হয়েছে এবং বাস্তব ডেটা দিয়ে টেস্ট করা হয়েছে।

BPSC এর "নোটিশ" পোর্টাল (https://bpsc.gov.bd/pages/notices) সম্পর্কে যা জানা গেছে:
- লিস্টিং পেজ সার্ভার-সাইড রেন্ডারড HTML টেবিল (`table#noticeTable`) - JS ছাড়াই
  পার্স করা যায়।
- `?page=1&page_size=100` কুয়েরি প্যারামিটার দিয়ে একসাথে অনেকগুলো রো আনা যায়
  (যাচাই করা হয়েছে - পুরো ৩৯টা এন্ট্রি এক রিকোয়েস্টে চলে আসে)।
- প্রতিটা রো তে থাকে: শিরোনাম (title), PDF অ্যাটাচমেন্ট লিংক (files),
  প্রকাশের তারিখ (publish_date, বাংলা সংখ্যায়), এবং একটা "দেখুন" ডিটেইল লিংক।
- "দেখুন" লিংকে (/pages/notices/<slug>) গিয়ে দেখা গেছে সেটা লিস্টিং পেজের
  মতোই generic শেল রেন্ডার করে - টাইটেল/PDF ছাড়া অতিরিক্ত কনটেন্ট static
  HTML এ নেই (সম্ভবত client-side JS দিয়ে ভরা হয়, যা এখানে এক্সিকিউট হয় না)।
  তাই আলাদা করে প্রতিটা ডিটেইল পেজ ফেচ না করে (যেটা সার্ভারে অতিরিক্ত চাপ
  দিত এবং কোনো নতুন তথ্যও দিত না), লিস্টিং পেজ থেকে পাওয়া তথ্যই ক্যাশ করে
  ব্যবহার করা হচ্ছে।
- BPSC এর নোটিশ বোর্ডে মূলত পরীক্ষার ফলাফল/প্রশাসনিক নোটিশ থাকে - সরাসরি
  application deadline প্রায় কখনোই টাইটেলে থাকে না (থাকলে PDF এর ভেতরে
  থাকে, যা পার্স করা হয় না - future work)। তাই deadline extraction টাইটেল
  থেকে best-effort regex দিয়ে করা হয়, না পেলে None থাকে - এটা এক্সপেক্টেড।

চালানোর আগে:
    pip install beautifulsoup4 lxml requests
"""
import logging
import re
from datetime import datetime
from typing import Dict, List, Optional

from bs4 import BeautifulSoup

from .base_scraper import BaseScraper, ScrapedCircular

logger = logging.getLogger(__name__)

BN_DIGITS = "০১২৩৪৫৬৭৮৯"
_BN_TO_EN_DIGITS = str.maketrans(BN_DIGITS, "0123456789")


def _bn_to_en_digits(text: str) -> str:
    return text.translate(_BN_TO_EN_DIGITS)


class BpscScraper(BaseScraper):
    """বাংলাদেশ সরকারী কর্ম কমিশন (BPSC) - নোটিশ বোর্ড স্ক্র্যাপার"""

    source_name = "bpsc.gov.bd"
    base_url = "https://bpsc.gov.bd"
    listing_url = "https://bpsc.gov.bd/pages/notices"
    organization_name = "বাংলাদেশ সরকারী কর্ম কমিশন (BPSC)"
    PAGE_SIZE = 100  # যাচাই করা হয়েছে - সাইট এই মান সমর্থন করে

    DEADLINE_PATTERN = re.compile(
        r"(আবেদনের\s*শেষ\s*তারিখ|আবেদন\s*করার\s*শেষ\s*সময়|শেষ\s*তারিখ)"
        r"[^০-৯0-9]{0,15}([০-৯0-9]{1,2}[/.-][০-৯0-9]{1,2}[/.-][০-৯0-9]{4})"
    )

    def __init__(self):
        super().__init__()
        self._detail_cache: Dict[str, ScrapedCircular] = {}

    def scrape_listing(self) -> List[str]:
        urls: List[str] = []
        page = 1

        while True:
            html = self.fetch(
                f"{self.listing_url}?page={page}&page_size={self.PAGE_SIZE}"
            )
            if not html:
                break

            soup = BeautifulSoup(html, "lxml")
            rows = [
                row
                for row in soup.select("table.notice-table tbody tr.table-tr")
                if "toggle-hidden" not in (row.get("class") or [])
            ]
            if not rows:
                break

            for row in rows:
                item = self._parse_row(row)
                if item:
                    urls.append(item.source_url)
                    self._detail_cache[item.source_url] = item

            logger.info("[%s] পেজ %d থেকে %d টা নোটিশ পাওয়া গেছে", self.source_name, page, len(rows))

            if len(rows) < self.PAGE_SIZE:
                break
            page += 1

        return urls

    def _parse_row(self, row) -> Optional[ScrapedCircular]:
        title_el = row.select_one('td[data-column="title"]')
        detail_link = row.select_one("td.centered a")
        if not title_el or not detail_link or not detail_link.get("href"):
            return None

        title = title_el.get_text(strip=True)

        href = detail_link["href"]
        detail_url = href if href.startswith("http") else f"{self.base_url}{href}"

        pdf_link = row.select_one('td[data-column="files"] a')
        pdf_url = pdf_link.get("href") if pdf_link else None

        date_el = row.select_one('td[data-column="publish_date"] span')
        publish_date_bn = date_el.get_text(strip=True) if date_el else None

        full_text = title
        if publish_date_bn:
            full_text = f"{title}\n\nপ্রকাশের তারিখ: {publish_date_bn}"

        return ScrapedCircular(
            title=title,
            organization_name=self.organization_name,
            application_deadline=self._extract_deadline(title),
            source_url=detail_url,
            circular_image_url=pdf_url,
            full_text=full_text,
            category="Government Job",
            raw_extra={"publish_date_bn": publish_date_bn},
        )

    def _extract_deadline(self, text: str) -> Optional[str]:
        match = self.DEADLINE_PATTERN.search(text)
        if not match:
            return None

        date_str = _bn_to_en_digits(match.group(2))
        for sep in ("/", "-", "."):
            if sep in date_str:
                parts = date_str.split(sep)
                if len(parts) == 3:
                    try:
                        day, month, year = (int(p) for p in parts)
                        return datetime(year, month, day).isoformat()
                    except ValueError:
                        return None
        return None

    def scrape_detail(self, url: str) -> Optional[ScrapedCircular]:
        # bpsc.gov.bd এর ডিটেইল পেজ লিস্টিং পেজের চেয়ে বেশি কিছু দেয় না
        # (উপরের মডিউল ডকস্ট্রিং দেখুন) - তাই আলাদা HTTP রিকোয়েস্ট না করে
        # scrape_listing() এ ক্যাশ করা ডেটা থেকেই রিটার্ন করা হচ্ছে।
        return self._detail_cache.get(url)


# সব স্ক্র্যাপার এখানে রেজিস্টার করুন - scheduler.py এটা লুপ করে চালাবে
# bdjobs.com ইচ্ছাকৃতভাবে বাদ - উপরের মডিউল ডকস্ট্রিং দেখুন
ALL_SCRAPERS = [
    BpscScraper,
]
