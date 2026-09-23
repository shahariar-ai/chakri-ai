"""
এই স্ক্রিপ্ট নিয়মিত (প্রতি ৬ ঘণ্টায়) সব স্ক্র্যাপার চালায়,
নতুন সার্কুলার ডেটাবেসে সেভ করে, এবং নতুন পাওয়া সার্কুলারের জন্য
পুশ নোটিফিকেশন পাঠায়।

চালানোর নিয়ম (আলাদা প্রসেস হিসেবে, ওয়েব সার্ভারের পাশাপাশি):
    python scheduler.py

প্রোডাকশনে এটা systemd service / cron job / Docker container হিসেবে
আলাদাভাবে চালানো উচিত, মূল API সার্ভারের সাথে না মিশিয়ে।
"""
import logging
from datetime import datetime

from apscheduler.schedulers.blocking import BlockingScheduler

from database import SessionLocal
import models
from scrapers.site_scrapers import ALL_SCRAPERS
from notifications.fcm_service import send_push_to_all

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("scheduler")

SCRAPE_INTERVAL_HOURS = 6


def get_or_create_organization(db, name: str) -> "models.Organization":
    """নাম দিয়ে Organization খুঁজে, না পেলে নতুন বানায়। scraped item এর
    organization_name স্ট্রিং থেকে JobCircular.organization_id (FK) পূরণ
    করার জন্য দরকার - আগে এটা বাদ পড়ে যাচ্ছিল।"""
    org = db.query(models.Organization).filter(models.Organization.name == name).first()
    if org:
        return org

    org = models.Organization(
        name=name,
        name_bn=name,
        org_type=models.OrgType.government,
    )
    db.add(org)
    db.flush()  # id পাওয়ার জন্য কমিট ছাড়াই flush
    return org


def parse_deadline(deadline_str):
    """ScrapedCircular.application_deadline (ISO string বা None) কে
    datetime এ রূপান্তর করে - JobCircular.application_deadline কলামে
    সরাসরি ISO string বসানো যায় না।"""
    if not deadline_str:
        return None
    try:
        return datetime.fromisoformat(deadline_str)
    except ValueError:
        logger.warning("অবৈধ deadline ফরম্যাট, স্কিপ করা হলো: %s", deadline_str)
        return None


def run_all_scrapers():
    db = SessionLocal()
    try:
        new_circulars = []

        for scraper_cls in ALL_SCRAPERS:
            scraper = scraper_cls()
            logger.info("চালু হচ্ছে: %s", scraper.source_name)
            try:
                items = scraper.run()
            except Exception as e:
                logger.error("স্ক্র্যাপার ব্যর্থ হয়েছে (%s): %s", scraper.source_name, e)
                continue

            for item in items:
                # ডুপ্লিকেট চেক - একই source_url আগে থেকে থাকলে স্কিপ
                existing = (
                    db.query(models.JobCircular)
                    .filter(models.JobCircular.source_url == item.source_url)
                    .first()
                )
                if existing:
                    continue

                organization = get_or_create_organization(db, item.organization_name)

                circular = models.JobCircular(
                    title=item.title,
                    organization_id=organization.id,
                    post_names=item.post_names,
                    vacancy_count=item.vacancy_count,
                    qualification=item.qualification,
                    application_deadline=parse_deadline(item.application_deadline),
                    source_url=item.source_url,
                    circular_image_url=item.circular_image_url,
                    full_text=item.full_text,
                    category=item.category,
                    scraped_from=scraper.source_name,
                )
                db.add(circular)
                new_circulars.append(circular)

        db.commit()
        logger.info("মোট %d টা নতুন সার্কুলার যোগ হয়েছে", len(new_circulars))

        if new_circulars:
            notify_new_circulars(db, new_circulars)

    finally:
        db.close()


def notify_new_circulars(db, circulars):
    """নতুন সার্কুলারগুলোর জন্য সব রেজিস্টার্ড ডিভাইসে পুশ নোটিফিকেশন পাঠায়"""
    tokens = [d.token for d in db.query(models.DeviceToken).all()]
    if not tokens:
        logger.info("কোনো রেজিস্টার্ড ডিভাইস নেই, নোটিফিকেশন স্কিপ করা হলো")
        return

    for circular in circulars:
        result = send_push_to_all(
            title="নতুন চাকরির সার্কুলার!",
            body=circular.title,
            tokens=tokens,
            data={"circular_id": str(circular.id), "type": "new_circular"},
        )
        logger.info("নোটিফিকেশন পাঠানো হয়েছে (%s): %s", circular.title[:50], result)
        circular.notified = True

    db.commit()


if __name__ == "__main__":
    scheduler = BlockingScheduler()
    scheduler.add_job(run_all_scrapers, "interval", hours=SCRAPE_INTERVAL_HOURS)

    logger.info("শিডিউলার শুরু হলো - প্রতি %d ঘণ্টায় স্ক্র্যাপিং চলবে", SCRAPE_INTERVAL_HOURS)
    # প্রথমবার সাথে সাথে একবার চালানো
    run_all_scrapers()
    scheduler.start()
