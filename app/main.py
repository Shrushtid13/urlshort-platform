import logging
import os
import secrets
import string
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import RedirectResponse
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
from pydantic import AnyHttpUrl, BaseModel

from app.cache import Cache
from app.storage import MemoryStore, PgStore, Store

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"),
                    format='{"ts":"%(asctime)s","level":"%(levelname)s","logger":"%(name)s","msg":"%(message)s"}')
log = logging.getLogger("urlshort")

REQUESTS = Counter("http_requests_total", "HTTP requests", ["method", "path", "status"])
LATENCY = Histogram("http_request_duration_seconds", "Request latency", ["method", "path"])
LINKS_CREATED = Counter("links_created_total", "Short links created")
CACHE_RESULT = Counter("redirect_cache_total", "Redirect cache lookups", ["result"])

ALPHABET = string.ascii_letters + string.digits
BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")


class LinkIn(BaseModel):
    url: AnyHttpUrl


def build_store() -> Store:
    dsn = os.getenv("DATABASE_URL")
    return PgStore(dsn) if dsn else MemoryStore()


def create_app(store: Store | None = None, cache: Cache | None = None) -> FastAPI:
    store = store or build_store()
    cache = cache or Cache(os.getenv("REDIS_URL"))

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        store.init()
        log.info("startup complete (store=%s)", type(store).__name__)
        yield
        store.close()

    app = FastAPI(title="urlshort-platform", version=os.getenv("APP_VERSION", "dev"), lifespan=lifespan)

    @app.middleware("http")
    async def metrics_mw(request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        route = request.scope.get("route")
        path = route.path if route else "unmatched"  # template, not raw path -> low cardinality
        LATENCY.labels(request.method, path).observe(time.perf_counter() - start)
        REQUESTS.labels(request.method, path, response.status_code).inc()
        return response

    @app.get("/healthz")
    def healthz():
        return {"status": "ok"}

    @app.get("/readyz")
    def readyz():
        if not store.ping():
            raise HTTPException(503, "database unavailable")
        return {"status": "ready", "cache": "up" if cache.ping() else "degraded"}

    @app.get("/metrics")
    def metrics():
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

    @app.post("/api/v1/links", status_code=201)
    def create_link(body: LinkIn):
        url = str(body.url)
        for _ in range(5):
            code = "".join(secrets.choice(ALPHABET) for _ in range(7))
            if store.create(code, url):
                LINKS_CREATED.inc()
                return {"code": code, "short_url": f"{BASE_URL}/{code}", "url": url}
        raise HTTPException(500, "could not allocate a code")

    @app.get("/api/v1/links/{code}/stats")
    def stats(code: str):
        row = store.get(code)
        if not row:
            raise HTTPException(404, "not found")
        return {"code": code, **row}

    @app.get("/{code}")
    def redirect(code: str):
        url = cache.get(code)
        if url:
            CACHE_RESULT.labels("hit").inc()
        else:
            CACHE_RESULT.labels("miss").inc()
            row = store.get(code)
            if not row:
                raise HTTPException(404, "not found")
            url = row["url"]
            cache.set(code, url)
        store.hit(code)
        return RedirectResponse(url, status_code=307)

    return app


app = create_app()
