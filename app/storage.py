"""Storage backends: in-memory (tests/local) and PostgreSQL (real deployments)."""
import threading
from typing import Protocol


class Store(Protocol):
    def init(self) -> None: ...
    def create(self, code: str, url: str) -> bool: ...
    def get(self, code: str) -> dict | None: ...
    def hit(self, code: str) -> None: ...
    def ping(self) -> bool: ...
    def close(self) -> None: ...


class MemoryStore:
    def __init__(self) -> None:
        self._d: dict[str, dict] = {}
        self._lock = threading.Lock()

    def init(self) -> None:
        pass

    def create(self, code: str, url: str) -> bool:
        with self._lock:
            if code in self._d:
                return False
            self._d[code] = {"url": url, "hits": 0}
            return True

    def get(self, code: str) -> dict | None:
        with self._lock:
            row = self._d.get(code)
            return dict(row) if row else None

    def hit(self, code: str) -> None:
        with self._lock:
            if code in self._d:
                self._d[code]["hits"] += 1

    def ping(self) -> bool:
        return True

    def close(self) -> None:
        pass


class PgStore:
    def __init__(self, dsn: str) -> None:
        from psycopg_pool import ConnectionPool

        self._pool = ConnectionPool(dsn, min_size=1, max_size=10, open=False)

    def init(self) -> None:
        self._pool.open(wait=True, timeout=30)
        with self._pool.connection() as conn:
            conn.execute(
                """CREATE TABLE IF NOT EXISTS links (
                       code TEXT PRIMARY KEY,
                       url TEXT NOT NULL,
                       hits BIGINT NOT NULL DEFAULT 0,
                       created_at TIMESTAMPTZ NOT NULL DEFAULT now())"""
            )

    def create(self, code: str, url: str) -> bool:
        with self._pool.connection() as conn:
            cur = conn.execute(
                "INSERT INTO links (code, url) VALUES (%s, %s) ON CONFLICT DO NOTHING",
                (code, url),
            )
            return cur.rowcount == 1

    def get(self, code: str) -> dict | None:
        with self._pool.connection() as conn:
            row = conn.execute(
                "SELECT url, hits FROM links WHERE code = %s", (code,)
            ).fetchone()
        return {"url": row[0], "hits": row[1]} if row else None

    def hit(self, code: str) -> None:
        with self._pool.connection() as conn:
            conn.execute("UPDATE links SET hits = hits + 1 WHERE code = %s", (code,))

    def ping(self) -> bool:
        try:
            with self._pool.connection() as conn:
                conn.execute("SELECT 1")
            return True
        except Exception:
            return False

    def close(self) -> None:
        self._pool.close()
