from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends, Request

from app.core.config import Settings, get_settings
from app.core.db import AsyncSession, Database
from app.core.release import ReleaseInfo


def get_database(request: Request) -> Database:
    database: Database = request.app.state.db
    return database


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
ReleaseDep = Annotated[ReleaseInfo, Depends(get_release)]
SessionDep = Annotated[AsyncSession, Depends(get_session)]
