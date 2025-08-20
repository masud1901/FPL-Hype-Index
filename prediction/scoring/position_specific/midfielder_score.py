"""
Midfielder Scoring

This module contains position-specific scoring algorithms for midfielders.
"""

from typing import Dict, Any
import pandas as pd

from ..base.score_base import PositionSpecificScore
from utils.logger import get_logger

logger = get_logger("midfielder_score")


class MidfielderScore(PositionSpecificScore):
    """Position-specific scoring for midfielders"""

    description = "Midfielder scoring based on goals, assists, creativity, and defensive contribution"
    position = "MID"

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)

        # Component weights
        self.goal_threat_weight = config.get("goal_threat_weight", 0.3)
        self.creativity_weight = config.get("creativity_weight", 0.3)
        self.defensive_weight = config.get("defensive_weight", 0.2)
        self.bonus_weight = config.get("bonus_weight", 0.2)

        # Scoring thresholds
        self.goals_excellent = config.get("goals_excellent", 10)
        self.goals_good = config.get("goals_good", 5)
        self.assists_excellent = config.get("assists_excellent", 12)
        self.assists_good = config.get("assists_good", 6)

    def calculate_score(self, data: Dict[str, Any]) -> float:
        """Calculate midfielder-specific score"""

        # Extract midfielder stats
        goals_scored = data.get("goals_scored", 0)
        assists = data.get("assists", 0)
        creativity = data.get("creativity", 0.0)
        threat = data.get("threat", 0.0)
        influence = data.get("influence", 0.0)
        bonus = data.get("bonus", 0)
        played = data.get("played", 1)

        # Calculate component scores
        goal_threat_score = self._calculate_goal_threat_score(goals_scored, threat)
        creativity_score = self._calculate_creativity_score(assists, creativity)
        defensive_score = self._calculate_defensive_score(influence, played)
        bonus_score = self._calculate_bonus_score(bonus, played)

        # Weighted total score
        total_score = (
            goal_threat_score * self.goal_threat_weight
            + creativity_score * self.creativity_weight
            + defensive_score * self.defensive_weight
            + bonus_score * self.bonus_weight
        )

        return total_score

    def _calculate_goal_threat_score(self, goals_scored: int, threat: float) -> float:
        """Calculate goal threat score"""
        # Base score from actual goals
        if goals_scored >= self.goals_excellent:
            goals_score = 10.0
        elif goals_scored >= self.goals_good:
            ratio = (goals_scored - self.goals_good) / (
                self.goals_excellent - self.goals_good
            )
            goals_score = 7.0 + (ratio * 3.0)
        else:
            ratio = goals_scored / self.goals_good
            goals_score = min(7.0, ratio * 7.0)

        # Bonus from threat rating (future potential)
        threat_bonus = min(3.0, threat / 100.0)  # Up to 3 points bonus

        total_score = min(10.0, goals_score + threat_bonus)
        return total_score

    def _calculate_creativity_score(self, assists: int, creativity: float) -> float:
        """Calculate creativity score"""
        # Base score from actual assists
        if assists >= self.assists_excellent:
            assists_score = 10.0
        elif assists >= self.assists_good:
            ratio = (assists - self.assists_good) / (
                self.assists_excellent - self.assists_good
            )
            assists_score = 7.0 + (ratio * 3.0)
        else:
            ratio = assists / self.assists_good
            assists_score = min(7.0, ratio * 7.0)

        # Bonus from creativity rating
        creativity_bonus = min(3.0, creativity / 100.0)  # Up to 3 points bonus

        total_score = min(10.0, assists_score + creativity_bonus)
        return total_score

    def _calculate_defensive_score(self, influence: float, played: int) -> float:
        """Calculate defensive contribution score"""
        if played == 0:
            return 0.0

        # Use influence as proxy for overall contribution including defensive work
        influence_per_game = influence / played

        # Scale to 0-10 (typical midfielder influence: 0-200 per game)
        defensive_score = min(10.0, influence_per_game / 20.0)

        return defensive_score

    def _calculate_bonus_score(self, bonus: int, played: int) -> float:
        """Calculate bonus point score"""
        if played == 0:
            return 0.0

        bonus_per_game = bonus / played

        # Scale bonus per game to 0-10
        # 0.4 bonus per game = 10 score (excellent for midfielder)
        score = min(10.0, bonus_per_game * 25.0)

        return score


class MidfielderCreativityScore(PositionSpecificScore):
    """Creativity specific scoring for midfielders"""

    description = "Midfielder creativity based on assists and key passes"
    position = "MID"

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.assists_weight = config.get("assists_weight", 0.7)
        self.creativity_weight = config.get("creativity_weight", 0.3)

    def calculate_score(self, data: Dict[str, Any]) -> float:
        """Calculate creativity score"""
        assists = data.get("assists", 0)
        creativity = data.get("creativity", 0.0)
        played = data.get("played", 1)

        # Assists score
        assists_score = min(10.0, assists * 0.8)  # 12.5 assists = 10 score

        # Creativity rating score
        if played > 0:
            creativity_per_game = creativity / played
            creativity_score = min(
                10.0, creativity_per_game / 20.0
            )  # 200 creativity per game = 10 score
        else:
            creativity_score = 0.0

        # Combined score
        total_score = (
            assists_score * self.assists_weight
            + creativity_score * self.creativity_weight
        )

        return total_score


class MidfielderGoalThreatScore(PositionSpecificScore):
    """Goal threat specific scoring for midfielders"""

    description = "Midfielder goal threat based on goals and threat rating"
    position = "MID"

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.goals_weight = config.get("goals_weight", 0.8)
        self.threat_weight = config.get("threat_weight", 0.2)

    def calculate_score(self, data: Dict[str, Any]) -> float:
        """Calculate goal threat score"""
        goals_scored = data.get("goals_scored", 0)
        threat = data.get("threat", 0.0)
        played = data.get("played", 1)

        # Goals score
        goals_score = min(10.0, goals_scored * 1.0)  # 10 goals = 10 score

        # Threat rating score
        if played > 0:
            threat_per_game = threat / played
            threat_score = min(
                10.0, threat_per_game / 15.0
            )  # 150 threat per game = 10 score
        else:
            threat_score = 0.0

        # Combined score
        total_score = (
            goals_score * self.goals_weight + threat_score * self.threat_weight
        )

        return total_score


class MidfielderVersatilityScore(PositionSpecificScore):
    """Versatility scoring for midfielders"""

    description = (
        "Midfielder versatility based on balanced contribution across all areas"
    )
    position = "MID"

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.balance_bonus = config.get("balance_bonus", 2.0)

    def calculate_score(self, data: Dict[str, Any]) -> float:
        """Calculate versatility score"""
        goals_scored = data.get("goals_scored", 0)
        assists = data.get("assists", 0)
        influence = data.get("influence", 0.0)
        creativity = data.get("creativity", 0.0)
        threat = data.get("threat", 0.0)
        played = data.get("played", 1)

        if played == 0:
            return 0.0

        # Normalize each component to per-game basis
        goals_per_game = goals_scored / played
        assists_per_game = assists / played
        influence_per_game = influence / played
        creativity_per_game = creativity / played
        threat_per_game = threat / played

        # Score each component (0-2.5 scale for balance)
        goals_component = min(2.5, goals_per_game * 5.0)  # 0.5 goals/game = 2.5
        assists_component = min(2.5, assists_per_game * 4.0)  # 0.625 assists/game = 2.5
        influence_component = min(
            2.5, influence_per_game / 40.0
        )  # 100 influence/game = 2.5
        creativity_component = min(
            2.5, creativity_per_game / 40.0
        )  # 100 creativity/game = 2.5
        threat_component = min(2.5, threat_per_game / 40.0)  # 100 threat/game = 2.5

        # Base score from all components
        components = [
            goals_component,
            assists_component,
            influence_component,
            creativity_component,
            threat_component,
        ]
        base_score = sum(components)

        # Balance bonus: reward players who contribute across multiple areas
        non_zero_components = sum(1 for c in components if c > 0.5)
        if non_zero_components >= 4:
            balance_bonus = self.balance_bonus
        elif non_zero_components >= 3:
            balance_bonus = self.balance_bonus * 0.5
        else:
            balance_bonus = 0.0

        total_score = min(10.0, base_score + balance_bonus)
        return total_score
