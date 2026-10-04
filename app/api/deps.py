from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends, Request

from app.core.cache import Cache
from app.core.config import Settings, get_settings
from app.core.db import AsyncSession, Database
from app.core.release import ReleaseInfo
from app.visits.exceptions import CacheNotConfiguredError


def get_database(request: Request) -> Database:
    database: Database = request.app.state.db
    return database


def get_optional_cache(request: Request) -> Cache | None:
    cache: Cache | None = request.app.state.cache
    return cache


def get_cache(cache: Annotated[Cache | None, Depends(get_optional_cache)]) -> Cache:
    if cache is None:
        raise CacheNotConfiguredError
    return cache


def get_release(request: Request) -> ReleaseInfo:
    release: ReleaseInfo = request.app.state.release
    return release


async def get_session(
    database: Annotated[Database, Depends(get_database)],
) -> AsyncIterator[AsyncSession]:
    async with database.session_factory() as session:
        yield session


SettingsDep = Annotated[Settings, Depends(get_settings)]
DatabaseDep = Annotated[Database, Depends(get_database)]
OptionalCacheDep = Annotated[Cache | None, Depends(get_optional_cache)]
CacheDep = Annotated[Cache, Depends(get_cache)]
ReleaseDep = Annotated[ReleaseInfo, Depends(get_release)]
SessionDep = Annotated[AsyncSession, Depends(get_session)]
