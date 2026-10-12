"""AI endpoint-এ IP-ভিত্তিক rate limit (in-memory sliding window; একটা সার্ভার প্রসেসের জন্য যথেষ্ট)।

env: RATE_LIMIT_ENABLED (ডিফল্ট true), RATE_LIMIT_PER_MINUTE (ডিফল্ট 10), RATE_LIMIT_PER_HOUR (ডিফল্ট 60)
Claude API খরচ ও অপব্যবহার ঠেকানোর জন্য। একাধিক ইনস্ট্যান্সে গেলে Redis-ভিত্তিক করতে হবে।
"""
import os
import time
from collections import defaultdict, deque

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

# Claude API কল করে এমন (বা ব্যয়বহুল) endpoint
LIMITED_PATHS = (
    "/api/resume/generate",
    "/api/resume/pdf",
    "/api/cover-letter/generate",
    "/api/interview/turn",
    "/api/job-match/analyze",
    "/api/job-match/recommend",
)


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.hits = defaultdict(deque)  # (ip) -> timestamps

    async def dispatch(self, request, call_next):
        if request.method != "POST" or request.url.path not in LIMITED_PATHS \
                or os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "false":
            return await call_next(request)

        per_min = int(os.getenv("RATE_LIMIT_PER_MINUTE", "10"))
        per_hour = int(os.getenv("RATE_LIMIT_PER_HOUR", "60"))
        ip = request.client.host if request.client else "unknown"
        now = time.monotonic()
        q = self.hits[ip]
        while q and now - q[0] > 3600:
            q.popleft()
        last_min = sum(1 for t in q if now - t <= 60)
        if last_min >= per_min or len(q) >= per_hour:
            retry = 60 if last_min >= per_min else 3600
            return JSONResponse(
                status_code=429,
                content={"detail": "অনেক বেশি অনুরোধ পাঠানো হয়েছে। কিছুক্ষণ পর আবার চেষ্টা করুন।"},
                headers={"Retry-After": str(retry)},
            )
        q.append(now)
        return await call_next(request)
