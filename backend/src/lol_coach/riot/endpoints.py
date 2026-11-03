"""Thin wrappers over Riot API endpoints used by Phase 1.

These return parsed Pydantic models. Region/platform routing is the caller's
responsibility — `account-v1` and `match-v5` live on regional routes
(`asia`, `americas`, `europe`, `sea`), while `summoner-v4` and `league-v4`
live on platform routes (`jp1`, `kr`, `na1`, etc.).
"""

from __future__ import annotations

from urllib.parse import quote

from lol_coach.riot.client import AsyncRiotClient
from lol_coach.riot.models import Match, RiotAccount


class AccountAPI:
    def __init__(self, client: AsyncRiotClient) -> None:
        self._client = client

    async def by_riot_id(self, regional: str, game_name: str, tag_line: str) -> RiotAccount:
        path = f"/riot/account/v1/accounts/by-riot-id/{quote(game_name)}/{quote(tag_line)}"
        data = await self._client.get(regional, path)
        return RiotAccount.model_validate(data)

    async def by_puuid(self, regional: str, puuid: str) -> RiotAccount:
        path = f"/riot/account/v1/accounts/by-puuid/{quote(puuid)}"
        data = await self._client.get(regional, path)
        return RiotAccount.model_validate(data)


class MatchAPI:
    def __init__(self, client: AsyncRiotClient) -> None:
        self._client = client

    async def ids_by_puuid(
        self,
        regional: str,
        puuid: str,
        *,
        start: int = 0,
        count: int = 20,
        queue: int | None = None,
        type_: str | None = None,
        start_time: int | None = None,
        end_time: int | None = None,
    ) -> list[str]:
        params: dict[str, int | str] = {"start": start, "count": count}
        if queue is not None:
            params["queue"] = queue
        if type_ is not None:
            params["type"] = type_
        if start_time is not None:
            params["startTime"] = start_time
        if end_time is not None:
            params["endTime"] = end_time
        path = f"/lol/match/v5/matches/by-puuid/{puuid}/ids"
        data = await self._client.get(regional, path, params=params)
        return list(data)

    async def by_id(self, regional: str, match_id: str) -> Match:
        path = f"/lol/match/v5/matches/{match_id}"
        data = await self._client.get(regional, path)
        return Match.model_validate(data)
