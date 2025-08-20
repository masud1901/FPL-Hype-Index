"""
SQLAlchemy models for the FPL Data Collection System.
"""

from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    DateTime,
    Boolean,
    Text,
    ForeignKey,
    Index,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

Base = declarative_base()


class Team(Base):
    """Team model representing Premier League teams."""

    __tablename__ = "teams"

    id = Column(Integer, primary_key=True)
    fpl_id = Column(Integer, unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False, index=True)
    short_name = Column(String(10), nullable=False, index=True)
    code = Column(Integer, nullable=False)

    # Team strength and performance
    strength = Column(Integer, default=0)  # FPL team strength
    strength_overall_home = Column(Integer, default=0)
    strength_overall_away = Column(Integer, default=0)
    strength_attack_home = Column(Integer, default=0)
    strength_attack_away = Column(Integer, default=0)
    strength_defence_home = Column(Integer, default=0)
    strength_defence_away = Column(Integer, default=0)

    # Current season stats
    played = Column(Integer, default=0)
    win = Column(Integer, default=0)
    loss = Column(Integer, default=0)
    draw = Column(Integer, default=0)
    points = Column(Integer, default=0)
    position = Column(Integer, default=0)  # League position

    # Goals
    goals_for = Column(Integer, default=0)
    goals_against = Column(Integer, default=0)
    goal_difference = Column(Integer, default=0)

    # Advanced metrics
    xg_for = Column(Float, default=0.0)  # Expected goals for
    xg_against = Column(Float, default=0.0)  # Expected goals against
    xg_difference = Column(Float, default=0.0)

    # Form and momentum
    form = Column(String(10), default="")  # Recent form string (WWDLL)
    unbeaten = Column(Integer, default=0)  # Games unbeaten
    winless = Column(Integer, default=0)  # Games without win

    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    players = relationship("Player", back_populates="team_obj")
    home_fixtures = relationship(
        "Fixture", foreign_keys="Fixture.team_h_id", back_populates="home_team"
    )
    away_fixtures = relationship(
        "Fixture", foreign_keys="Fixture.team_a_id", back_populates="away_team"
    )


class Fixture(Base):
    """Fixture model for Premier League matches."""

    __tablename__ = "fixtures"

    id = Column(Integer, primary_key=True, index=True)
    fpl_id = Column(Integer, unique=True, nullable=False, index=True)
    event = Column(Integer, nullable=False, index=True)  # Gameweek number
    team_h_id = Column(Integer, ForeignKey("teams.id"), nullable=False, index=True)
    team_a_id = Column(Integer, ForeignKey("teams.id"), nullable=False, index=True)
    team_h_score = Column(Integer, nullable=True)
    team_a_score = Column(Integer, nullable=True)
    finished = Column(Boolean, default=False, index=True)
    kickoff_time = Column(DateTime, nullable=False, index=True)
    difficulty = Column(Integer, nullable=True)
    team_h_difficulty = Column(Integer, nullable=True)
    team_a_difficulty = Column(Integer, nullable=True)
    started = Column(Boolean, default=False)
    finished_provisional = Column(Boolean, default=False)
    minutes = Column(Integer, default=0)
    provisional_start_time = Column(Boolean, default=False)
    pulse_id = Column(Integer, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    home_team = relationship(
        "Team", foreign_keys=[team_h_id], back_populates="home_fixtures"
    )
    away_team = relationship(
        "Team", foreign_keys=[team_a_id], back_populates="away_fixtures"
    )

    def __repr__(self):
        return (
            f"<Team(id={self.id}, name='{self.name}', short_name='{self.short_name}')>"
        )


class Player(Base):
    """Player model representing FPL players."""

    __tablename__ = "players"

    id = Column(Integer, primary_key=True)
    fpl_id = Column(Integer, unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False, index=True)
    team = Column(String(100), nullable=False, index=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=True, index=True)
    position = Column(String(10), nullable=False)  # GK, DEF, MID, FWD
    price = Column(Float, nullable=False)
    form = Column(Float, default=0.0)
    total_points = Column(Integer, default=0)
    selected_by_percent = Column(Float, default=0.0)
    transfers_in = Column(Integer, default=0)
    transfers_out = Column(Integer, default=0)
    goals_scored = Column(Integer, default=0)
    assists = Column(Integer, default=0)
    clean_sheets = Column(Integer, default=0)
    goals_conceded = Column(Integer, default=0)
    own_goals = Column(Integer, default=0)
    penalties_saved = Column(Integer, default=0)
    penalties_missed = Column(Integer, default=0)
    yellow_cards = Column(Integer, default=0)
    red_cards = Column(Integer, default=0)
    saves = Column(Integer, default=0)
    bonus = Column(Integer, default=0)
    bps = Column(Integer, default=0)
    influence = Column(Float, default=0.0)
    creativity = Column(Float, default=0.0)
    threat = Column(Float, default=0.0)
    ict_index = Column(Float, default=0.0)

    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    team_obj = relationship("Team", back_populates="players")
    stats = relationship(
        "PlayerStats", back_populates="player", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Player(id={self.id}, name='{self.name}', team='{self.team}', position='{self.position}')>"


class PlayerStats(Base):
    """Player statistics model for gameweek-specific data."""

    __tablename__ = "player_stats"

    id = Column(Integer, primary_key=True)
    player_id = Column(Integer, ForeignKey("players.id"), nullable=False, index=True)
    gameweek = Column(Integer, nullable=False)

    # Basic stats
    goals = Column(Integer, default=0)
    assists = Column(Integer, default=0)
    minutes = Column(Integer, default=0)
    bonus = Column(Integer, default=0)
    bps = Column(Integer, default=0)

    # Advanced stats (from other sources)
    xg = Column(Float, default=0.0)  # Expected goals
    xa = Column(Float, default=0.0)  # Expected assists
    xgi = Column(Float, default=0.0)  # Expected goal involvements
    xgc = Column(Float, default=0.0)  # Expected goals conceded
    xcs = Column(Float, default=0.0)  # Expected clean sheets

    # Performance metrics
    influence = Column(Float, default=0.0)
    creativity = Column(Float, default=0.0)
    threat = Column(Float, default=0.0)
    ict_index = Column(Float, default=0.0)

    # Source tracking
    source = Column(
        String(50), nullable=False, index=True
    )  # fpl_api, understat, fbref, etc.

    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    player = relationship("Player", back_populates="stats")

    # Indexes for efficient querying
    __table_args__ = (
        Index("idx_player_gameweek_source", "player_id", "gameweek", "source"),
        Index("idx_gameweek_source", "gameweek", "source"),
    )

    def __repr__(self):
        return f"<PlayerStats(player_id={self.player_id}, gameweek={self.gameweek}, source='{self.source}')>"


class DataQualityLog(Base):
    """Model for tracking data quality issues and validation results."""

    __tablename__ = "data_quality_log"

    id = Column(Integer, primary_key=True)
    source = Column(String(50), nullable=False, index=True)
    data_type = Column(String(50), nullable=False)  # player, stats, fixture, etc.
    quality_score = Column(Float, nullable=False)  # 0.0 to 1.0
    issues = Column(Text)  # JSON string of issues found
    record_count = Column(Integer, default=0)
    valid_count = Column(Integer, default=0)
    invalid_count = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)

    def __repr__(self):
        return f"<DataQualityLog(source='{self.source}', data_type='{self.data_type}', quality_score={self.quality_score})>"


class ScraperRunLog(Base):
    """Model for tracking scraper execution history."""

    __tablename__ = "scraper_run_log"

    id = Column(Integer, primary_key=True)
    scraper_name = Column(String(50), nullable=False, index=True)
    status = Column(String(20), nullable=False)  # success, failed, partial
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime)
    duration_seconds = Column(Float)
    records_processed = Column(Integer, default=0)
    records_saved = Column(Integer, default=0)
    error_message = Column(Text)

    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)

    def __repr__(self):
        return f"<ScraperRunLog(scraper_name='{self.scraper_name}', status='{self.status}', duration={self.duration_seconds}s)>"
