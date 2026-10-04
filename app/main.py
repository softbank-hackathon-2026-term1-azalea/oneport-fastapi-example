import logging
import time
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager

from asgi_correlation_id import CorrelationIdMiddleware
from fastapi import FastAPI, Request, Response

from app.api.routes import health, notes, ui
from app.core.config import get_settings
from app.core.db import Database
from app.core.logging import configure_logging
from app.core.release import load_release
from app.exceptions import register_exception_handlers

log = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    release = load_release(app_name=settings.app_name, color=settings.app_color)
    configure_logging(
        fmt=settings.log_format,
        level=settings.log_level,
        static_fields={"app": release.app, "version": release.version},
    )
    database = Database(settings.sqlalchemy_url)
    app.state.settings = settings
    app.state.release = release
    app.state.db = database
    log.info("application started", extra=release.as_dict())
    try:
        yield
    finally:
        await database.dispose()
        log.info("application stopped")


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Oneport Notes",
        lifespan=lifespan,
        docs_url="/docs" if settings.docs_enabled else None,
        redoc_url=None,
        openapi_url="/openapi.json" if settings.docs_enabled else None,
    )

    @app.middleware("http")
    async def access_log(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        started = time.perf_counter()
        response = await call_next(request)
        release_id = request.app.state.settings.launchpad_release_id
        if release_id:
            response.headers["X-Launchpad-Release"] = release_id
        if request.url.path not in ("/health", "/ready"):
            log.info(
                "request",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "status": response.status_code,
                    "duration_ms": round((time.perf_counter() - started) * 1000, 1),
                },
            )
        return response

    app.add_middleware(CorrelationIdMiddleware, header_name="X-Request-ID")

    app.include_router(health.router)
    app.include_router(notes.router)
    app.include_router(ui.router)
    register_exception_handlers(app)
    return app


app = create_app()
