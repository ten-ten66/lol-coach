from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from lol_coach.config import Settings, get_settings
from lol_coach.db.session import get_session_factory
from lol_coach.riot.client import AsyncRiotClient


async def get_db() -> AsyncIterator[AsyncSession]:
    factory = get_session_factory()
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def get_riot_client() -> AsyncIterator[AsyncRiotClient]:
    settings = get_settings()
    async with AsyncRiotClient(settings.riot_api_key.get_secret_value()) as client:
        yield client


SettingsDep = Annotated[Settings, Depends(get_settings)]
DbDep = Annotated[AsyncSession, Depends(get_db)]
RiotDep = Annotated[AsyncRiotClient, Depends(get_riot_client)]
