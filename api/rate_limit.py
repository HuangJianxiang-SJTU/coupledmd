"""
Rate limiting middleware for CoupledMD.

Two tiers:
  Tier 0 (anonymous, default): full read access, 60 req/min per IP.
  Tier 1 (optional free API key): 600 req/min per key.

The key only raises the rate limit — it unlocks no data that anonymous
users cannot already get.  This satisfies the NAR free-access rule.

Implementation: Starlette middleware (not slowapi decorators) for
reliable operation with gunicorn + uvicorn workers.
"""

import os
import secrets
import time
from collections import defaultdict
from pathlib import Path
from threading import Lock

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse


# ---------------------------------------------------------------------------
# Token-bucket rate limiter (in-memory, per-worker)
# ---------------------------------------------------------------------------

class TokenBucket:
    """Simple token-bucket rate limiter for a single key."""

    def __init__(self, rate: float, capacity: int):
        self.rate = rate          # tokens per second
        self.capacity = capacity  # max tokens
        self.tokens = capacity
        self.last_refill = time.monotonic()

    def consume(self) -> bool:
        now = time.monotonic()
        elapsed = now - self.last_refill
        self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
        self.last_refill = now
        if self.tokens >= 1:
            self.tokens -= 1
            return True
        return False


class RateLimiter:
    """Per-IP and per-key rate limiter using token buckets."""

    def __init__(self, tier0_limit: str = "60/minute", tier1_limit: str = "600/minute"):
        self.tier0_rate, self.tier0_capacity = self._parse_limit(tier0_limit)
        self.tier1_rate, self.tier1_capacity = self._parse_limit(tier1_limit)
        self._buckets: dict[str, TokenBucket] = {}
        self._lock = Lock()
        # Clean up old buckets every 5 minutes
        self._last_cleanup = time.monotonic()

    @staticmethod
    def _parse_limit(limit_str: str) -> tuple[float, int]:
        """Parse '60/minute' into (rate_per_second, capacity)."""
        parts = limit_str.split("/")
        count = int(parts[0])
        period = parts[1] if len(parts) > 1 else "minute"
        if period == "minute":
            rate = count / 60.0
        elif period == "second":
            rate = float(count)
        elif period == "hour":
            rate = count / 3600.0
        else:
            rate = count / 60.0
        return rate, count

    def _get_bucket(self, key: str, tier: int) -> TokenBucket:
        if key not in self._buckets:
            if tier == 1:
                self._buckets[key] = TokenBucket(self.tier1_rate, self.tier1_capacity)
            else:
                self._buckets[key] = TokenBucket(self.tier0_rate, self.tier0_capacity)
        return self._buckets[key]

    def check(self, key: str, tier: int = 0) -> bool:
        """Check if the request is allowed. Returns True if allowed.

        Note: limits are per-worker and in-memory. The Dockerfile runs a single
        uvicorn worker, so the configured limits hold as-is; scaling workers
        multiplies the effective limit.
        """
        # Periodic cleanup
        now = time.monotonic()
        if now - self._last_cleanup > 300:
            with self._lock:
                # Remove buckets that haven't been used in 10 minutes
                stale = [k for k, b in self._buckets.items()
                         if now - b.last_refill > 600]
                for k in stale:
                    del self._buckets[k]
                self._last_cleanup = now

        # Get/create the bucket and consume a token under the same lock so the
        # token-bucket mutation is serialized across concurrent requests.
        with self._lock:
            bucket = self._get_bucket(key, tier)
            return bucket.consume()


# ---------------------------------------------------------------------------
# API-key store (SQLite-backed, lightweight)
# ---------------------------------------------------------------------------

_KEYS_DB = Path(os.environ.get(
    "KEYS_DB_PATH",
    os.path.join(os.environ.get("DATA_ROOT", str(Path(__file__).resolve().parent.parent)),
                 "data", "keys.db"),
))

TIER1_LIMIT = "600/minute"


def _init_keys_db():
    """Create the keys table if it doesn't exist."""
    import sqlite3
    _KEYS_DB.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(_KEYS_DB))
    conn.execute("""
        CREATE TABLE IF NOT EXISTS api_keys (
            key       TEXT PRIMARY KEY,
            email     TEXT,
            institution TEXT,
            name      TEXT,
            tier      INTEGER NOT NULL DEFAULT 1,
            created_at REAL NOT NULL,
            notes     TEXT
        )
    """)
    conn.commit()
    conn.close()


# Eagerly ensure the table exists at import time so the middleware's
# _lookup_key() never hits a "no such table" error on a fresh deploy
# (e.g. a scanner hitting ?api_key=... before any key has been issued).
_init_keys_db()


def _lookup_key(key: str) -> dict | None:
    """Return the key record or None."""
    import sqlite3
    conn = sqlite3.connect(str(_KEYS_DB))
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM api_keys WHERE key = ?", (key,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def issue_key(email: str = "", institution: str = "", name: str = "", notes: str = "") -> str:
    """Create a new Tier-1 API key and return it."""
    import sqlite3
    _init_keys_db()
    key = f"cmd_{secrets.token_urlsafe(24)}"
    conn = sqlite3.connect(str(_KEYS_DB))
    conn.execute(
        "INSERT INTO api_keys (key, email, institution, name, tier, created_at, notes) VALUES (?, ?, ?, ?, 1, ?, ?)",
        (key, email, institution, name, time.time(), notes),
    )
    conn.commit()
    conn.close()
    return key


def delete_key(key: str) -> bool:
    """Delete an API key. Returns True if it existed."""
    import sqlite3
    conn = sqlite3.connect(str(_KEYS_DB))
    cur = conn.cursor()
    cur.execute("DELETE FROM api_keys WHERE key = ?", (key,))
    deleted = cur.rowcount > 0
    conn.commit()
    conn.close()
    return deleted


# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------

# Global rate limiter instance
_limiter = RateLimiter()


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Per-IP rate limiting middleware.

    - Tier 0 (anonymous): 60 req/min per IP
    - Tier 1 (API key): 600 req/min per key
    - Returns HTTP 429 with Retry-After on limit exceeded
    - Never redirects to login
    """

    async def dispatch(self, request: Request, call_next):
        # Only rate-limit API endpoints
        path = request.url.path
        if not path.startswith("/api/"):
            return await call_next(request)

        # Determine key and tier
        api_key = request.query_params.get("api_key") or request.headers.get("X-API-Key")
        if api_key and _lookup_key(api_key):
            key = f"key:{api_key}"
            tier = 1
        else:
            # Use client IP
            client_ip = request.client.host if request.client else "unknown"
            key = f"ip:{client_ip}"
            tier = 0

        if not _limiter.check(key, tier):
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded. Try again later or request an API key at /api/v1/keys/request"},
                headers={"Retry-After": "60"},
            )

        response = await call_next(request)
        # Add rate limit headers
        response.headers["X-RateLimit-Tier"] = str(tier)
        return response
