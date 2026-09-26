"""
পুরনো/ছোট Subject নাম -> canonical (merge করা) নাম।
scripts/merge_subjects.py (একবারের merge) ও admin import (নতুন ডেটা) দুটোই এটা ব্যবহার করে,
যাতে "বাংলা" নামে import করলে merge-করা "বাংলা ব্যাকরণ ও সাহিত্য"-তেই যায়, নতুন ডুপ্লিকেট subject না বানায়।
"""

SUBJECT_ALIASES = {
    "বাংলা": "বাংলা ব্যাকরণ ও সাহিত্য",
    "ইংরেজি": "ইংরেজি গ্রামার ও Vocabulary",
    "সাধারণ জ্ঞান": "সাধারণ জ্ঞান (বাংলাদেশ বিষয়াবলি)",
    "বিজ্ঞান": "বিজ্ঞান ও প্রযুক্তি",
    "গণিত": "সাধারণ গণিত",
}


def canonical_subject_name(name: str) -> str:
    name = " ".join(name.split())  # অতিরিক্ত স্পেস বাদ
    return SUBJECT_ALIASES.get(name, name)
