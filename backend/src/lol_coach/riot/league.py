"""Endpoint wrappers for league-v4 (rank tiers and entries)."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from lol_coach.riot.client import AsyncRiotClient

Queue = Literal["RANKED_SOLO_5x5", "RANKED_FLEX_SR"]


class _LeagueModel(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)


class LeagueEntry(_LeagueModel):
    summoner_id: str | None = Field(default=None, alias="summonerId")
    puuid: str | None = None
    rank: str
    league_points: int = Field(alias="leaguePoints")
    wins: int
    losses: int


class League(_LeagueModel):
    tier: str
    queue: str
    name: str
    entries: list[LeagueEntry]


class LeagueEntryFull(_LeagueModel):
    """A ranked entry from league-v4 entries-by-puuid (includes queue + tier)."""

    queue_type: str = Field(alias="queueType")
    tier: str
    rank: str
    league_points: int = Field(alias="leaguePoints")
    wins: int
    losses: int


class SummonerDTO(_LeagueModel):
    """summoner-v4 summoner record (icon + level)."""

    id: str
    profile_icon_id: int = Field(alias="profileIconId")
    summoner_level: int = Field(alias="summonerLevel")


class LeagueAPI:
    def __init__(self, client: AsyncRiotClient) -> None:
        self._client = client

    async def challenger(self, platform: str, queue: Queue = "RANKED_SOLO_5x5") -> League:
        data = await self._client.get(
            platform, f"/lol/league/v4/challengerleagues/by-queue/{queue}"
        )
        return League.model_validate(data)

    async def grandmaster(self, platform: str, queue: Queue = "RANKED_SOLO_5x5") -> League:
        data = await self._client.get(
            platform, f"/lol/league/v4/grandmasterleagues/by-queue/{queue}"
        )
        return League.model_validate(data)

    async def master(self, platform: str, queue: Queue = "RANKED_SOLO_5x5") -> League:
        data = await self._client.get(platform, f"/lol/league/v4/masterleagues/by-queue/{queue}")
        return League.model_validate(data)

    async def entries_by_puuid(self, platform: str, puuid: str) -> list[LeagueEntryFull]:
        """All ranked entries (solo/flex) for a puuid via league-v4."""
        data = await self._client.get(platform, f"/lol/league/v4/entries/by-puuid/{puuid}")
        return [LeagueEntryFull.model_validate(e) for e in data]


class SummonerAPI:
    """summoner-v4: needed to convert summonerId → puuid in older league-v4 responses."""

    def __init__(self, client: AsyncRiotClient) -> None:
        self._client = client

    async def by_summoner_id(self, platform: str, summoner_id: str) -> dict[str, object]:
        data: dict[str, object] = await self._client.get(
            platform, f"/lol/summoner/v4/summoners/{summoner_id}"
        )
        return data

    async def by_puuid(self, platform: str, puuid: str) -> SummonerDTO:
        data = await self._client.get(platform, f"/lol/summoner/v4/summoners/by-puuid/{puuid}")
        return SummonerDTO.model_validate(data)
