"""Redis cache that fails open: if Redis is down, the app still serves from the DB."""
import logging

log = logging.getLogger("urlshort.cache")


class Cache:
    def __init__(self, url: str | None, ttl: int = 300) -> None:
        self.ttl = ttl
        self._r = None
        if url:
            import redis

            self._r = redis.Redis.from_url(url, socket_timeout=0.5, decode_responses=True)

    def get(self, key: str) -> str | None:
        if not self._r:
            return None
        try:
            return self._r.get(key)
        except Exception as exc:
            log.warning("cache get failed: %s", exc)
            return None

    def set(self, key: str, value: str) -> None:
        if not self._r:
            return
        try:
            self._r.setex(key, self.ttl, value)
        except Exception as exc:
            log.warning("cache set failed: %s", exc)

    def ping(self) -> bool:
        if not self._r:
            return True
        try:
            return bool(self._r.ping())
        except Exception:
            return False
