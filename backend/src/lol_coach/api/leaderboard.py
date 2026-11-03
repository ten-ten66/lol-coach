from __future__ import annotations

from fastapi import APIRouter, HTTPException, Path, Query
from pydantic import BaseModel

from lol_coach.api.deps import RiotDep
from lol_coach.riot.regions import PLATFORM_TO_REGIONAL, regional_for
from lol_coach.services.leaderboard import LeaderboardService

router = APIRouter(prefix="/leaderboard", tags=["leaderboard"])


class LadderEntryOut(BaseModel):
    rank_position: int
    game_name: str | None
    tag_line: str | None
    league_points: int
    wins: int
    losses: int
    win_rate: float


class LadderOut(BaseModel):
    platform: str
    tier: str
    queue: str
    entries: list[LadderEntryOut]


@router.get("/{platform}", response_model=LadderOut)
async def leaderboard(
    client: RiotDep,
    platform: str = Path(..., description="Platform route (kr, jp1, na1, ...)"),
    tier: str = Query("challenger", description="challenger | grandmaster | master"),
    queue: str = Query("RANKED_SOLO_5x5"),
    limit: int = Query(25, ge=1, le=100),
) -> LadderOut:
    if platform.lower() not in PLATFORM_TO_REGIONAL:
        raise HTTPException(status_code=400, detail=f"unknown platform '{platform}'")
    platform = platform.lower()
    regional = regional_for(platform)
    service = LeaderboardService(client)
    ladder = await service.fetch(platform, regional, tier, queue, limit)
    return LadderOut(
        platform=platform,
        tier=ladder.tier,
        queue=ladder.queue,
        entries=[
            LadderEntryOut(
                rank_position=e.rank_position,
                game_name=e.game_name,
                tag_line=e.tag_line,
                league_points=e.league_points,
                wins=e.wins,
                losses=e.losses,
                win_rate=round(e.win_rate, 4),
            )
            for e in ladder.entries
        ],
    )
