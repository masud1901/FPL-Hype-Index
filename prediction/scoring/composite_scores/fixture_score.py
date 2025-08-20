"""
Fixture Score

This module contains the Fixture Score (FxS) algorithm that evaluates
upcoming fixture difficulty and its impact on player prospects.
"""

from typing import Dict, Any, List
import pandas as pd
import numpy as np

from ..base.score_base import CompositeScore
from utils.logger import get_logger

logger = get_logger("fixture_score")


class FixtureScore(CompositeScore):
    """Fixture Score - evaluates upcoming fixture difficulty and player prospects"""

    description = "Fixture difficulty evaluation based on opponent strength, venue, and scheduling"

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)

        # Component weights
        self.difficulty_weight = config.get("difficulty_weight", 0.5)
        self.venue_weight = config.get("venue_weight", 0.2)
        self.scheduling_weight = config.get("scheduling_weight", 0.2)
        self.rotation_weight = config.get("rotation_weight", 0.1)

        # Fixture analysis parameters
        self.lookahead_gameweeks = config.get("lookahead_gameweeks", 5)
        self.home_advantage = config.get("home_advantage", 0.5)
        self.away_penalty = config.get("away_penalty", -0.3)

        # Fixture difficulty thresholds
        self.easy_fixture_threshold = config.get("easy_fixture_threshold", 2.5)
        self.hard_fixture_threshold = config.get("hard_fixture_threshold", 4.0)

        # Scheduling factors
        self.double_gameweek_bonus = config.get("double_gameweek_bonus", 2.0)
        self.blank_gameweek_penalty = config.get("blank_gameweek_penalty", -5.0)

    def calculate_score(self, data: Dict[str, Any]) -> float:
        """Calculate Fixture Score"""

        # Get upcoming fixtures data
        fixtures_data = self._get_upcoming_fixtures(data)

        # Calculate component scores
        difficulty_score = self._calculate_difficulty_score(fixtures_data)
        venue_score = self._calculate_venue_score(fixtures_data)
        scheduling_score = self._calculate_scheduling_score(fixtures_data)
        rotation_score = self._calculate_rotation_risk_score(data, fixtures_data)

        # Weighted combination
        total_score = (
            difficulty_score * self.difficulty_weight
            + venue_score * self.venue_weight
            + scheduling_score * self.scheduling_weight
            + rotation_score * self.rotation_weight
        )

        return self.normalize_score(total_score)

    def _get_upcoming_fixtures(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get upcoming fixtures data (simulated for now)"""
        # In a real implementation, this would fetch actual fixture data
        # For now, simulate based on team strength and position

        team_strength = data.get("team_strength", 50.0)
        team_position = data.get("team_position", 10)

        fixtures = []

        # Simulate upcoming fixtures
        for gw in range(self.lookahead_gameweeks):
            # Simulate opponent strength based on league position variance
            base_opponent_strength = 50.0
            variance = np.random.normal(0, 15.0)  # Random opponent
            opponent_strength = max(20.0, min(80.0, base_opponent_strength + variance))

            # Simulate venue (roughly 50% home, 50% away)
            is_home = np.random.random() > 0.5

            # Simulate fixture difficulty (1-5 scale)
            strength_diff = opponent_strength - team_strength
            base_difficulty = 3.0 + (strength_diff / 20.0)  # Scale strength diff
            difficulty = max(1.0, min(5.0, base_difficulty))

            fixture = {
                "gameweek": gw + 1,
                "opponent_strength": opponent_strength,
                "is_home": is_home,
                "difficulty": difficulty,
                "is_double": np.random.random() < 0.1,  # 10% chance of double gameweek
                "is_blank": np.random.random() < 0.05,  # 5% chance of blank gameweek
            }

            fixtures.append(fixture)

        return fixtures

    def _calculate_difficulty_score(self, fixtures_data: List[Dict[str, Any]]) -> float:
        """Calculate fixture difficulty score"""
        if not fixtures_data:
            return 5.0  # Neutral if no fixtures

        # Weight recent fixtures more heavily
        weights = [0.9**i for i in range(len(fixtures_data))]

        difficulty_scores = []
        for i, fixture in enumerate(fixtures_data):
            difficulty = fixture.get("difficulty", 3.0)

            # Convert difficulty to opportunity score (lower difficulty = higher score)
            if difficulty <= self.easy_fixture_threshold:
                opportunity_score = 8.0 + (self.easy_fixture_threshold - difficulty)
            elif difficulty >= self.hard_fixture_threshold:
                opportunity_score = max(
                    0.0, 4.0 - (difficulty - self.hard_fixture_threshold)
                )
            else:
                # Linear interpolation between easy and hard
                ratio = (difficulty - self.easy_fixture_threshold) / (
                    self.hard_fixture_threshold - self.easy_fixture_threshold
                )
                opportunity_score = 8.0 - (ratio * 4.0)  # 8 to 4

            difficulty_scores.append(opportunity_score * weights[i])

        if not difficulty_scores:
            return 5.0

        # Weighted average
        total_score = sum(difficulty_scores)
        total_weight = sum(weights[: len(difficulty_scores)])

        return total_score / total_weight if total_weight > 0 else 5.0

    def _calculate_venue_score(self, fixtures_data: List[Dict[str, Any]]) -> float:
        """Calculate venue advantage/disadvantage score"""
        if not fixtures_data:
            return 5.0

        venue_scores = []
        weights = [0.9**i for i in range(len(fixtures_data))]

        for i, fixture in enumerate(fixtures_data):
            is_home = fixture.get("is_home", True)

            if is_home:
                venue_score = 5.0 + self.home_advantage
            else:
                venue_score = 5.0 + self.away_penalty

            venue_scores.append(venue_score * weights[i])

        # Weighted average
        total_score = sum(venue_scores)
        total_weight = sum(weights[: len(venue_scores)])

        return total_score / total_weight if total_weight > 0 else 5.0

    def _calculate_scheduling_score(self, fixtures_data: List[Dict[str, Any]]) -> float:
        """Calculate scheduling advantages/disadvantages score"""
        if not fixtures_data:
            return 5.0

        base_score = 5.0

        # Count double gameweeks and blank gameweeks
        double_count = sum(1 for f in fixtures_data if f.get("is_double", False))
        blank_count = sum(1 for f in fixtures_data if f.get("is_blank", False))

        # Apply bonuses and penalties
        scheduling_adjustment = (
            double_count * self.double_gameweek_bonus
            + blank_count * self.blank_gameweek_penalty
        )

        final_score = base_score + scheduling_adjustment

        return max(0.0, min(10.0, final_score))

    def _calculate_rotation_risk_score(
        self, data: Dict[str, Any], fixtures_data: List[Dict[str, Any]]
    ) -> float:
        """Calculate rotation risk based on player status and fixture congestion"""
        # Base rotation risk factors
        position = data.get("position", "MID").upper()
        selected_by_percent = data.get("selected_by_percent", 50.0)
        total_points = data.get("total_points", 0)
        played = data.get("played", 1)

        # Calculate base rotation risk
        if played > 0:
            points_per_game = total_points / played
        else:
            points_per_game = 0.0

        # Position-based rotation risk
        position_risk = {
            "GK": 0.1,  # Goalkeepers rarely rotated
            "DEF": 0.2,  # Defenders moderate rotation
            "MID": 0.3,  # Midfielders higher rotation
            "FWD": 0.25,  # Forwards moderate rotation
        }

        base_risk = position_risk.get(position, 0.25)

        # Performance-based adjustment
        if points_per_game > 5.0:
            performance_adjustment = -0.1  # Good players less likely to be rotated
        elif points_per_game < 3.0:
            performance_adjustment = 0.15  # Poor players more likely to be rotated
        else:
            performance_adjustment = 0.0

        # Ownership-based adjustment (popular players less likely to be dropped)
        if selected_by_percent > 50.0:
            ownership_adjustment = -0.05
        elif selected_by_percent < 10.0:
            ownership_adjustment = 0.1
        else:
            ownership_adjustment = 0.0

        # Fixture congestion adjustment
        fixture_count = len([f for f in fixtures_data if not f.get("is_blank", False)])
        if fixture_count >= 3:  # Many fixtures = higher rotation risk
            congestion_adjustment = 0.1
        else:
            congestion_adjustment = 0.0

        # Calculate final rotation risk
        total_risk = (
            base_risk
            + performance_adjustment
            + ownership_adjustment
            + congestion_adjustment
        )
        total_risk = max(0.0, min(1.0, total_risk))

        # Convert risk to score (lower risk = higher score)
        rotation_score = (1.0 - total_risk) * 10.0

        return rotation_score


class FixtureDifficultyScore(CompositeScore):
    """Fixture difficulty specific scoring focusing on opponent strength"""

    description = (
        "Fixture difficulty assessment based on opponent strength and recent form"
    )

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)

        self.lookahead_weeks = config.get("lookahead_weeks", 4)
        self.strength_weight = config.get("strength_weight", 0.7)
        self.form_weight = config.get("form_weight", 0.3)

    def calculate_score(self, data: Dict[str, Any]) -> float:
        """Calculate fixture difficulty score"""
        team_strength = data.get("team_strength", 50.0)

        # Simulate upcoming opponent strengths
        upcoming_difficulties = []

        for week in range(self.lookahead_weeks):
            # Random opponent strength
            opponent_strength = np.random.normal(50.0, 15.0)
            opponent_strength = max(20.0, min(80.0, opponent_strength))

            # Calculate relative difficulty
            strength_difference = opponent_strength - team_strength

            # Convert to opportunity score (easier opponents = higher score)
            if strength_difference <= -20:  # Much stronger team
                opportunity = 9.0
            elif strength_difference <= -10:  # Stronger team
                opportunity = 7.0 + ((20 + strength_difference) / 10.0)
            elif strength_difference <= 10:  # Similar strength
                opportunity = 5.0 + ((-strength_difference) / 10.0)
            elif strength_difference <= 20:  # Weaker team
                opportunity = 3.0 + ((10 - strength_difference) / 10.0)
            else:  # Much weaker team
                opportunity = 1.0

            upcoming_difficulties.append(max(0.0, min(10.0, opportunity)))

        # Weight recent fixtures more
        weights = [0.85**i for i in range(len(upcoming_difficulties))]

        if not upcoming_difficulties:
            return 5.0

        # Weighted average
        weighted_sum = sum(
            diff * weight for diff, weight in zip(upcoming_difficulties, weights)
        )
        weight_sum = sum(weights)

        return weighted_sum / weight_sum if weight_sum > 0 else 5.0


class FixtureSchedulingScore(CompositeScore):
    """Fixture scheduling specific scoring focusing on gameweek patterns"""

    description = "Fixture scheduling assessment including double gameweeks and blanks"

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)

        self.dgw_bonus = config.get("dgw_bonus", 3.0)
        self.bgw_penalty = config.get("bgw_penalty", -4.0)
        self.fixture_count_weight = config.get("fixture_count_weight", 1.0)

    def calculate_score(self, data: Dict[str, Any]) -> float:
        """Calculate fixture scheduling score"""
        # Base score
        base_score = 5.0

        # Simulate scheduling (in real implementation, use actual fixture data)
        has_dgw = np.random.random() < 0.15  # 15% chance of DGW in period
        has_bgw = np.random.random() < 0.08  # 8% chance of BGW in period

        scheduling_adjustment = 0.0

        if has_dgw:
            scheduling_adjustment += self.dgw_bonus

        if has_bgw:
            scheduling_adjustment += self.bgw_penalty

        final_score = base_score + scheduling_adjustment

        return max(0.0, min(10.0, final_score))
