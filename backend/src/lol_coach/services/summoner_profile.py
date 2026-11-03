"""Fetch a summoner's public profile: Riot ID, level, icon, ranked entries.

Unlike :mod:`summoner_stats` (which aggregates match history), this only needs
account-v1, summoner-v4 and league-v4 — no DB. The two platform-route calls run
concurrently once the puuid is known.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass

from lol_coach.riot.client import AsyncRiotClient
from lol_coach.riot.endpoints import AccountAPI
from lol_coach.riot.league import LeagueAPI, SummonerAPI


@dataclass
class RankEntry:
    queue_type: str
    tier: str
    rank: str
    league_points: int
    wins: int
    losses: int

    @property
    def win_rate(self) -> float:
        total = self.wins + self.losses
        return self.wins / total if total else 0.0


@dataclass
class SummonerProfile:
    game_name: str
    tag_line: str
    puuid: str
    profile_icon_id: int
    summoner_level: int
    ranks: list[RankEntry]


class SummonerProfileService:
    def __init__(self, client: AsyncRiotClient) -> None:
        self._account = AccountAPI(client)
        self._summoner = SummonerAPI(client)
        self._league = LeagueAPI(client)

    async def fetch(
        self, regional: str, platform: str, game_name: str, tag_line: str
    ) -> SummonerProfile:
        account = await self._account.by_riot_id(regional, game_name, tag_line)
        dto, entries = await asyncio.gather(
            self._summoner.by_puuid(platform, account.puuid),
            self._league.entries_by_puuid(platform, account.puuid),
        )
        ranks = [
            RankEntry(
                queue_type=e.queue_type,
                tier=e.tier,
                rank=e.rank,
                league_points=e.league_points,
                wins=e.wins,
                losses=e.losses,
            )
            for e in entries
        ]
        return SummonerProfile(
            game_name=account.game_name,
            tag_line=account.tag_line,
            puuid=account.puuid,
            profile_icon_id=dto.profile_icon_id,
            summoner_level=dto.summoner_level,
            ranks=ranks,
        )
