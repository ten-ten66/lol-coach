from __future__ import annotations

from fastapi import APIRouter, Query
from pydantic import BaseModel
from sqlalchemy import select, text

from lol_coach.api.deps import DbDep
from lol_coach.models import Champion

router = APIRouter(prefix="/champions", tags=["champions"])


class ChampionOut(BaseModel):
    id: int
    key: str
    name: str


@router.get("", response_model=list[ChampionOut])
async def list_champions(db: DbDep) -> list[ChampionOut]:
    result = await db.execute(select(Champion).order_by(Champion.name))
    return [ChampionOut(id=c.id, key=c.key, name=c.name) for c in result.scalars()]


class ChampionStatOut(BaseModel):
    champion_id: int
    champion_name: str
    games: int
    wins: int
    win_rate: float
    pick_rate: float


@router.get("/stats", response_model=list[ChampionStatOut])
async def champion_stats(
    db: DbDep,
    role: str | None = Query(None, description="Role (TOP/JUNGLE/MIDDLE/BOTTOM/UTILITY)"),
    patch: str | None = Query(None, description="Patch filter, e.g. 16.10"),
    queue: int = Query(420, description="Queue ID (420=ranked solo)"),
    min_games: int = Query(1, ge=1, description="Minimum games to include a champion"),
) -> list[ChampionStatOut]:
    """Per-champion win/pick rates aggregated from locally ingested matches.

    Meaningfulness scales with how much match data has been ingested
    (`lol-coach ingest sample`). With a small sample the numbers are noisy.
    """
    # Build filters conditionally — avoids asyncpg ":param IS NULL" type ambiguity.
    role_norm = role.upper() if role else None
    where = ["m.queue_id = :queue", "p.team_position IS NOT NULL", "p.team_position <> ''"]
    params: dict[str, int | str] = {"queue": queue, "min_games": min_games}
    total_where = ["queue_id = :queue"]
    total_params: dict[str, int | str] = {"queue": queue}
    if patch:
        where.append("m.patch = :patch")
        total_where.append("patch = :patch")
        params["patch"] = patch
        total_params["patch"] = patch
    if role_norm:
        where.append("p.team_position = :role")
        params["role"] = role_norm

    total_sql = text(f"SELECT count(*) FROM matches WHERE {' AND '.join(total_where)}")
    stats_sql = text(
        f"""
        SELECT p.champion_id, c.name, count(*) AS games,
               count(*) FILTER (WHERE p.win) AS wins
        FROM participants p
        JOIN matches m ON p.match_id = m.match_id
        JOIN champions c ON c.id = p.champion_id
        WHERE {' AND '.join(where)}
        GROUP BY p.champion_id, c.name
        HAVING count(*) >= :min_games
        """
    )

    total_matches = int((await db.execute(total_sql, total_params)).scalar_one() or 0)
    rows = (await db.execute(stats_sql, params)).all()

    out: list[ChampionStatOut] = []
    for champion_id, name, games, wins in rows:
        g = int(games)
        w = int(wins)
        out.append(
            ChampionStatOut(
                champion_id=int(champion_id),
                champion_name=str(name),
                games=g,
                wins=w,
                win_rate=round(w / g, 4) if g else 0.0,
                pick_rate=round(g / total_matches, 4) if total_matches else 0.0,
            )
        )
    out.sort(key=lambda s: (-s.win_rate, -s.games, s.champion_name))
    return out
