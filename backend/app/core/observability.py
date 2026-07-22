from __future__ import annotations

from collections import Counter
from threading import Lock
from typing import Tuple


class ApplicationMetrics:
    """Small dependency-free counter set exposed in Prometheus text format."""

    def __init__(self) -> None:
        self._requests: Counter[Tuple[str, str, int]] = Counter()
        self._lock = Lock()

    def record_request(self, method: str, path: str, status_code: int) -> None:
        with self._lock:
            self._requests[(method, path, status_code)] += 1

    def render_prometheus(self) -> str:
        with self._lock:
            lines = [
                "# HELP converra_http_requests_total HTTP requests handled.",
                "# TYPE converra_http_requests_total counter",
            ]
            for (method, path, status_code), count in sorted(self._requests.items()):
                lines.append(
                    'converra_http_requests_total{method="%s",path="%s",status="%s"} %s'
                    % (method, path.replace('"', ""), status_code, count)
                )
        return "\n".join(lines) + "\n"
