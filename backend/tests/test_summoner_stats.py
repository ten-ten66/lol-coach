"""Unit tests for `_aggregate` — constructs ORM Match/Participant objects in
memory without a DB session, since `_aggregate` only reads simple fields.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from lol_coach.models import Match, Participant
from lol_coach.services.summoner_stats import _aggregate


def _participant(
    puuid: str = "P_ME",
    champion: str = "Ahri",
    *,
    win: bool = True,
    kills: int = 5,
    deaths: int = 2,
    assists: int = 8,
    cs: int = 200,
    role: str = "MIDDLE",
) -> Participant:
    return Participant(
        match_id="dummy",
        puuid=puuid,
        team_id=100 if win else 200,
        champion_id=103,
        champion_name=champion,
        team_position=role,
        win=win,
        kills=kills,
        deaths=deaths,
        assists=assists,
        cs=cs,
        gold_earned=12000,
    )


def _match(match_id: str, me: Participant, *, duration: int = 1800) -> Match:
    opponent = _participant(
        puuid="P_OPP",
        champion="Zed",
        win=not me.win,
        kills=2,
        deaths=5,
        assists=1,
    )
    opponent.match_id = match_id
    me.match_id = match_id
    m = Match(
        match_id=match_id,
        region="kr",
        queue_id=420,
        patch="14.10",
        game_start_at=datetime(2026, 5, 1, tzinfo=UTC),
        game_duration_sec=duration,
        winning_team=100 if me.win else 200,
    )
    m.participants = [me, opponent]
    return m


def test_aggregate_basic() -> None:
    matches = [
        _match("M1", _participant(champion="Ahri", win=True, kills=5, deaths=2, assists=8, cs=180)),
        _match(
            "M2", _participant(champion="Ahri", win=False, kills=2, deaths=5, assists=3, cs=160)
        ),
        _match("M3", _participant(champion="Zed", win=True, kills=8, deaths=4, assists=2, cs=200)),
    ]
    result = _aggregate("Faker", "KR1", "P_ME", matches)

    assert result.total_games == 3
    assert result.total_wins == 2
    assert result.win_rate == pytest.approx(2 / 3)

    by = {c.champion: c for c in result.by_champion}
    assert by["Ahri"].games == 2
    assert by["Ahri"].wins == 1
    assert by["Ahri"].win_rate == 0.5
    assert by["Ahri"].kda == pytest.approx((5 + 8 + 2 + 3) / (2 + 5))
    assert by["Zed"].games == 1
    assert by["Zed"].win_rate == 1.0


def test_aggregate_zero_deaths_kda() -> None:
    matches = [
        _match("M1", _participant(kills=10, deaths=0, assists=5)),
    ]
    result = _aggregate("Faker", "KR1", "P_ME", matches)
    assert result.by_champion[0].kda == 15.0


def test_aggregate_skips_match_when_puuid_missing() -> None:
    me_other = _participant(puuid="OTHER")
    matches = [_match("M1", me_other)]
    result = _aggregate("Faker", "KR1", "P_ME", matches)
    assert result.total_games == 0
    assert result.by_champion == []


def test_aggregate_sorting_prefers_more_games_then_winrate() -> None:
    matches = [
        _match("M1", _participant(champion="Aatrox", win=True)),
        _match("M2", _participant(champion="Aatrox", win=False)),
        _match("M3", _participant(champion="Zed", win=True)),
    ]
    result = _aggregate("F", "KR1", "P_ME", matches)
    # Aatrox played 2x, Zed 1x — Aatrox should sort first
    assert [c.champion for c in result.by_champion] == ["Aatrox", "Zed"]
