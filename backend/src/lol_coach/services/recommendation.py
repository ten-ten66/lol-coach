"""Draft recommendation: rank candidate champions by combined matchup + synergy
win rate, weighted by sample size to penalize uncertain estimates.

Scoring (per candidate champion `c`):

  score(c) = w_vs * sum_over_enemies(  winrate(c vs e) - 0.5 ) / |enemies|
           + w_syn * sum_over_allies(   winrate(c+ a) - 0.5 ) / |allies|

Each term is shrunken toward 0.5 (no edge) when the sample is small:

  winrate_shrunk(games, wins) =
      (wins + ALPHA * 0.5) / (games + ALPHA)

ALPHA acts as a pseudo-count. Pairs with games < MIN_SAMPLES contribute 0.

The endpoint returns a list of {champion, score, sample sizes, breakdown}.
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from lol_coach.models import Champion, ChampionMatchupAgg, ChampionSynergyAgg

ALPHA = 100.0
MIN_SAMPLES = 1  # very low for prototype with sparse data; raise once we have 10k+ matches
W_VS = 0.5
W_SYN = 0.5


@dataclass(frozen=True)
class PickedChampion:
    champion_id: int
    role: str


@dataclass
class Breakdown:
    vs_enemies_score: float
    synergy_score: float
    matchup_samples: int
    synergy_samples: int


@dataclass
class Recommendation:
    champion_id: int
    champion_name: str
    score: float
    breakdown: Breakdown


def _shrunk_winrate(games: int, wins: int) -> float:
    return (wins + ALPHA * 0.5) / (games + ALPHA)


async def recommend(
    session: AsyncSession,
    *,
    patch: str,
    tier_band: str = "ALL",
    allies: list[PickedChampion],
    enemies: list[PickedChampion],
    missing_role: str,
    top_n: int = 5,
) -> list[Recommendation]:
    picked_ids = {p.champion_id for p in (*allies, *enemies)}

    # All champions to evaluate
    all_champ_rows = (
        (await session.execute(select(Champion))).scalars().all()
    )
    candidates = [c for c in all_champ_rows if c.id not in picked_ids]

    # Pull matchups: candidate vs enemies in missing_role
    enemy_ids = [e.champion_id for e in enemies if e.role == missing_role]
    matchup_data: dict[tuple[int, int], tuple[int, int]] = {}
    if enemy_ids:
        cand_ids = [c.id for c in candidates]
        # We only care about rows where (a,b) is (min, max) of {candidate, enemy}
        # so the join condition is symmetric.
        m_q = select(
            ChampionMatchupAgg.champion_a,
            ChampionMatchupAgg.champion_b,
            ChampionMatchupAgg.games,
            ChampionMatchupAgg.wins_a,
        ).where(
            ChampionMatchupAgg.role == missing_role,
            ChampionMatchupAgg.patch == patch,
            ChampionMatchupAgg.tier_band == tier_band,
            or_(
                and_(
                    ChampionMatchupAgg.champion_a.in_(cand_ids),
                    ChampionMatchupAgg.champion_b.in_(enemy_ids),
                ),
                and_(
                    ChampionMatchupAgg.champion_a.in_(enemy_ids),
                    ChampionMatchupAgg.champion_b.in_(cand_ids),
                ),
            ),
        )
        for a, b, games, wins_a in (await session.execute(m_q)).all():
            matchup_data[(a, b)] = (games, wins_a)

    # Pull synergies: candidate with each ally (any role)
    ally_ids = [a.champion_id for a in allies]
    synergy_data: dict[tuple[int, int], tuple[int, int]] = {}
    if ally_ids:
        cand_ids = [c.id for c in candidates]
        s_q = select(
            ChampionSynergyAgg.champion_a,
            ChampionSynergyAgg.champion_b,
            ChampionSynergyAgg.games,
            ChampionSynergyAgg.wins,
        ).where(
            ChampionSynergyAgg.patch == patch,
            ChampionSynergyAgg.tier_band == tier_band,
            or_(
                and_(
                    ChampionSynergyAgg.champion_a.in_(cand_ids),
                    ChampionSynergyAgg.champion_b.in_(ally_ids),
                ),
                and_(
                    ChampionSynergyAgg.champion_a.in_(ally_ids),
                    ChampionSynergyAgg.champion_b.in_(cand_ids),
                ),
            ),
        )
        for a, b, games, wins in (await session.execute(s_q)).all():
            synergy_data[(a, b)] = (games, wins)

    recommendations: list[Recommendation] = []
    for c in candidates:
        vs_terms: list[float] = []
        vs_samples = 0
        for eid in enemy_ids:
            a, b = sorted((c.id, eid))
            data = matchup_data.get((a, b))
            if data is None or data[0] < MIN_SAMPLES:
                continue
            games, wins_a = data
            # wins_a is wins for champion_a (the lower id). If c is a, that's c's wins.
            wins_for_c = wins_a if c.id == a else games - wins_a
            wr = _shrunk_winrate(games, wins_for_c)
            vs_terms.append(wr - 0.5)
            vs_samples += games

        syn_terms: list[float] = []
        syn_samples = 0
        for aid in ally_ids:
            a, b = sorted((c.id, aid))
            data = synergy_data.get((a, b))
            if data is None or data[0] < MIN_SAMPLES:
                continue
            games, wins = data
            wr = _shrunk_winrate(games, wins)
            syn_terms.append(wr - 0.5)
            syn_samples += games

        vs_score = sum(vs_terms) / len(vs_terms) if vs_terms else 0.0
        syn_score = sum(syn_terms) / len(syn_terms) if syn_terms else 0.0
        score = W_VS * vs_score + W_SYN * syn_score

        recommendations.append(
            Recommendation(
                champion_id=c.id,
                champion_name=c.name,
                score=score,
                breakdown=Breakdown(
                    vs_enemies_score=vs_score,
                    synergy_score=syn_score,
                    matchup_samples=vs_samples,
                    synergy_samples=syn_samples,
                ),
            )
        )

    recommendations.sort(
        key=lambda r: (
            -r.score,
            -(r.breakdown.matchup_samples + r.breakdown.synergy_samples),
            r.champion_name,
        )
    )
    return recommendations[:top_n]
