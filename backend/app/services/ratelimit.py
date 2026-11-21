import logging
import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request

log = logging.getLogger("app.ratelimit")


class RateLimiter:
    """Per-IP sliding window limiter (in memory; fine for a single backend process)."""

    def __init__(self, max_calls: int, window_seconds: int):
        self.max_calls = max_calls
        self.window = window_seconds
        self.hits: dict[str, deque] = defaultdict(deque)

    def __call__(self, request: Request) -> None:
        key = request.client.host if request.client else "unknown"
        now = time.monotonic()
        q = self.hits[key]
        while q and now - q[0] > self.window:
            q.popleft()
        if len(q) >= self.max_calls:
            log.warning("rate limit hit ip=%s path=%s", key, request.url.path)
            raise HTTPException(429, "Too many attempts. Try again later.")
        q.append(now)
