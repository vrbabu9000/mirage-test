"""Rate limiting utilities for Anthropic API calls.

Two pieces:

1. `RateLimiter`: a token-bucket global throttle that every worker thread
   goes through before hitting the API. Configured at 40 requests per
   minute (80% of the published 50/min limit) so parallel workers stay
   comfortably under the ceiling.

2. `call_with_backoff`: an exponential-backoff retry wrapper that knows
   how to read the `retry-after` header on 429 responses and waits the
   server-specified duration. Much more robust than blind retries.
"""
from __future__ import annotations

import random
import threading
import time
from typing import Callable, TypeVar

import anthropic

T = TypeVar("T")


class RateLimiter:
    """Thread-safe token-bucket rate limiter."""

    def __init__(self, requests_per_minute: int = 40):
        self.capacity = float(requests_per_minute)
        self.tokens = float(requests_per_minute)
        self.refill_rate = requests_per_minute / 60.0  # tokens per second
        self.last_refill = time.monotonic()
        self.lock = threading.Lock()

    def acquire(self) -> None:
        """Block until a token is available, then consume one."""
        while True:
            with self.lock:
                now = time.monotonic()
                elapsed = now - self.last_refill
                self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
                self.last_refill = now
                if self.tokens >= 1.0:
                    self.tokens -= 1.0
                    return
                # Not enough tokens — compute wait and sleep outside the lock.
                wait = (1.0 - self.tokens) / self.refill_rate
            time.sleep(wait)


# Global limiter shared across threads. Conservative: 40/min leaves
# headroom for the observer + agent streams running in parallel and
# for bursts during Phase 4.
_GLOBAL_LIMITER = RateLimiter(requests_per_minute=40)


def call_with_backoff(
    func: Callable[[], T],
    max_retries: int = 6,
    base_delay: float = 2.0,
    max_delay: float = 60.0,
) -> T:
    """Invoke `func` through the global limiter with exponential backoff.

    On `RateLimitError`, honor the `retry-after` header when present;
    otherwise exponential backoff with jitter. On other transient
    errors (APIConnectionError, APITimeoutError, APIStatusError with
    5xx), also retry with backoff. On permanent errors, raise.
    """
    last_err: Exception | None = None
    for attempt in range(max_retries):
        _GLOBAL_LIMITER.acquire()
        try:
            return func()
        except anthropic.RateLimitError as exc:
            last_err = exc
            # Honor Retry-After header if present.
            retry_after = None
            try:
                hdrs = getattr(exc.response, "headers", None)
                if hdrs is not None:
                    retry_after = hdrs.get("retry-after") or hdrs.get("Retry-After")
            except Exception:
                pass
            if retry_after is not None:
                try:
                    wait = float(retry_after) + random.uniform(0, 1)
                except ValueError:
                    wait = min(max_delay, base_delay * (2 ** attempt)) + random.uniform(0, 1)
            else:
                wait = min(max_delay, base_delay * (2 ** attempt)) + random.uniform(0, 1)
            time.sleep(wait)
        except (anthropic.APIConnectionError, anthropic.APITimeoutError) as exc:
            last_err = exc
            wait = min(max_delay, base_delay * (2 ** attempt)) + random.uniform(0, 0.5)
            time.sleep(wait)
        except anthropic.APIStatusError as exc:
            last_err = exc
            # Retry on 5xx, give up on 4xx (except the 429 handled above).
            status = getattr(exc, "status_code", None) or 0
            if 500 <= status < 600:
                wait = min(max_delay, base_delay * (2 ** attempt)) + random.uniform(0, 0.5)
                time.sleep(wait)
            else:
                raise
    # Retries exhausted.
    raise last_err  # type: ignore[misc]
