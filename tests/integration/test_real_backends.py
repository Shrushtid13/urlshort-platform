"""Runs against real Postgres + Redis. Skipped unless DATABASE_URL is set (CI sets it)."""
import os
import uuid

import pytest

from app.cache import Cache
from app.storage import PgStore

pytestmark = pytest.mark.skipif(not os.getenv("DATABASE_URL"), reason="needs real Postgres")


@pytest.fixture(scope="module")
def pg():
    store = PgStore(os.environ["DATABASE_URL"])
    store.init()
    yield store
    store.close()


def test_pg_roundtrip(pg):
    code = uuid.uuid4().hex[:7]
    assert pg.create(code, "https://example.com") is True
    assert pg.create(code, "https://other.com") is False  # unique constraint honoured
    pg.hit(code)
    pg.hit(code)
    assert pg.get(code) == {"url": "https://example.com", "hits": 2}
    assert pg.ping() is True


@pytest.mark.skipif(not os.getenv("REDIS_URL"), reason="needs real Redis")
def test_redis_cache_roundtrip():
    cache = Cache(os.environ["REDIS_URL"], ttl=5)
    key = uuid.uuid4().hex
    assert cache.get(key) is None
    cache.set(key, "https://example.com")
    assert cache.get(key) == "https://example.com"
    assert cache.ping() is True


def test_cache_fails_open_when_redis_down():
    cache = Cache("redis://127.0.0.1:1/0")  # nothing listens here
    assert cache.get("x") is None  # no exception
    cache.set("x", "y")  # no exception
    assert cache.ping() is False
