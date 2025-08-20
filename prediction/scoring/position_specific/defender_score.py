"""
Defender Scoring

This module contains position-specific scoring algorithms for defenders.
"""

from typing import Dict, Any
import pandas as pd

from ..base.score_base import PositionSpecificScore
from utils.logger import get_logger

logger = get_logger("defender_score")


class DefenderScore(PositionSpecificScore):
    """Position-specific scoring for defenders"""

    description = "Defender scoring based on clean sheets, attacking returns, and defensive actions"
    position = "DEF"

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)

        # Component weights
        self.clean_sheet_weight = config.get("clean_sheet_weight", 0.4)
        self.attacking_weight = config.get("attacking_weight", 0.3)
        self.defensive_weight = config.get("defensive_weight", 0.2)
        self.bonus_weight = config.get("bonus_weight", 0.1)

        # Scoring thresholds
        self.clean_sheets_excellent = config.get("clean_sheets_excellent", 12)
        self.clean_sheets_good = config.get("clean_sheets_good", 8)
        self.goals_excellent = config.get("goals_excellent", 5)
        self.assists_excellent = config.get("assists_excellent", 8)

    def calculate_score(self, data: Dict[str, Any]) -> float:
        """Calculate defender-specific score"""

        # Extract defender stats
        clean_sheets = data.get("clean_sheets", 0)
        goals_scored = data.get("goals_scored", 0)
        assists = data.get("assists", 0)
        goals_conceded = data.get("goals_conceded", 0)
        bonus = data.get("bonus", 0)
        influence = data.get("influence", 0.0)
        played = data.get("played", 1)

        # Calculate component scores
        clean_sheet_score = self._calculate_clean_sheet_score(
            clean_sheets, goals_conceded, played
        )
        attacking_score = self._calculate_attacking_score(goals_scored, assists)
        defensive_score = self._calculate_defensive_score(influence, played)
        bonus_score = self._calculate_bonus_score(bonus, played)

        # Weighted total score
        total_score = (
            clean_sheet_score * self.clean_sheet_weight
            + attacking_score * self.attacking_weight
            + defensive_score * self.defensive_weight
            + bonus_score * self.bonus_weight
        )

        return total_score

    def _calculate_clean_sheet_score(
        self, clean_sheets: int, goals_conceded: int, played: int
    ) -> float:
        """Calculate clean sheet performance score"""
        if played == 0:
            return 0.0

        # Base score from clean sheets
        if clean_sheets >= self.clean_sheets_excellent:
            base_score = 10.0
        elif clean_sheets >= self.clean_sheets_good:
            # Linear interpolation
            ratio = (clean_sheets - self.clean_sheets_good) / (
                self.clean_sheets_excellent - self.clean_sheets_good
            )
            base_score = 7.0 + (ratio * 3.0)
        else:
            # Linear scaling
            ratio = clean_sheets / self.clean_sheets_good
            base_score = min(7.0, ratio * 7.0)

        # Adjustment based on goals conceded rate
        goals_per_game = goals_conceded / played
        if goals_per_game > 1.5:
            penalty = (goals_per_game - 1.5) * 2.0
            base_score = max(0.0, base_score - penalty)
        elif goals_per_game < 0.8:
            bonus = (0.8 - goals_per_game) * 2.0
            base_score = min(10.0, base_score + bonus)

        return base_score

    def _calculate_attacking_score(self, goals_scored: int, assists: int) -> float:
        """Calculate attacking returns score"""
        # Goals are worth more than assists for defenders
        attacking_points = (goals_scored * 2.0) + assists

        # Scale to 0-10
        if attacking_points >= 10:  # Excellent attacking returns
            return 10.0
        elif attacking_points >= 6:  # Good attacking returns
            ratio = (attacking_points - 6) / 4
            return 7.0 + (ratio * 3.0)
        else:
            # Linear scaling
            ratio = attacking_points / 6
            return min(7.0, ratio * 7.0)

    def _calculate_defensive_score(self, influence: float, played: int) -> float:
        """Calculate defensive actions score based on influence"""
        if played == 0:
            return 0.0

        # Normalize influence per game
        influence_per_game = influence / played

        # Scale influence to 0-10 (typical defender influence: 0-150 per game)
        normalized_score = min(10.0, influence_per_game / 15.0)

        return normalized_score

    def _calculate_bonus_score(self, bonus: int, played: int) -> float:
        """Calculate bonus point score"""
        if played == 0:
            return 0.0

        bonus_per_game = bonus / played

        # Scale bonus per game to 0-10
        # 0.5 bonus per game = 10 score (excellent for defender)
        score = min(10.0, bonus_per_game * 20.0)

        return score


class DefenderAttackingThreatScore(PositionSpecificScore):
    """Attacking threat specific scoring for defenders"""

    description = "Defender attacking threat based on goals and assists potential"
    position = "DEF"

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.goal_weight = config.get("goal_weight", 0.6)
        self.assist_weight = config.get("assist_weight", 0.4)

    def calculate_score(self, data: Dict[str, Any]) -> float:
        """Calculate attacking threat score"""
        goals_scored = data.get("goals_scored", 0)
        assists = data.get("assists", 0)
        threat = data.get("threat", 0.0)
        played = data.get("played", 1)

        # Base score from actual returns
        goals_score = min(10.0, goals_scored * 2.0)  # 5 goals = 10 score
        assists_score = min(10.0, assists * 1.25)  # 8 assists = 10 score

        base_score = (goals_score * self.goal_weight) + (
            assists_score * self.assist_weight
        )

        # Bonus from threat rating (future potential)
        if played > 0:
            threat_per_game = threat / played
            threat_bonus = min(2.0, threat_per_game / 50.0)  # Up to 2 points bonus
            base_score += threat_bonus

        return min(10.0, base_score)


class DefenderCleanSheetPotentialScore(PositionSpecificScore):
    """Clean sheet potential scoring for defenders"""

    description = "Defender clean sheet potential based on team defense"
    position = "DEF"

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.team_defense_weight = config.get("team_defense_weight", 0.7)
        self.individual_weight = config.get("individual_weight", 0.3)

    def calculate_score(self, data: Dict[str, Any]) -> float:
        """Calculate clean sheet potential score"""
        clean_sheets = data.get("clean_sheets", 0)
        goals_conceded = data.get("goals_conceded", 0)
        team_strength = data.get("team_strength", 50.0)
        played = data.get("played", 1)

        # Individual clean sheet rate
        if played > 0:
            cs_rate = clean_sheets / played
            individual_score = min(10.0, cs_rate * 20.0)  # 50% CS rate = 10 score
        else:
            individual_score = 0.0

        # Team defensive strength
        team_defense_score = min(10.0, team_strength / 10.0)

        # Combined score
        potential_score = (
            individual_score * self.individual_weight
            + team_defense_score * self.team_defense_weight
        )

        return potential_score
