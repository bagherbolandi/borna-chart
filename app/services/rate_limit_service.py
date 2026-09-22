from __future__ import annotations

from collections import deque
from threading import Lock
from time import monotonic


class RateLimitService:
    _events: dict[str, deque[float]] = {}
    _lock = Lock()

    @classmethod
    def allow(cls, *, key: str, limit: int, window_seconds: int) -> tuple[bool, int]:
        now = monotonic()
        with cls._lock:
            bucket = cls._events.setdefault(key, deque())
            while bucket and now - bucket[0] >= window_seconds:
                bucket.popleft()
            if len(bucket) >= limit:
                retry_after = max(1, int(window_seconds - (now - bucket[0])))
                return False, retry_after
            bucket.append(now)
            return True, 0

    @classmethod
    def reset(cls) -> None:
        with cls._lock:
            cls._events.clear()
