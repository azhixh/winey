"""
Simple in-memory TTL cache for external provider responses.

Documented Cache Expiration Policy:
- Default TTL: 3600 seconds (1 hour).
- Rationale: Food product formulations change infrequently, while an hourly cache avoids redundant
  HTTP overhead, conforms to Open Food Facts guidelines, and adheres to USDA API rate limits.
- Eviction: Expired keys are discarded on access or during periodic cleanup.
- Volatility: Non-persistent (cleared on server restart).
"""

import time
from typing import Any, Optional


class SimpleTTLCache:
    """
    Thread-safe in-memory key-value cache with time-to-live (TTL) expiration.
    """

    def __init__(self, default_ttl_seconds: int = 3600):
        self.default_ttl = default_ttl_seconds
        self._store: dict[str, tuple[Any, float]] = {}

    def get(self, key: str) -> Optional[Any]:
        """Retrieve value if key exists and has not expired."""
        if key not in self._store:
            return None
        value, expiry = self._store[key]
        if time.time() > expiry:
            del self._store[key]
            return None
        return value

    def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> None:
        """Store value with expiration timestamp."""
        ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl
        expiry = time.time() + ttl
        self._store[key] = (value, expiry)

    def clear(self) -> None:
        """Clear all cached entries."""
        self._store.clear()

    def size(self) -> int:
        """Return number of unexpired items in cache."""
        now = time.time()
        # Clean expired
        expired = [k for k, (_, exp) in self._store.items() if now > exp]
        for k in expired:
            del self._store[k]
        return len(self._store)
