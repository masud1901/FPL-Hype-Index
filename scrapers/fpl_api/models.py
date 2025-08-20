"""
Pydantic models for FPL API data structures.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class FPLPlayer(BaseModel):
    """FPL API player model."""

    id: int = Field(..., description="FPL player ID")
    first_name: str = Field(..., description="Player's first name")
    second_name: str = Field(..., description="Player's last name")
    web_name: str = Field(..., description="Player's web name")
    team: int = Field(..., description="Team ID")
    element_type: int = Field(
        ..., description="Position ID (1=GK, 2=DEF, 3=MID, 4=FWD)"
    )
    now_cost: int = Field(..., description="Current price in tenths")
    selected_by_percent: str = Field(..., description="Percentage selected by managers")
    form: str = Field(..., description="Form points")
    total_points: int = Field(..., description="Total points")
    goals_scored: int = Field(..., description="Goals scored")
    assists: int = Field(..., description="Assists")
    clean_sheets: int = Field(..., description="Clean sheets")
    goals_conceded: int = Field(..., description="Goals conceded")
    own_goals: int = Field(..., description="Own goals")
    penalties_saved: int = Field(..., description="Penalties saved")
    penalties_missed: int = Field(..., description="Penalties missed")
    yellow_cards: int = Field(..., description="Yellow cards")
    red_cards: int = Field(..., description="Red cards")
    saves: int = Field(..., description="Saves")
    bonus: int = Field(..., description="Bonus points")
    bps: int = Field(..., description="BPS points")
    influence: str = Field(..., description="Influence rating")
    creativity: str = Field(..., description="Creativity rating")
    threat: str = Field(..., description="Threat rating")
    ict_index: str = Field(..., description="ICT index")
    transfers_in: int = Field(..., description="Transfers in")
    transfers_out: int = Field(..., description="Transfers out")

    @property
    def full_name(self) -> str:
        """Get player's full name."""
        return f"{self.first_name} {self.second_name}"

    @property
    def price(self) -> float:
        """Get player's price in pounds."""
        return self.now_cost / 10.0

    @property
    def position(self) -> str:
        """Get player's position as string."""
        positions = {1: "GK", 2: "DEF", 3: "MID", 4: "FWD"}
        return positions.get(self.element_type, "UNK")


class FPLTeam(BaseModel):
    """FPL API team model."""

    id: int = Field(..., description="Team ID")
    name: str = Field(..., description="Team name")
    short_name: str = Field(..., description="Team short name")
    code: int = Field(..., description="Team code")


class FPLGameweek(BaseModel):
    """FPL API gameweek model."""

    id: int = Field(..., description="Gameweek ID")
    name: str = Field(..., description="Gameweek name")
    deadline_time: datetime = Field(..., description="Deadline time")
    average_entry_score: Optional[int] = Field(None, description="Average entry score")
    finished: bool = Field(..., description="Whether gameweek is finished")
    data_checked: bool = Field(..., description="Whether data is checked")
    highest_scoring_entry: Optional[int] = Field(
        None, description="Highest scoring entry"
    )
    is_previous: bool = Field(..., description="Whether this is the previous gameweek")
    is_current: bool = Field(..., description="Whether this is the current gameweek")
    is_next: bool = Field(..., description="Whether this is the next gameweek")


class FPLFixture(BaseModel):
    """FPL API fixture model."""

    id: int = Field(..., description="Fixture ID")
    event: int = Field(..., description="Gameweek number")
    team_h: int = Field(..., description="Home team ID")
    team_a: int = Field(..., description="Away team ID")
    team_h_score: Optional[int] = Field(None, description="Home team score")
    team_a_score: Optional[int] = Field(None, description="Away team score")
    finished: bool = Field(..., description="Whether fixture is finished")
    kickoff_time: datetime = Field(..., description="Kickoff time")
    difficulty: Optional[int] = Field(None, description="Fixture difficulty")
    team_h_difficulty: Optional[int] = Field(None, description="Home team difficulty")
    team_a_difficulty: Optional[int] = Field(None, description="Away team difficulty")
    started: bool = Field(..., description="Whether fixture has started")
    finished_provisional: bool = Field(
        ..., description="Whether fixture is provisionally finished"
    )
    minutes: int = Field(..., description="Minutes played")
    provisional_start_time: bool = Field(
        ..., description="Whether start time is provisional"
    )
    pulse_id: int = Field(..., description="Pulse ID")


class FPLBootstrapData(BaseModel):
    """FPL API bootstrap data model."""

    events: List[FPLGameweek] = Field(..., description="Gameweek events")
    teams: List[FPLTeam] = Field(..., description="Teams")
    total_players: int = Field(..., description="Total players")
    game_settings: Dict[str, Any] = Field(..., description="Game settings")
    phases: List[Dict[str, Any]] = Field(..., description="Phases")
    element_stats: List[Dict[str, Any]] = Field(..., description="Element stats")
    element_types: List[Dict[str, Any]] = Field(..., description="Element types")


class FPLScrapedData(BaseModel):
    """Standardized FPL scraped data model."""

    players: List[FPLPlayer] = Field(..., description="Players data")
    teams: List[FPLTeam] = Field(..., description="Teams data")
    gameweeks: List[FPLGameweek] = Field(..., description="Gameweeks data")
    fixtures: List[FPLFixture] = Field(..., description="Fixtures data")
    scraped_at: datetime = Field(
        default_factory=datetime.utcnow, description="When data was scraped"
    )
    source: str = Field(default="fpl_api", description="Data source")
