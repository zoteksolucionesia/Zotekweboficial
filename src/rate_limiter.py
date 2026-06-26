import os
import time
from collections import defaultdict
from fastapi import Request, HTTPException

try:
    from upstash_ratelimit import Ratelimit, SlidingWindow
    from upstash_redis import Redis as UpstashRedis
    _UPSTASH_OK = True
except ImportError:
    _UPSTASH_OK = False

# In-memory fallback — funciona sin Redis, pero se reinicia con el proceso
class _InMemory:
    def __init__(self):
        self._store: dict = defaultdict(list)

    def check(self, key: str, max_req: int, window_sec: int) -> tuple:
        now = time.time()
        self._store[key] = [t for t in self._store[key] if t > now - window_sec]
        if len(self._store[key]) >= max_req:
            retry_after = int(min(self._store[key]) + window_sec - now) + 1
            return False, retry_after
        self._store[key].append(now)
        return True, 0

_fallback = _InMemory()
_limiters: dict = {}


def _get_limiter(name: str, max_req: int, window: str):
    if not _UPSTASH_OK:
        return None
    url = os.getenv("UPSTASH_REDIS_REST_URL")
    token = os.getenv("UPSTASH_REDIS_REST_TOKEN")
    if not url or not token:
        return None
    if name not in _limiters:
        redis = UpstashRedis(url=url, token=token)
        _limiters[name] = Ratelimit(
            redis=redis,
            limiter=SlidingWindow(max_requests=max_req, window=window),
            prefix=f"rl:{name}",
        )
    return _limiters[name]


def check(
    request: Request,
    name: str,
    max_req: int,
    window: str,      # formato Upstash: "60 s", "15 m", "1 h", "24 h"
    window_sec: int,  # mismo intervalo en segundos para el fallback
    identifier: str = None,
):
    """Verifica el rate limit. Lanza HTTPException 429 si se excede.

    Si UPSTASH_REDIS_REST_URL / _TOKEN no están configuradas, usa
    fallback en memoria (no persiste entre reinicios de Cloud Run).
    """
    forwarded = request.headers.get("x-forwarded-for", "")
    ip = forwarded.split(",")[0].strip() or (
        request.client.host if request.client else "unknown"
    )
    key = identifier or ip

    limiter = _get_limiter(name, max_req, window)
    if limiter:
        resp = limiter.limit(key)
        if not resp.allowed:
            retry_after = max(1, int(resp.reset / 1000 - time.time()) + 1)
            raise _http_429(retry_after, resp.limit, resp.remaining)
    else:
        allowed, retry_after = _fallback.check(key, max_req, window_sec)
        if not allowed:
            raise _http_429(retry_after)


def _http_429(retry_after: int, limit: int = None, remaining: int = 0):
    mins = max(1, retry_after // 60)
    headers = {"Retry-After": str(retry_after)}
    if limit is not None:
        headers["X-RateLimit-Limit"] = str(limit)
        headers["X-RateLimit-Remaining"] = str(remaining)
    return HTTPException(
        status_code=429,
        detail={
            "error": "rate_limit_exceeded",
            "message": f"Demasiadas peticiones. Intenta de nuevo en {mins} minuto{'s' if mins != 1 else ''}.",
            "retry_after": retry_after,
        },
        headers=headers,
    )
