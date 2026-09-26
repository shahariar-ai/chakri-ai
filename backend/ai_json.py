"""
Claude থেকে JSON schema অনুযায়ী structured output নেওয়ার শেয়ার্ড হেল্পার।
Mock Interview ও Job Matching দুটোই এটা ব্যবহার করে।
"""
import json
import os

import anthropic
from fastapi import HTTPException

AI_MODEL = "claude-sonnet-4-6"  # main.py-র resume/cover letter-এর সাথে একই মডেল


def _client() -> anthropic.Anthropic:
    # main.py-তে load_dotenv() রাউটার import-এর পরে চলে, তাই ক্লায়েন্ট lazily বানানো হয়
    return anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


def call_json(prompt: str, schema: dict, max_tokens: int = 4000) -> dict:
    """prompt পাঠিয়ে schema-মাফিক dict ফেরত দেয়; যেকোনো সমস্যায় HTTPException(502/500)।"""
    if not os.getenv("ANTHROPIC_API_KEY"):
        raise HTTPException(status_code=500, detail="ANTHROPIC_API_KEY সেট করা নেই")
    try:
        # SDK 0.39-এ output_config প্যারামিটার নেই, তাই extra_body দিয়ে structured output চাওয়া হলো
        message = _client().messages.create(
            model=AI_MODEL,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
            extra_body={"output_config": {"format": {"type": "json_schema", "schema": schema}}},
        )
    except anthropic.APIStatusError as e:
        raise HTTPException(status_code=502, detail=f"AI error ({e.status_code}): {e.message}")
    except anthropic.APIConnectionError:
        raise HTTPException(status_code=502, detail="AI সার্ভারে সংযোগ করা যায়নি")

    if message.stop_reason != "end_turn":
        raise HTTPException(status_code=502, detail=f"AI উত্তর অসম্পূর্ণ (stop_reason={message.stop_reason})")
    text = next((b.text for b in message.content if b.type == "text"), "")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        raise HTTPException(status_code=502, detail="AI থেকে অবৈধ JSON এসেছে")
