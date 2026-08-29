from collections import defaultdict, deque
from threading import Lock
from time import monotonic

from fastapi import HTTPException, Request, status


class InMemoryRateLimiter:
    """Small-process protection for sensitive endpoints.

    Use a shared Redis-backed limiter when the application is deployed with
    multiple workers or instances.
    """

    def __init__(self, attempts: int, window_seconds: int):
        self.attempts = attempts
        self.window_seconds = window_seconds
        self._requests: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def check(self, key: str) -> None:
        now = monotonic()
        with self._lock:
            attempts = self._requests[key]
            while attempts and now - attempts[0] >= self.window_seconds:
                attempts.popleft()
            if len(attempts) >= self.attempts:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Too many attempts. Please try again later.",
                    headers={"Retry-After": str(self.window_seconds)},
                )
            attempts.append(now)


auth_limiter = InMemoryRateLimiter(attempts=10, window_seconds=60)


def limit_auth_attempts(request: Request) -> None:
    client_host = request.client.host if request.client else "unknown"
    auth_limiter.check(client_host)
