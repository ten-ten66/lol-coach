"""Pydantic models for Riot API responses.

Only the fields we actually consume are declared. `model_config` allows extra
fields so Riot adding new keys doesn't break parsing.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class _RiotModel(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)


class RiotAccount(_RiotModel):
    puuid: str
    game_name: str = Field(alias="gameName")
    tag_line: str = Field(alias="tagLine")


class MatchMetadata(_RiotModel):
    match_id: str = Field(alias="matchId")
    participants: list[str]  # list of puuids


class MatchParticipant(_RiotModel):
    puuid: str
    summoner_name: str = Field(alias="summonerName", default="")
    riot_id_game_name: str = Field(alias="riotIdGameName", default="")
    riot_id_tagline: str = Field(alias="riotIdTagline", default="")
    champion_id: int = Field(alias="championId")
    champion_name: str = Field(alias="championName")
    team_id: int = Field(alias="teamId")
    team_position: str = Field(alias="teamPosition", default="")
    win: bool
    kills: int
    deaths: int
    assists: int
    total_minions_killed: int = Field(alias="totalMinionsKilled", default=0)
    neutral_minions_killed: int = Field(alias="neutralMinionsKilled", default=0)
    gold_earned: int = Field(alias="goldEarned", default=0)


class MatchInfo(_RiotModel):
    game_version: str = Field(alias="gameVersion")
    game_creation: int = Field(alias="gameCreation")  # ms epoch
    game_duration: int = Field(alias="gameDuration")  # seconds (sometimes ms; see API notes)
    game_start_timestamp: int = Field(alias="gameStartTimestamp", default=0)
    queue_id: int = Field(alias="queueId")
    map_id: int = Field(alias="mapId", default=0)
    participants: list[MatchParticipant]


class Match(_RiotModel):
    metadata: MatchMetadata
    info: MatchInfo
