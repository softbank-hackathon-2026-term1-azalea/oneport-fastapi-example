import logging
from typing import Any

from fastapi import APIRouter, Response, status

from app.api.deps import DatabaseDep, OptionalCacheDep, ReleaseDep, SettingsDep

log = logging.getLogger(__name__)
router = APIRouter(tags=["health"])


@router.get("/health")
async def health(settings: SettingsDep, response: Response) -> dict[str, str]:
    if settings.app_force_unhealthy:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "unhealthy", "reason": "APP_FORCE_UNHEALTHY"}
    return {"status": "ok"}


@router.get("/ready")
async def ready(
    database: DatabaseDep, cache: OptionalCacheDep, response: Response
) -> dict[str, str]:
    body = {"status": "ok", "database": "up", "cache": "disabled"}
    try:
        await database.ping()
    except Exception:
        log.exception("database readiness check failed")
        body["database"] = "down"
    if cache is not None:
        try:
            await cache.ping()
            body["cache"] = "up"
        except Exception:
            log.exception("cache readiness check failed")
            body["cache"] = "down"
    if "down" in body.values():
        body["status"] = "unavailable"
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return body


@router.get("/version")
async def version(release: ReleaseDep) -> dict[str, Any]:
    return release.as_dict()


@router.get("/failure", status_code=status.HTTP_503_SERVICE_UNAVAILABLE)
async def failure() -> dict[str, str]:
    return {"status": "failure"}
