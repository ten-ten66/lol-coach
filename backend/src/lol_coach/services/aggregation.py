"""Recompute matchup and synergy aggregate tables from raw participants.

These are full recomputes — TRUNCATE + bulk INSERT. Cheap until we hit millions
of matches. When that becomes a problem, switch to incremental updates tracked
by `matches.aggregated_at`.
"""

from __future__ import annotations

import structlog
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

log = structlog.get_logger(__name__)


_MATCHUP_SQL = text(
    """
    INSERT INTO champion_matchups_agg (champion_a, champion_b, role, patch, tier_band, games, wins_a, updated_at)
    SELECT
      LEAST(p1.champion_id, p2.champion_id)                                     AS champion_a,
      GREATEST(p1.champion_id, p2.champion_id)                                  AS champion_b,
      p1.team_position                                                          AS role,
      m.patch                                                                   AS patch,
      'ALL'                                                                     AS tier_band,
      COUNT(*)                                                                  AS games,
      COUNT(*) FILTER (
        WHERE (p1.champion_id < p2.champion_id AND p1.win)
           OR (p2.champion_id < p1.champion_id AND p2.win)
      )                                                                          AS wins_a,
      NOW()                                                                     AS updated_at
    FROM participants p1
    JOIN participants p2
      ON p1.match_id = p2.match_id
     AND p1.team_id <> p2.team_id
     AND p1.team_position = p2.team_position
     AND p1.champion_id < p2.champion_id
     AND p1.team_position <> ''
     AND p1.team_position IS NOT NULL
    JOIN matches m ON p1.match_id = m.match_id
    WHERE m.queue_id = 420
    GROUP BY 1, 2, 3, 4, 5
    """
)


_SYNERGY_SQL = text(
    """
    INSERT INTO champion_synergy_agg (champion_a, champion_b, patch, tier_band, games, wins, updated_at)
    SELECT
      LEAST(p1.champion_id, p2.champion_id)                                     AS champion_a,
      GREATEST(p1.champion_id, p2.champion_id)                                  AS champion_b,
      m.patch                                                                   AS patch,
      'ALL'                                                                     AS tier_band,
      COUNT(*)                                                                  AS games,
      COUNT(*) FILTER (WHERE p1.win)                                            AS wins,
      NOW()                                                                     AS updated_at
    FROM participants p1
    JOIN participants p2
      ON p1.match_id = p2.match_id
     AND p1.team_id = p2.team_id
     AND p1.champion_id < p2.champion_id
    JOIN matches m ON p1.match_id = m.match_id
    WHERE m.queue_id = 420
    GROUP BY 1, 2, 3, 4
    """
)


async def recompute_matchups(session: AsyncSession) -> int:
    """Truncate and rebuild champion_matchups_agg. Returns rows inserted."""
    await session.execute(text("TRUNCATE TABLE champion_matchups_agg"))
    result = await session.execute(_MATCHUP_SQL)
    rows = int(getattr(result, "rowcount", 0) or 0)
    log.info("matchups_recomputed", rows=rows)
    return rows


async def recompute_synergies(session: AsyncSession) -> int:
    """Truncate and rebuild champion_synergy_agg. Returns rows inserted."""
    await session.execute(text("TRUNCATE TABLE champion_synergy_agg"))
    result = await session.execute(_SYNERGY_SQL)
    rows = int(getattr(result, "rowcount", 0) or 0)
    log.info("synergies_recomputed", rows=rows)
    return rows


async def recompute_all(session: AsyncSession) -> tuple[int, int]:
    matchup_rows = await recompute_matchups(session)
    synergy_rows = await recompute_synergies(session)
    return matchup_rows, synergy_rows
