"""Match ingestion: fetch from Riot if not in DB, persist, return ORM rows.

Champions and patches are upserted on-the-fly from match data. This avoids
needing a separate Data Dragon sync step before we can ingest matches.
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime

import structlog
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from lol_coach.models import Champion, Match, Participant, Patch
from lol_coach.riot.endpoints import MatchAPI
from lol_coach.riot.models import Match as RiotMatch

log = structlog.get_logger(__name__)


class MatchIngestService:
    def __init__(self, session: AsyncSession, match_api: MatchAPI) -> None:
        self._session = session
        self._match_api = match_api

    async def get_or_fetch(self, regional: str, match_id: str) -> Match:
        existing = await self._session.get(Match, match_id)
        if existing is not None:
            return existing
        riot_match = await self._match_api.by_id(regional, match_id)
        return await self._persist(regional, riot_match)

    async def get_or_fetch_many(
        self, regional: str, match_ids: list[str], concurrency: int = 5
    ) -> list[Match]:
        # Fetch what we have in DB
        stmt = select(Match).where(Match.match_id.in_(match_ids))
        result = await self._session.execute(stmt)
        cached = {m.match_id: m for m in result.scalars().all()}
        missing = [mid for mid in match_ids if mid not in cached]
        if missing:
            log.info("ingest_fetching", count=len(missing), cached=len(cached))
            sem = asyncio.Semaphore(concurrency)

            async def fetch_one(mid: str) -> RiotMatch:
                async with sem:
                    return await self._match_api.by_id(regional, mid)

            fetched = await asyncio.gather(*(fetch_one(mid) for mid in missing))
            for rm in fetched:
                persisted = await self._persist(regional, rm)
                cached[persisted.match_id] = persisted
        return [cached[mid] for mid in match_ids if mid in cached]

    async def _persist(self, region: str, rm: RiotMatch) -> Match:
        patch_version = _parse_patch(rm.info.game_version)
        await self._upsert_patch(patch_version)
        await self._upsert_champions(
            [(p.champion_id, p.champion_name) for p in rm.info.participants]
        )

        # gameDuration is seconds when gameEndTimestamp is present (post-11.20),
        # but Riot sometimes returns ms for older matches; clamp.
        duration = rm.info.game_duration
        if duration > 24 * 3600:  # >24h => almost certainly ms
            duration = duration // 1000

        winning_team: int | None = None
        winners = {p.team_id for p in rm.info.participants if p.win}
        if len(winners) == 1:
            winning_team = next(iter(winners))

        game_start_at = datetime.fromtimestamp(rm.info.game_creation / 1000, tz=UTC)

        match = Match(
            match_id=rm.metadata.match_id,
            region=region,
            queue_id=rm.info.queue_id,
            patch=patch_version,
            game_start_at=game_start_at,
            game_duration_sec=duration,
            winning_team=winning_team,
        )
        match.participants = [
            Participant(
                match_id=rm.metadata.match_id,
                puuid=p.puuid,
                team_id=p.team_id,
                champion_id=p.champion_id,
                champion_name=p.champion_name,
                team_position=p.team_position or None,
                win=p.win,
                kills=p.kills,
                deaths=p.deaths,
                assists=p.assists,
                cs=p.total_minions_killed + p.neutral_minions_killed,
                gold_earned=p.gold_earned,
            )
            for p in rm.info.participants
        ]
        self._session.add(match)
        await self._session.flush()
        return match

    async def _upsert_patch(self, version: str) -> None:
        major, minor = _split_patch(version)
        stmt = (
            pg_insert(Patch)
            .values(version=version, major=major, minor=minor)
            .on_conflict_do_nothing(index_elements=["version"])
        )
        await self._session.execute(stmt)

    async def _upsert_champions(self, champions: list[tuple[int, str]]) -> None:
        if not champions:
            return
        rows = [
            {"id": cid, "key": name, "name": name} for cid, name in {*champions}
        ]
        stmt = (
            pg_insert(Champion)
            .values(rows)
            .on_conflict_do_nothing(index_elements=["id"])
        )
        await self._session.execute(stmt)


def _parse_patch(game_version: str) -> str:
    """'14.10.1.1234' → '14.10'."""
    parts = game_version.split(".")
    if len(parts) >= 2:
        return f"{parts[0]}.{parts[1]}"
    return game_version


def _split_patch(version: str) -> tuple[int, int]:
    major_str, _, minor_str = version.partition(".")
    return int(major_str), int(minor_str) if minor_str else 0
