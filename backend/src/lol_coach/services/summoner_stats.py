"""Aggregate recent match data into per-champion stats.

Uses the match ingestion service for DB-backed caching so repeated lookups
don't re-hit the Riot API.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from lol_coach.models import Match as MatchRow
from lol_coach.riot.client import AsyncRiotClient
from lol_coach.riot.endpoints import AccountAPI, MatchAPI
from lol_coach.services.ingest import MatchIngestService


@dataclass
class MatchSummary:
    match_id: str
    queue_id: int
    game_start_at: datetime
    game_duration_sec: int
    champion: str
    role: str
    win: bool
    kills: int
    deaths: int
    assists: int
    cs: int


@dataclass
class ChampionAgg:
    champion: str
    games: int = 0
    wins: int = 0
    kills: int = 0
    deaths: int = 0
    assists: int = 0
    cs: int = 0

    @property
    def win_rate(self) -> float:
        return self.wins / self.games if self.games else 0.0

    @property
    def kda(self) -> float:
        if self.deaths == 0:
            return float(self.kills + self.assists)
        return (self.kills + self.assists) / self.deaths

    @property
    def avg_cs(self) -> float:
        return self.cs / self.games if self.games else 0.0


@dataclass
class SummonerStats:
    game_name: str
    tag_line: str
    puuid: str
    total_games: int
    total_wins: int
    matches: list[MatchSummary]
    by_champion: list[ChampionAgg] = field(default_factory=list)

    @property
    def win_rate(self) -> float:
        return self.total_wins / self.total_games if self.total_games else 0.0


class SummonerStatsService:
    def __init__(self, client: AsyncRiotClient, session: AsyncSession) -> None:
        self._account = AccountAPI(client)
        self._match = MatchAPI(client)
        self._ingest = MatchIngestService(session, self._match)

    async def fetch(
        self,
        regional: str,
        game_name: str,
        tag_line: str,
        *,
        count: int = 20,
        queue: int | None = 420,
        concurrency: int = 5,
    ) -> SummonerStats:
        account = await self._account.by_riot_id(regional, game_name, tag_line)
        match_ids = await self._match.ids_by_puuid(
            regional, account.puuid, count=count, queue=queue
        )
        matches = await self._ingest.get_or_fetch_many(regional, match_ids, concurrency=concurrency)
        return _aggregate(account.game_name, account.tag_line, account.puuid, matches)


def _aggregate(game_name: str, tag_line: str, puuid: str, matches: list[MatchRow]) -> SummonerStats:
    summaries: list[MatchSummary] = []
    aggs: dict[str, ChampionAgg] = {}
    total_wins = 0

    for m in matches:
        me = next((p for p in m.participants if p.puuid == puuid), None)
        if me is None:
            continue
        summaries.append(
            MatchSummary(
                match_id=m.match_id,
                queue_id=m.queue_id,
                game_start_at=m.game_start_at,
                game_duration_sec=m.game_duration_sec,
                champion=me.champion_name,
                role=me.team_position or "UNKNOWN",
                win=me.win,
                kills=me.kills,
                deaths=me.deaths,
                assists=me.assists,
                cs=me.cs,
            )
        )
        if me.win:
            total_wins += 1
        agg = aggs.setdefault(me.champion_name, ChampionAgg(champion=me.champion_name))
        agg.games += 1
        agg.wins += 1 if me.win else 0
        agg.kills += me.kills
        agg.deaths += me.deaths
        agg.assists += me.assists
        agg.cs += me.cs

    by_champion = sorted(aggs.values(), key=lambda a: (-a.games, -a.win_rate, a.champion))
    return SummonerStats(
        game_name=game_name,
        tag_line=tag_line,
        puuid=puuid,
        total_games=len(summaries),
        total_wins=total_wins,
        matches=summaries,
        by_champion=by_champion,
    )
