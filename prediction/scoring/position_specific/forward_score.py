"""
Forward Scoring

This module contains position-specific scoring algorithms for forwards.
"""

from typing import Dict, Any
import pandas as pd

from ..base.score_base import PositionSpecificScore
from utils.logger import get_logger

logger = get_logger("forward_score")


class ForwardScore(PositionSpecificScore):
    """Position-specific scoring for forwards"""

    description = "Forward scoring based on goals, assists, threat, and bonus potential"
    position = "FWD"

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)

        # Component weights
        self.finishing_weight = config.get("finishing_weight", 0.4)
        self.goal_threat_weight = config.get("goal_threat_weight", 0.3)
        self.assist_weight = config.get("assist_weight", 0.2)
        self.bonus_weight = config.get("bonus_weight", 0.1)

        # Scoring thresholds
        self.goals_excellent = config.get("goals_excellent", 20)
        self.goals_good = config.get("goals_good", 12)
        self.assists_excellent = config.get("assists_excellent", 10)
        self.assists_good = config.get("assists_good", 5)

    def calculate_score(self, data: Dict[str, Any]) -> float:
        """Calculate forward-specific score"""

        # Extract forward stats
        goals_scored = data.get("goals_scored", 0)
        assists = data.get("assists", 0)
        threat = data.get("threat", 0.0)
        bonus = data.get("bonus", 0)
        played = data.get("played", 1)

        # Calculate component scores
        finishing_score = self._calculate_finishing_score(goals_scored)
        goal_threat_score = self._calculate_goal_threat_score(threat, played)
        assist_score = self._calculate_assist_score(assists)
        bonus_score = self._calculate_bonus_score(bonus, played)

        # Weighted total score
        total_score = (
            finishing_score * self.finishing_weight
            + goal_threat_score * self.goal_threat_weight
            + assist_score * self.assist_weight
            + bonus_score * self.bonus_weight
        )

        return total_score

    def _calculate_finishing_score(self, goals_scored: int) -> float:
        """Calculate finishing ability score based on goals"""
        if goals_scored >= self.goals_excellent:
            return 10.0
        elif goals_scored >= self.goals_good:
            # Linear interpolation between good and excellent
            ratio = (goals_scored - self.goals_good) / (
                self.goals_excellent - self.goals_good
            )
            return 7.0 + (ratio * 3.0)
        else:
            # Linear scaling from 0 to 7
            ratio = goals_scored / self.goals_good
            return min(7.0, ratio * 7.0)

    def _calculate_goal_threat_score(self, threat: float, played: int) -> float:
        """Calculate goal threat score based on threat rating"""
        if played == 0:
            return 0.0

        threat_per_game = threat / played

        # Scale threat to 0-10 (typical forward threat: 0-300 per game)
        # 200 threat per game = 10 score
        threat_score = min(10.0, threat_per_game / 20.0)

        return threat_score

    def _calculate_assist_score(self, assists: int) -> float:
        """Calculate assist potential score"""
        if assists >= self.assists_excellent:
            return 10.0
        elif assists >= self.assists_good:
            # Linear interpolation
            ratio = (assists - self.assists_good) / (
                self.assists_excellent - self.assists_good
            )
            return 7.0 + (ratio * 3.0)
        else:
            # Linear scaling
            ratio = assists / self.assists_good
            return min(7.0, ratio * 7.0)

    def _calculate_bonus_score(self, bonus: int, played: int) -> float:
        """Calculate bonus point potential score"""
        if played == 0:
            return 0.0

        bonus_per_game = bonus / played

        # Scale bonus per game to 0-10
        # 0.3 bonus per game = 10 score (excellent for forward)
        score = min(10.0, bonus_per_game * 33.3)

        return score


class ForwardFinishingScore(PositionSpecificScore):
    """Finishing specific scoring for forwards"""

    description = "Forward finishing ability based on goals and conversion rate"
    position = "FWD"

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.goals_weight = config.get("goals_weight", 0.8)
        self.efficiency_weight = config.get("efficiency_weight", 0.2)

    def calculate_score(self, data: Dict[str, Any]) -> float:
        """Calculate finishing score"""
        goals_scored = data.get("goals_scored", 0)
        threat = data.get("threat", 0.0)
        played = data.get("played", 1)

        # Goals score (primary component)
        goals_score = min(10.0, goals_scored * 0.5)  # 20 goals = 10 score

        # Efficiency score (goals relative to threat/chances)
        if threat > 0 and played > 0:
            threat_per_game = threat / played
            goals_per_game = goals_scored / played

            # If threat is high but goals are low, efficiency is poor
            # If goals are high relative to threat, efficiency is good
            if threat_per_game > 0:
                efficiency_ratio = (goals_per_game * 100) / threat_per_game
                efficiency_score = min(
                    10.0, efficiency_ratio * 2.0
                )  # 5% conversion = 10 score
            else:
                efficiency_score = 5.0  # Neutral if no threat data
        else:
            efficiency_score = 5.0  # Neutral if no data

        # Combined score
        total_score = (
            goals_score * self.goals_weight + efficiency_score * self.efficiency_weight
        )

        return total_score


class ForwardThreatScore(PositionSpecificScore):
    """Threat rating specific scoring for forwards"""

    description = "Forward threat rating based on chances created and positioning"
    position = "FWD"

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.threat_threshold_excellent = config.get(
            "threat_threshold_excellent", 250.0
        )
        self.threat_threshold_good = config.get("threat_threshold_good", 150.0)

    def calculate_score(self, data: Dict[str, Any]) -> float:
        """Calculate threat score"""
        threat = data.get("threat", 0.0)
        played = data.get("played", 1)

        if played == 0:
            return 0.0

        threat_per_game = threat / played

        if threat_per_game >= self.threat_threshold_excellent:
            return 10.0
        elif threat_per_game >= self.threat_threshold_good:
            # Linear interpolation
            ratio = (threat_per_game - self.threat_threshold_good) / (
                self.threat_threshold_excellent - self.threat_threshold_good
            )
            return 7.0 + (ratio * 3.0)
        else:
            # Linear scaling
            ratio = threat_per_game / self.threat_threshold_good
            return min(7.0, ratio * 7.0)


class ForwardTargetManScore(PositionSpecificScore):
    """Target man ability scoring for forwards"""

    description = "Forward target man ability based on aerial duels and hold-up play"
    position = "FWD"

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.aerial_weight = config.get("aerial_weight", 0.6)
        self.hold_up_weight = config.get("hold_up_weight", 0.4)

    def calculate_score(self, data: Dict[str, Any]) -> float:
        """Calculate target man score"""
        # Use influence as proxy for overall contribution including hold-up play
        influence = data.get("influence", 0.0)
        assists = data.get("assists", 0)  # Assists indicate good hold-up play
        played = data.get("played", 1)

        if played == 0:
            return 0.0

        # Hold-up play score (based on influence and assists)
        influence_per_game = influence / played
        assists_per_game = assists / played

        hold_up_score = min(
            10.0, (influence_per_game / 25.0) + (assists_per_game * 2.0)
        )

        # Aerial ability score (simulated - would use actual aerial duel data)
        # For now, use a combination of goals and influence as proxy
        goals_scored = data.get("goals_scored", 0)
        goals_per_game = goals_scored / played

        # Assume some goals come from headers/aerial ability
        aerial_score = min(10.0, (goals_per_game * 3.0) + (influence_per_game / 30.0))

        # Combined score
        total_score = (
            aerial_score * self.aerial_weight + hold_up_score * self.hold_up_weight
        )

        return total_score


class ForwardSpeedScore(PositionSpecificScore):
    """Speed/pace ability scoring for forwards"""

    description = "Forward pace and counter-attacking threat"
    position = "FWD"

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.pace_indicators_weight = config.get("pace_indicators_weight", 1.0)

    def calculate_score(self, data: Dict[str, Any]) -> float:
        """Calculate speed/pace score"""
        # Use threat as primary indicator of pace and getting into scoring positions
        threat = data.get("threat", 0.0)
        goals_scored = data.get("goals_scored", 0)
        played = data.get("played", 1)

        if played == 0:
            return 0.0

        threat_per_game = threat / played
        goals_per_game = goals_scored / played

        # High threat with good goals suggests pace and positioning
        pace_score = min(10.0, (threat_per_game / 20.0) + (goals_per_game * 2.0))

        # Bonus for high threat-to-goals ratio (getting into positions)
        if threat_per_game > 100 and goals_per_game > 0.3:
            pace_bonus = 1.0
        else:
            pace_bonus = 0.0

        total_score = min(10.0, pace_score + pace_bonus)
        return total_score
