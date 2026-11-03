from __future__ import annotations

from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel, Field
from sqlalchemy import select

from lol_coach.api.deps import DbDep
from lol_coach.models import ChampionMatchupAgg
from lol_coach.services.recommendation import PickedChampion, recommend

router = APIRouter(prefix="/draft", tags=["draft"])

Role = Literal["TOP", "JUNGLE", "MIDDLE", "BOTTOM", "UTILITY"]


class PickIn(BaseModel):
    champion_id: int = Field(..., ge=1, description="Riot champion ID")
    role: Role


class DraftRequest(BaseModel):
    patch: str = Field(..., examples=["14.10"])
    tier_band: str = Field("ALL", description="Tier band; current data uses 'ALL'")
    allies: list[PickIn] = Field(default_factory=list)
    enemies: list[PickIn] = Field(default_factory=list)
    missing_role: Role
    top_n: int = Field(5, ge=1, le=20)


class RecommendationOut(BaseModel):
    champion_id: int
    champion_name: str
    score: float
    vs_enemies_score: float
    synergy_score: float
    matchup_samples: int
    synergy_samples: int


class DraftResponse(BaseModel):
    patch: str
    tier_band: str
    missing_role: Role
    recommendations: list[RecommendationOut]


@router.post("/recommend", response_model=DraftResponse)
async def recommend_picks(req: DraftRequest, db: DbDep) -> DraftResponse:
    recs = await recommend(
        db,
        patch=req.patch,
        tier_band=req.tier_band,
        allies=[PickedChampion(p.champion_id, p.role) for p in req.allies],
        enemies=[PickedChampion(p.champion_id, p.role) for p in req.enemies],
        missing_role=req.missing_role,
        top_n=req.top_n,
    )
    return DraftResponse(
        patch=req.patch,
        tier_band=req.tier_band,
        missing_role=req.missing_role,
        recommendations=[
            RecommendationOut(
                champion_id=r.champion_id,
                champion_name=r.champion_name,
                score=round(r.score, 5),
                vs_enemies_score=round(r.breakdown.vs_enemies_score, 5),
                synergy_score=round(r.breakdown.synergy_score, 5),
                matchup_samples=r.breakdown.matchup_samples,
                synergy_samples=r.breakdown.synergy_samples,
            )
            for r in recs
        ],
    )


@router.get("/patches")
async def draft_patches(db: DbDep) -> dict[str, list[str]]:
    """Patch / tier-band combos available in the aggregate tables (for UI dropdowns)."""
    patches = list((await db.execute(select(ChampionMatchupAgg.patch).distinct())).scalars().all())
    bands = list(
        (await db.execute(select(ChampionMatchupAgg.tier_band).distinct())).scalars().all()
    )

    def _key(p: str) -> tuple[int, ...]:
        try:
            return tuple(int(x) for x in p.split("."))
        except ValueError:
            return (0,)

    patches.sort(key=_key, reverse=True)
    return {"patches": patches, "tier_bands": sorted(bands)}
