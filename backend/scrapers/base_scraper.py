"""
সব সোর্স-নির্দিষ্ট স্ক্র্যাপারের বেস ক্লাস।

⚠️ ব্যবহারের আগে অবশ্যই করণীয়:
1. প্রতিটা সাইটের robots.txt চেক করুন (যেমন https://bdjobs.com/robots.txt)
2. সাইটের Terms of Service পড়ে নিন — commercial redistribution অনুমোদিত কিনা যাচাই করুন
3. Rate limiting মেনে চলুন (নিচে REQUEST_DELAY_SECONDS দেখুন) — সার্ভারে চাপ না দেওয়া
4. যেসব সরকারি সাইটে অফিসিয়াল API/RSS ফিড আছে (যেমন কিছু bpsc/ntrca নোটিশ বোর্ড),
   সেগুলো scraping-এর বদলে সরাসরি ব্যবহার করাই ভালো ও বেশি নির্ভরযোগ্য।

এই ফাইলে বাস্তব সাইট অ্যাক্সেস করা হয়নি (sandbox এ নেটওয়ার্ক সীমাবদ্ধ) —
আপনার নিজের মেশিনে প্রতিটা সাবক্লাসের selector গুলো আসল HTML দেখে যাচাই/ঠিক করতে হবে।
"""
import time
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional

import requests

logger = logging.getLogger(__name__)

REQUEST_DELAY_SECONDS = 2  # প্রতিটা রিকোয়েস্টের মাঝে বিরতি - সৌজন্যতা ও ব্লক এড়ানোর জন্য
USER_AGENT = "ChakriAI-Bot/1.0 (+contact: your-email@example.com)"


@dataclass
class ScrapedCircular:
    title: str
    organization_name: str
    post_names: Optional[str] = None
    vacancy_count: Optional[str] = None
    qualification: Optional[str] = None
    application_deadline: Optional[str] = None  # ISO string, পরে parse হবে
    source_url: Optional[str] = None
    circular_image_url: Optional[str] = None
    full_text: Optional[str] = None
    category: Optional[str] = None
    raw_extra: dict = field(default_factory=dict)


class BaseScraper(ABC):
    source_name: str = "unknown"
    base_url: str = ""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT})

    def fetch(self, url: str) -> Optional[str]:
        try:
            resp = self.session.get(url, timeout=15)
            resp.raise_for_status()
            time.sleep(REQUEST_DELAY_SECONDS)
            return resp.text
        except requests.RequestException as e:
            logger.error("Fetch failed for %s: %s", url, e)
            return None

    @abstractmethod
    def scrape_listing(self) -> List[str]:
        """সার্কুলার লিস্টিং পেজ থেকে প্রতিটা সার্কুলারের URL সংগ্রহ করে"""
        raise NotImplementedError

    @abstractmethod
    def scrape_detail(self, url: str) -> Optional[ScrapedCircular]:
        """একটা নির্দিষ্ট সার্কুলার পেজ থেকে বিস্তারিত তথ্য বের করে"""
        raise NotImplementedError

    def run(self) -> List[ScrapedCircular]:
        """পুরো স্ক্র্যাপিং প্রক্রিয়া চালায়: লিস্টিং -> প্রতিটা ডিটেইল পেজ"""
        results = []
        urls = self.scrape_listing()
        logger.info("[%s] %d টা সার্কুলার URL পাওয়া গেছে", self.source_name, len(urls))

        for url in urls:
            item = self.scrape_detail(url)
            if item:
                results.append(item)

        return results
