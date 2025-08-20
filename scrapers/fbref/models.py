"""
Data models for FBRef scraper.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class FBRefPlayer(BaseModel):
    """FBRef player data model."""

    id: str
    name: str
    team: str
    position: Optional[str] = None
    nationality: Optional[str] = None
    age: Optional[int] = None
    height: Optional[str] = None
    weight: Optional[str] = None
    season: str
    league: str = "Premier League"

    # Performance stats
    games: int = 0
    games_started: int = 0
    minutes: int = 0
    goals: int = 0
    assists: int = 0
    goals_per_90: float = 0.0
    assists_per_90: float = 0.0
    goals_assists_per_90: float = 0.0
    goals_pens: int = 0
    pens_att: int = 0
    cards_yellow: int = 0
    cards_red: int = 0
    xg: float = 0.0
    npxg: float = 0.0
    xa: float = 0.0
    npxg_xa: float = 0.0

    # Shooting stats
    shots: int = 0
    shots_on_target: int = 0
    shots_on_target_pct: float = 0.0
    shots_per_90: float = 0.0
    shots_on_target_per_90: float = 0.0
    goals_per_shot: float = 0.0
    goals_per_shot_on_target: float = 0.0

    # Passing stats
    passes: int = 0
    passes_completed: int = 0
    passes_pct: float = 0.0
    passes_total_distance: int = 0
    passes_progressive_distance: int = 0
    passes_completed_short: int = 0
    passes_short: int = 0
    passes_pct_short: float = 0.0
    passes_completed_medium: int = 0
    passes_medium: int = 0
    passes_pct_medium: float = 0.0
    passes_completed_long: int = 0
    passes_long: int = 0
    passes_pct_long: float = 0.0
    assists: int = 0
    xa: float = 0.0
    xa_net: float = 0.0
    assisted_shots: int = 0
    passes_into_final_third: int = 0
    passes_into_penalty_area: int = 0
    crosses_into_penalty_area: int = 0

    # Defensive stats
    tackles: int = 0
    tackles_won: int = 0
    tackles_def_3rd: int = 0
    tackles_mid_3rd: int = 0
    tackles_att_3rd: int = 0
    dribble_tackles: int = 0
    dribbles_vs: int = 0
    dribble_tackle_pct: float = 0.0
    dribbled_past: int = 0
    blocks: int = 0
    blocked_shots: int = 0
    blocked_passes: int = 0
    interceptions: int = 0
    tackles_interceptions: int = 0
    clearances: int = 0
    errors: int = 0

    # Possession stats
    touches: int = 0
    touches_def_pen_area: int = 0
    touches_def_3rd: int = 0
    touches_mid_3rd: int = 0
    touches_att_3rd: int = 0
    touches_att_pen_area: int = 0
    touches_live_ball: int = 0
    dribbles_completed: int = 0
    dribbles: int = 0
    dribble_pct: float = 0.0
    dribbles_completed_distance: int = 0
    dribbles_progressive_distance: int = 0
    carries: int = 0
    carry_distance: int = 0
    carry_progressive_distance: int = 0
    carry_into_final_third: int = 0
    carry_into_penalty_area: int = 0
    miscontrols: int = 0
    dispossessed: int = 0
    passes_received: int = 0
    progressive_passes_received: int = 0

    class Config:
        extra = "allow"


class FBRefTeam(BaseModel):
    """FBRef team data model."""

    id: str
    name: str
    short_name: str
    season: str
    league: str = "Premier League"

    # Team stats
    games: int = 0
    wins: int = 0
    draws: int = 0
    losses: int = 0
    goals_for: int = 0
    goals_against: int = 0
    goal_difference: int = 0
    points: int = 0
    points_per_game: float = 0.0

    class Config:
        extra = "allow"


class FBRefMatch(BaseModel):
    """FBRef match data model."""

    id: str
    date: datetime
    home_team: str
    away_team: str
    home_score: int
    away_score: int
    home_xg: float = 0.0
    away_xg: float = 0.0
    season: str
    league: str = "Premier League"

    class Config:
        extra = "allow"


class FBRefPlayerStats(BaseModel):
    """FBRef player statistics for a specific season."""

    player_id: str
    player_name: str
    team: str
    season: str
    league: str = "Premier League"

    # Core stats
    games: int = 0
    minutes: int = 0
    goals: int = 0
    assists: int = 0
    xg: float = 0.0
    xa: float = 0.0
    npxg: float = 0.0
    npxg_xa: float = 0.0

    # Advanced stats
    goals_per_90: float = 0.0
    assists_per_90: float = 0.0
    goals_assists_per_90: float = 0.0
    xg_per_90: float = 0.0
    xa_per_90: float = 0.0
    npxg_per_90: float = 0.0
    npxg_xa_per_90: float = 0.0

    class Config:
        extra = "allow"


class FBRefScrapedData(BaseModel):
    """Complete FBRef scraped data model."""

    players: List[FBRefPlayer]
    teams: List[FBRefTeam]
    matches: List[FBRefMatch]
    player_stats: List[FBRefPlayerStats]
    scraped_at: datetime
    source: str = "fbref"
    season: str
    league: str = "Premier League"

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}
