from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    SmallInteger,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from lol_coach.db.base import Base


class Patch(Base):
    __tablename__ = "patches"

    version: Mapped[str] = mapped_column(String(16), primary_key=True)
    major: Mapped[int] = mapped_column(Integer, nullable=False)
    minor: Mapped[int] = mapped_column(Integer, nullable=False)
    is_current: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


class Champion(Base):
    __tablename__ = "champions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    key: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str | None] = mapped_column(String(128), nullable=True)
    tags: Mapped[str | None] = mapped_column(String(128), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class Summoner(Base):
    __tablename__ = "summoners"

    puuid: Mapped[str] = mapped_column(String(78), primary_key=True)
    region: Mapped[str] = mapped_column(String(8), nullable=False)
    game_name: Mapped[str | None] = mapped_column(String(64), nullable=True)
    tag_line: Mapped[str | None] = mapped_column(String(16), nullable=True)
    current_tier: Mapped[str | None] = mapped_column(String(16), nullable=True)
    current_rank: Mapped[str | None] = mapped_column(String(8), nullable=True)
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (Index("idx_summoners_region_tier", "region", "current_tier"),)


class Match(Base):
    __tablename__ = "matches"

    match_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    region: Mapped[str] = mapped_column(String(8), nullable=False)
    queue_id: Mapped[int] = mapped_column(Integer, nullable=False)
    patch: Mapped[str] = mapped_column(String(16), ForeignKey("patches.version"), nullable=False)
    game_start_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    game_duration_sec: Mapped[int] = mapped_column(Integer, nullable=False)
    winning_team: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    ingested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    participants: Mapped[list[Participant]] = relationship(
        back_populates="match", cascade="all, delete-orphan", lazy="selectin"
    )

    __table_args__ = (
        Index("idx_matches_patch_queue", "patch", "queue_id"),
        Index("idx_matches_game_start", "game_start_at"),
    )


class Participant(Base):
    __tablename__ = "participants"

    match_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("matches.match_id", ondelete="CASCADE"), primary_key=True
    )
    puuid: Mapped[str] = mapped_column(String(78), primary_key=True)
    team_id: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    champion_id: Mapped[int] = mapped_column(Integer, ForeignKey("champions.id"), nullable=False)
    champion_name: Mapped[str] = mapped_column(String(64), nullable=False)
    team_position: Mapped[str | None] = mapped_column(String(8), nullable=True)
    win: Mapped[bool] = mapped_column(Boolean, nullable=False)
    kills: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    deaths: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    assists: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    cs: Mapped[int] = mapped_column(Integer, nullable=False)
    gold_earned: Mapped[int] = mapped_column(Integer, nullable=False)

    match: Mapped[Match] = relationship(back_populates="participants")

    __table_args__ = (
        Index("idx_participants_puuid", "puuid"),
        Index("idx_participants_champion", "champion_id"),
    )


class ChampionMatchupAgg(Base):
    __tablename__ = "champion_matchups_agg"

    champion_a: Mapped[int] = mapped_column(Integer, ForeignKey("champions.id"), primary_key=True)
    champion_b: Mapped[int] = mapped_column(Integer, ForeignKey("champions.id"), primary_key=True)
    role: Mapped[str] = mapped_column(String(8), primary_key=True)
    patch: Mapped[str] = mapped_column(String(16), ForeignKey("patches.version"), primary_key=True)
    tier_band: Mapped[str] = mapped_column(String(16), primary_key=True)
    games: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    wins_a: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (CheckConstraint("champion_a < champion_b", name="ck_matchup_ordered"),)


class ChampionSynergyAgg(Base):
    __tablename__ = "champion_synergy_agg"

    champion_a: Mapped[int] = mapped_column(Integer, ForeignKey("champions.id"), primary_key=True)
    champion_b: Mapped[int] = mapped_column(Integer, ForeignKey("champions.id"), primary_key=True)
    patch: Mapped[str] = mapped_column(String(16), ForeignKey("patches.version"), primary_key=True)
    tier_band: Mapped[str] = mapped_column(String(16), primary_key=True)
    games: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    wins: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (CheckConstraint("champion_a < champion_b", name="ck_synergy_ordered"),)


class IngestionJob(Base):
    __tablename__ = "ingestion_jobs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    job_type: Mapped[str] = mapped_column(String(32), nullable=False)
    payload: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="pending")
    error: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
