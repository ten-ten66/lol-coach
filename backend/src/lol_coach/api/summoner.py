from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, HTTPException, Path, Query
from pydantic import BaseModel

from lol_coach.api.deps import DbDep, RiotDep
from lol_coach.riot.errors import NotFoundError as RiotNotFound
from lol_coach.riot.regions import PLATFORM_TO_REGIONAL, regional_for
from lol_coach.services.summoner_profile import (
    RankEntry,
    SummonerProfileService,
)
from lol_coach.services.summoner_stats import (
    ChampionAgg,
    MatchSummary,
    SummonerStatsService,
)

router = APIRouter(prefix="/summoner", tags=["summoner"])


class ChampionAggOut(BaseModel):
    champion: str
    games: int
    wins: int
    win_rate: float
    kda: float
    avg_cs: float

    @classmethod
    def from_agg(cls, a: ChampionAgg) -> ChampionAggOut:
        return cls(
            champion=a.champion,
            games=a.games,
            wins=a.wins,
            win_rate=round(a.win_rate, 4),
            kda=round(a.kda, 2),
            avg_cs=round(a.avg_cs, 1),
        )


class MatchSummaryOut(BaseModel):
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

    @classmethod
    def from_match(cls, m: MatchSummary) -> MatchSummaryOut:
        return cls(**m.__dict__)


class SummonerStatsOut(BaseModel):
    game_name: str
    tag_line: str
    puuid: str
    platform: str
    total_games: int
    total_wins: int
    win_rate: float
    by_champion: list[ChampionAggOut]
    matches: list[MatchSummaryOut]


def _validate_platform(platform: str) -> str:
    if platform.lower() not in PLATFORM_TO_REGIONAL:
        raise HTTPException(
            status_code=400,
            detail=f"unknown platform '{platform}'. Known: {sorted(PLATFORM_TO_REGIONAL)}",
        )
    return platform.lower()


@router.get(
    "/{platform}/{game_name}/{tag_line}/recent",
    response_model=SummonerStatsOut,
    responses={404: {"description": "Riot ID not found"}},
)
async def recent_stats(
    db: DbDep,
    client: RiotDep,
    platform: str = Path(..., description="Platform route (jp1, kr, na1, ...)"),
    game_name: str = Path(...),
    tag_line: str = Path(...),
    count: int = Query(20, ge=1, le=100),
    queue: int = Query(420, description="Queue ID (420=ranked solo, 0=all)"),
) -> SummonerStatsOut:
    platform = _validate_platform(platform)
    regional = regional_for(platform)
    service = SummonerStatsService(client, db)
    try:
        stats = await service.fetch(
            regional,
            game_name,
            tag_line,
            count=count,
            queue=queue if queue != 0 else None,
        )
    except RiotNotFound as e:
        raise HTTPException(status_code=404, detail=str(e)) from e

    return SummonerStatsOut(
        game_name=stats.game_name,
        tag_line=stats.tag_line,
        puuid=stats.puuid,
        platform=platform,
        total_games=stats.total_games,
        total_wins=stats.total_wins,
        win_rate=round(stats.win_rate, 4),
        by_champion=[ChampionAggOut.from_agg(c) for c in stats.by_champion],
        matches=[MatchSummaryOut.from_match(m) for m in stats.matches],
    )


class RankEntryOut(BaseModel):
    queue_type: str
    tier: str
    rank: str
    league_points: int
    wins: int
    losses: int
    win_rate: float

    @classmethod
    def from_entry(cls, e: RankEntry) -> RankEntryOut:
        return cls(
            queue_type=e.queue_type,
            tier=e.tier,
            rank=e.rank,
            league_points=e.league_points,
            wins=e.wins,
            losses=e.losses,
            win_rate=round(e.win_rate, 4),
        )


class SummonerProfileOut(BaseModel):
    game_name: str
    tag_line: str
    puuid: str
    platform: str
    profile_icon_id: int
    summoner_level: int
    ranks: list[RankEntryOut]


@router.get(
    "/{platform}/{game_name}/{tag_line}/profile",
    response_model=SummonerProfileOut,
    responses={404: {"description": "Riot ID not found"}},
)
async def summoner_profile(
    client: RiotDep,
    platform: str = Path(..., description="Platform route (jp1, kr, na1, ...)"),
    game_name: str = Path(...),
    tag_line: str = Path(...),
) -> SummonerProfileOut:
    platform = _validate_platform(platform)
    regional = regional_for(platform)
    service = SummonerProfileService(client)
    try:
        profile = await service.fetch(regional, platform, game_name, tag_line)
    except RiotNotFound as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    return SummonerProfileOut(
        game_name=profile.game_name,
        tag_line=profile.tag_line,
        puuid=profile.puuid,
        platform=platform,
        profile_icon_id=profile.profile_icon_id,
        summoner_level=profile.summoner_level,
        ranks=[RankEntryOut.from_entry(r) for r in profile.ranks],
    )
