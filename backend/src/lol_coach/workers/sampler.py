"""High-rank match sampling.

Pulls a slice of Challenger / GM / Master players for a platform, then for each
fetches their recent ranked solo match IDs and ingests the matches via the
shared ingestion service.

Designed to be invoked both:
  - Manually via `lol-coach ingest sample`
  - Periodically via ARQ
"""

from __future__ import annotations

import asyncio
import random
from dataclasses import dataclass

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from lol_coach.riot.client import AsyncRiotClient
from lol_coach.riot.endpoints import MatchAPI
from lol_coach.riot.league import LeagueAPI, LeagueEntry, SummonerAPI
from lol_coach.riot.regions import regional_for
from lol_coach.services.ingest import MatchIngestService

log = structlog.get_logger(__name__)


@dataclass
class SamplingResult:
    platform: str
    players_sampled: int
    matches_seen: int
    matches_ingested: int


async def sample_high_rank(
    client: AsyncRiotClient,
    session: AsyncSession,
    platform: str,
    *,
    n_players: int = 20,
    matches_per_player: int = 20,
    concurrency: int = 5,
    queue_id: int = 420,
) -> SamplingResult:
    """One-shot: fetch top-rank players' recent matches and ingest them.

    `n_players` is sampled at random from the union of Challenger + GM + Master.
    """
    platform = platform.lower()
    regional = regional_for(platform)
    league = LeagueAPI(client)
    summoner = SummonerAPI(client)
    match_api = MatchAPI(client)
    ingest = MatchIngestService(session, match_api)

    log.info("sampler_start", platform=platform, n_players=n_players)

    challenger, grandmaster, master = await asyncio.gather(
        league.challenger(platform),
        league.grandmaster(platform),
        league.master(platform),
    )
    all_entries: list[LeagueEntry] = [
        *challenger.entries,
        *grandmaster.entries,
        *master.entries,
    ]
    if not all_entries:
        log.warning("sampler_no_entries", platform=platform)
        return SamplingResult(platform=platform, players_sampled=0, matches_seen=0, matches_ingested=0)

    sample = random.sample(all_entries, k=min(n_players, len(all_entries)))

    # league-v4 entries may not include puuid; convert via summoner-v4 if needed
    sem = asyncio.Semaphore(concurrency)

    async def to_puuid(entry: LeagueEntry) -> str | None:
        if entry.puuid:
            return entry.puuid
        if entry.summoner_id is None:
            return None
        async with sem:
            data = await summoner.by_summoner_id(platform, entry.summoner_id)
            puuid = data.get("puuid")
            return puuid if isinstance(puuid, str) else None

    raw_puuids = await asyncio.gather(*(to_puuid(e) for e in sample))
    puuids: list[str] = [p for p in raw_puuids if p]

    # Collect match IDs across all sampled players
    async def ids_for(puuid: str) -> list[str]:
        async with sem:
            return await match_api.ids_by_puuid(
                regional, puuid, count=matches_per_player, queue=queue_id
            )

    id_lists = await asyncio.gather(*(ids_for(p) for p in puuids))
    all_ids = sorted({mid for sub in id_lists for mid in sub})

    log.info("sampler_match_ids", platform=platform, players=len(puuids), match_ids=len(all_ids))

    # Ingest (skips matches already in DB)
    before = len(all_ids)
    matches = await ingest.get_or_fetch_many(regional, all_ids, concurrency=concurrency)
    log.info("sampler_done", platform=platform, ingested=len(matches), seen=before)

    return SamplingResult(
        platform=platform,
        players_sampled=len(puuids),
        matches_seen=before,
        matches_ingested=len(matches),
    )
