"""Simple in-memory fixed-window rate limiter, keyed by client IP + route.

Good enough for a single-process MVP deployment. Swap for a Redis-backed
implementation (same interface) once running multiple workers/instances.
"""

import time
from collections import defaultdict

from fastapi import HTTPException, Request, status


class RateLimiter:
    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._hits: dict[str, list[float]] = defaultdict(list)

    async def __call__(self, request: Request) -> None:
        key = f"{request.url.path}:{request.client.host if request.client else 'unknown'}"
        now = time.monotonic()
        window_start = now - self.window_seconds

        hits = [t for t in self._hits[key] if t > window_start]
        if len(hits) >= self.max_requests:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests, please try again later",
            )

        hits.append(now)
        self._hits[key] = hits


auth_rate_limiter = RateLimiter(max_requests=10, window_seconds=60)
receipt_create_rate_limiter = RateLimiter(max_requests=60, window_seconds=60)
