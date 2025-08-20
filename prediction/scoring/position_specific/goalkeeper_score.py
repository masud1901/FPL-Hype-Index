"""
Goalkeeper Scoring

This module contains position-specific scoring algorithms for goalkeepers.
"""

from typing import Dict, Any
import pandas as pd

from ..base.score_base import PositionSpecificScore
from utils.logger import get_logger

logger = get_logger("goalkeeper_score")


class GoalkeeperScore(PositionSpecificScore):
    """Position-specific scoring for goalkeepers"""

    description = "Goalkeeper scoring based on saves, clean sheets, and distribution"
    position = "GK"

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)

        # Component weights
        self.save_performance_weight = config.get("save_performance_weight", 0.4)
        self.clean_sheet_weight = config.get("clean_sheet_weight", 0.3)
        self.distribution_weight = config.get("distribution_weight", 0.2)
        self.bonus_weight = config.get("bonus_weight", 0.1)

        # Scoring thresholds
        self.saves_per_game_excellent = config.get("saves_per_game_excellent", 5.0)
        self.saves_per_game_good = config.get("saves_per_game_good", 3.0)
        self.clean_sheets_excellent = config.get("clean_sheets_excellent", 10)
        self.clean_sheets_good = config.get("clean_sheets_good", 5)

    def calculate_score(self, data: Dict[str, Any]) -> float:
        """Calculate goalkeeper-specific score"""

        # Extract goalkeeper stats
        saves = data.get("saves", 0)
        clean_sheets = data.get("clean_sheets", 0)
        goals_conceded = data.get("goals_conceded", 0)
        bonus = data.get("bonus", 0)
        influence = data.get("influence", 0.0)
        played = data.get("played", 1)

        # Calculate component scores
        save_score = self._calculate_save_performance(saves, played)
        clean_sheet_score = self._calculate_clean_sheet_score(
            clean_sheets, goals_conceded, played
        )
        distribution_score = self._calculate_distribution_score(influence)
        bonus_score = self._calculate_bonus_score(bonus, played)

        # Weighted total score
        total_score = (
            save_score * self.save_performance_weight
            + clean_sheet_score * self.clean_sheet_weight
            + distribution_score * self.distribution_weight
            + bonus_score * self.bonus_weight
        )

        return total_score

    def _calculate_save_performance(self, saves: int, played: int) -> float:
        """Calculate save performance score"""
        if played == 0:
            return 0.0

        saves_per_game = saves / played

        if saves_per_game >= self.saves_per_game_excellent:
            return 10.0
        elif saves_per_game >= self.saves_per_game_good:
            # Linear interpolation between good and excellent
            ratio = (saves_per_game - self.saves_per_game_good) / (
                self.saves_per_game_excellent - self.saves_per_game_good
            )
            return 7.0 + (ratio * 3.0)
        else:
            # Linear scaling from 0 to 7 for saves below good threshold
            ratio = saves_per_game / self.saves_per_game_good
            return min(7.0, ratio * 7.0)

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

        # Penalty for high goals conceded rate
        goals_per_game = goals_conceded / played
        if goals_per_game > 2.0:
            penalty = (goals_per_game - 2.0) * 2.0  # -2 points per extra goal per game
            base_score = max(0.0, base_score - penalty)
        elif goals_per_game < 1.0:
            bonus = (1.0 - goals_per_game) * 1.0  # +1 point for excellent defense
            base_score = min(10.0, base_score + bonus)

        return base_score

    def _calculate_distribution_score(self, influence: float) -> float:
        """Calculate distribution quality score based on influence"""
        # Normalize influence to 0-10 scale
        # Typical goalkeeper influence ranges from 0-500
        normalized_influence = min(10.0, influence / 100.0)
        return normalized_influence

    def _calculate_bonus_score(self, bonus: int, played: int) -> float:
        """Calculate bonus point potential score"""
        if played == 0:
            return 0.0

        bonus_per_game = bonus / played

        # Scale bonus per game to 0-10
        # 1 bonus per game = 10 score (very good for GK)
        score = min(10.0, bonus_per_game * 10.0)

        return score


class GoalkeeperSavePercentageScore(PositionSpecificScore):
    """Save percentage specific scoring for goalkeepers"""

    description = "Goalkeeper save percentage scoring"
    position = "GK"

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.excellent_save_percentage = config.get("excellent_save_percentage", 0.8)
        self.good_save_percentage = config.get("good_save_percentage", 0.7)

    def calculate_score(self, data: Dict[str, Any]) -> float:
        """Calculate save percentage score"""
        saves = data.get("saves", 0)
        shots_faced = data.get("shots_faced", saves + data.get("goals_conceded", 0))

        if shots_faced == 0:
            return 5.0  # Neutral score if no shots faced

        save_percentage = saves / shots_faced

        if save_percentage >= self.excellent_save_percentage:
            return 10.0
        elif save_percentage >= self.good_save_percentage:
            # Linear interpolation
            ratio = (save_percentage - self.good_save_percentage) / (
                self.excellent_save_percentage - self.good_save_percentage
            )
            return 7.0 + (ratio * 3.0)
        else:
            # Linear scaling from 0 to 7
            ratio = save_percentage / self.good_save_percentage
            return min(7.0, ratio * 7.0)


class GoalkeeperReliabilityScore(PositionSpecificScore):
    """Reliability scoring for goalkeepers based on consistency"""

    description = "Goalkeeper reliability based on consistent performance"
    position = "GK"

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.consistency_periods = config.get("consistency_periods", 5)

    def calculate_score(self, data: Dict[str, Any]) -> float:
        """Calculate reliability score based on consistent performance"""
        # Use form as proxy for consistency
        form = data.get("form", 0.0)
        total_points = data.get("total_points", 0)
        played = data.get("played", 1)

        # Base reliability from form
        form_score = min(10.0, form)

        # Consistency bonus from points per game variance (simulated)
        points_per_game = total_points / played if played > 0 else 0

        # Higher points per game with good form = reliable
        if form_score > 7.0 and points_per_game > 4.0:
            reliability_bonus = 1.0
        elif form_score > 5.0 and points_per_game > 3.0:
            reliability_bonus = 0.5
        else:
            reliability_bonus = 0.0

        # Penalty for very low form (unreliable)
        if form_score < 3.0:
            reliability_penalty = 2.0
        else:
            reliability_penalty = 0.0

        reliability_score = form_score + reliability_bonus - reliability_penalty

        return max(0.0, min(10.0, reliability_score))
