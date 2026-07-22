from __future__ import annotations

from collections import defaultdict, deque
from threading import Lock
from time import monotonic


class InMemoryRateLimiter:
    """Process-local guardrail suitable for one application instance."""

    def __init__(self, limit: int, window_seconds: int) -> None:
        self.limit = limit
        self.window_seconds = window_seconds
        self._requests: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def allowed(self, identifier: str) -> bool:
        now = monotonic()
        with self._lock:
            bucket = self._requests[identifier]
            while bucket and bucket[0] <= now - self.window_seconds:
                bucket.popleft()
            if len(bucket) >= self.limit:
                return False
            bucket.append(now)
            return True
