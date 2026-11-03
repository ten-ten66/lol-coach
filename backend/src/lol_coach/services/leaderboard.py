"""Apex-tier leaderboard (Challenger / Grandmaster / Master) via league-v4.

league-v4 returns entries keyed by puuid/summonerId but without Riot IDs, so we
resolve display names with account-v1 (by-puuid) for the top `limit` entries.
All calls require a valid Riot API key.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import cast

from lol_coach.riot.client import AsyncRiotClient
from lol_coach.riot.endpoints import AccountAPI
from lol_coach.riot.league import LeagueAPI, Queue
from lol_coach.riot.models import RiotAccount


@dataclass
class LadderEntry:
    rank_position: int
    game_name: str | None
    tag_line: str | None
    puuid: str | None
    league_points: int
    wins: int
    losses: int

    @property
    def win_rate(self) -> float:
        total = self.wins + self.losses
        return self.wins / total if total else 0.0


@dataclass
class Ladder:
    tier: str
    queue: str
    entries: list[LadderEntry]


class LeaderboardService:
    def __init__(self, client: AsyncRiotClient) -> None:
        self._league = LeagueAPI(client)
        self._account = AccountAPI(client)

    async def fetch(
        self,
        platform: str,
        regional: str,
        tier: str,
        queue: str,
        limit: int,
        *,
        resolve_names: bool = True,
    ) -> Ladder:
        tier_u = tier.upper()
        q = cast(Queue, queue)
        if tier_u == "GRANDMASTER":
            league = await self._league.grandmaster(platform, q)
        elif tier_u == "MASTER":
            league = await self._league.master(platform, q)
        else:
            tier_u = "CHALLENGER"
            league = await self._league.challenger(platform, q)

        top = sorted(league.entries, key=lambda e: e.league_points, reverse=True)[:limit]

        names: dict[str, RiotAccount] = {}
        if resolve_names:
            puuids = [e.puuid for e in top if e.puuid]
            results = await asyncio.gather(
                *(self._account.by_puuid(regional, p) for p in puuids),
                return_exceptions=True,
            )
            for puuid, result in zip(puuids, results, strict=True):
                if isinstance(result, RiotAccount):
                    names[puuid] = result

        entries: list[LadderEntry] = []
        for i, e in enumerate(top, start=1):
            acct = names.get(e.puuid) if e.puuid else None
            entries.append(
                LadderEntry(
                    rank_position=i,
                    game_name=acct.game_name if acct else None,
                    tag_line=acct.tag_line if acct else None,
                    puuid=e.puuid,
                    league_points=e.league_points,
                    wins=e.wins,
                    losses=e.losses,
                )
            )
        return Ladder(tier=tier_u, queue=queue, entries=entries)
