"""ARQ worker configuration.

Run with: `uv run arq lol_coach.workers.arq_config.WorkerSettings`

Scheduled jobs:
  - sample_high_rank_all: every 6h, sample matches from JP1 + KR
  - recompute_aggregates: every 1h, refresh matchup/synergy tables
"""

from __future__ import annotations

from typing import Any, ClassVar
from urllib.parse import urlparse

from arq import cron
from arq.connections import RedisSettings

from lol_coach.config import get_settings
from lol_coach.db.session import session_scope
from lol_coach.riot.client import AsyncRiotClient
from lol_coach.services.aggregation import recompute_matchups, recompute_synergies
from lol_coach.workers.sampler import sample_high_rank


async def task_sample_high_rank(
    ctx: dict[str, object], platform: str, n_players: int = 20
) -> dict[str, object]:
    settings = get_settings()
    async with (
        AsyncRiotClient(settings.riot_api_key.get_secret_value()) as client,
        session_scope() as session,
    ):
        result = await sample_high_rank(client, session, platform, n_players=n_players)
        return {
            "platform": result.platform,
            "players": result.players_sampled,
            "ingested": result.matches_ingested,
            "seen": result.matches_seen,
        }


async def task_recompute_aggregates(ctx: dict[str, object]) -> dict[str, int]:
    async with session_scope() as session:
        m_rows = await recompute_matchups(session)
        s_rows = await recompute_synergies(session)
        return {"matchup_rows": m_rows, "synergy_rows": s_rows}


def _redis_settings() -> RedisSettings:
    parsed = urlparse(get_settings().redis_url)
    return RedisSettings(
        host=parsed.hostname or "localhost",
        port=parsed.port or 6379,
        database=int(parsed.path.lstrip("/") or 0),
    )


class WorkerSettings:
    redis_settings = _redis_settings()
    functions: ClassVar[list[Any]] = [task_sample_high_rank, task_recompute_aggregates]
    cron_jobs: ClassVar[list[Any]] = [
        cron(  # type: ignore[call-arg]  # arq cron accepts kwargs at runtime
            task_sample_high_rank,
            hour={0, 6, 12, 18},
            minute=0,
            kwargs={"platform": "jp1"},
        ),
        cron(task_recompute_aggregates, minute=30),
    ]
    job_timeout = 30 * 60
    keep_result = 60 * 60
