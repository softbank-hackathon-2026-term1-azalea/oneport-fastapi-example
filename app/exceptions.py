import logging

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from redis.exceptions import RedisError

from app.notes.exceptions import NoteNotFoundError
from app.visits.exceptions import CacheNotConfiguredError

log = logging.getLogger(__name__)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(NoteNotFoundError)
    async def note_not_found(_: Request, exc: NoteNotFoundError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": str(exc), "note_id": exc.note_id},
        )

    @app.exception_handler(CacheNotConfiguredError)
    async def cache_not_configured(_: Request, exc: CacheNotConfiguredError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, content={"detail": str(exc)}
        )

    @app.exception_handler(RedisError)
    async def cache_unavailable(_: Request, exc: RedisError) -> JSONResponse:
        log.warning("cache request failed", extra={"error": type(exc).__name__})
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, content={"detail": "cache unavailable"}
        )
