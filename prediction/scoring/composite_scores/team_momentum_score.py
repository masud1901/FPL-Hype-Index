"""
Team Momentum Score

This module contains the Team Momentum Score (TMS) algorithm that evaluates
team performance trends and their impact on player prospects.
"""

from typing import Dict, Any, List
import pandas as pd
import numpy as np

from ..base.score_base import CompositeScore
from utils.logger import get_logger

logger = get_logger("team_momentum_score")


class TeamMomentumScore(CompositeScore):
    """Team Momentum Score - evaluates team performance trends affecting player value"""

    description = "Team momentum evaluation based on recent results, goals, and expected performance"

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)

        # Component weights
        self.results_weight = config.get("results_weight", 0.4)
        self.goals_weight = config.get("goals_weight", 0.3)
        self.defensive_weight = config.get("defensive_weight", 0.2)
        self.expected_weight = config.get("expected_weight", 0.1)

        # Momentum parameters
        self.lookback_games = config.get("lookback_games", 6)
        self.recent_weight_factor = config.get(
            "recent_weight_factor", 0.8
        )  # Decay factor

        # Performance thresholds
        self.excellent_form = config.get("excellent_form", 2.0)  # Points per game
        self.good_form = config.get("good_form", 1.5)
        self.poor_form = config.get("poor_form", 0.8)

    def calculate_score(self, data: Dict[str, Any]) -> float:
        """Calculate Team Momentum Score"""

        # Extract team performance data
        team_data = self._extract_team_data(data)

        # Calculate component scores
        results_score = self._calculate_results_momentum(team_data)
        goals_score = self._calculate_attacking_momentum(team_data)
        defensive_score = self._calculate_defensive_momentum(team_data)
        expected_score = self._calculate_expected_performance(team_data)

        # Weighted combination
        total_score = (
            results_score * self.results_weight
            + goals_score * self.goals_weight
            + defensive_score * self.defensive_weight
            + expected_score * self.expected_weight
        )

        return self.normalize_score(total_score)

    def _extract_team_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract team-related data from player data"""
        team_data = {
            "team_strength": data.get("team_strength", 50.0),
            "team_form": data.get("team_form", ""),
            "team_position": data.get("team_position", 10),
            "team_points": data.get("team_points", 0),
            "team_goals_for": data.get("team_goals_for", 0),
            "team_goals_against": data.get("team_goals_against", 0),
            "team_played": data.get("team_played", 1),
        }

        return team_data

    def _calculate_results_momentum(self, team_data: Dict[str, Any]) -> float:
        """Calculate momentum from recent results"""
        team_form = team_data.get("team_form", "")
        team_points = team_data.get("team_points", 0)
        team_played = team_data.get("team_played", 1)

        # Calculate points per game
        if team_played > 0:
            ppg = team_points / team_played
        else:
            ppg = 0.0

        # Parse form string if available (e.g., "WWDLL")
        if team_form:
            form_score = self._parse_form_string(team_form)
        else:
            # Use points per game as fallback
            if ppg >= self.excellent_form:
                form_score = 10.0
            elif ppg >= self.good_form:
                ratio = (ppg - self.good_form) / (self.excellent_form - self.good_form)
                form_score = 7.0 + (ratio * 3.0)
            elif ppg >= self.poor_form:
                ratio = (ppg - self.poor_form) / (self.good_form - self.poor_form)
                form_score = 4.0 + (ratio * 3.0)
            else:
                ratio = ppg / self.poor_form
                form_score = min(4.0, ratio * 4.0)

        return max(0.0, min(10.0, form_score))

    def _parse_form_string(self, form_string: str) -> float:
        """Parse form string (e.g., 'WWDLL') into momentum score"""
        if not form_string:
            return 5.0

        # Map form characters to points
        form_points = {"W": 3, "D": 1, "L": 0}

        # Calculate weighted form score (recent games weighted more)
        total_score = 0.0
        total_weight = 0.0

        for i, result in enumerate(form_string[: self.lookback_games]):
            weight = self.recent_weight_factor**i
            points = form_points.get(result.upper(), 0)
            total_score += points * weight
            total_weight += weight

        if total_weight == 0:
            return 5.0

        # Normalize to 0-10 scale (3 points per game = 10)
        avg_points = total_score / total_weight
        normalized_score = (avg_points / 3.0) * 10.0

        return min(10.0, normalized_score)

    def _calculate_attacking_momentum(self, team_data: Dict[str, Any]) -> float:
        """Calculate momentum from attacking performance"""
        goals_for = team_data.get("team_goals_for", 0)
        played = team_data.get("team_played", 1)

        if played == 0:
            return 5.0

        goals_per_game = goals_for / played

        # Scale goals per game to 0-10
        # 2.5 goals per game = 10, 1.5 = 7, 1.0 = 4, 0.5 = 1
        if goals_per_game >= 2.5:
            return 10.0
        elif goals_per_game >= 1.5:
            ratio = (goals_per_game - 1.5) / 1.0
            return 7.0 + (ratio * 3.0)
        elif goals_per_game >= 1.0:
            ratio = (goals_per_game - 1.0) / 0.5
            return 4.0 + (ratio * 3.0)
        elif goals_per_game >= 0.5:
            ratio = (goals_per_game - 0.5) / 0.5
            return 1.0 + (ratio * 3.0)
        else:
            ratio = goals_per_game / 0.5
            return ratio * 1.0

    def _calculate_defensive_momentum(self, team_data: Dict[str, Any]) -> float:
        """Calculate momentum from defensive performance"""
        goals_against = team_data.get("team_goals_against", 0)
        played = team_data.get("team_played", 1)

        if played == 0:
            return 5.0

        goals_against_per_game = goals_against / played

        # Scale goals against per game to 0-10 (inverted - fewer goals against = better)
        # 0.5 goals against = 10, 1.0 = 7, 1.5 = 4, 2.0+ = 0
        if goals_against_per_game <= 0.5:
            return 10.0
        elif goals_against_per_game <= 1.0:
            ratio = (goals_against_per_game - 0.5) / 0.5
            return 10.0 - (ratio * 3.0)  # 10 to 7
        elif goals_against_per_game <= 1.5:
            ratio = (goals_against_per_game - 1.0) / 0.5
            return 7.0 - (ratio * 3.0)  # 7 to 4
        elif goals_against_per_game <= 2.0:
            ratio = (goals_against_per_game - 1.5) / 0.5
            return 4.0 - (ratio * 4.0)  # 4 to 0
        else:
            return 0.0

    def _calculate_expected_performance(self, team_data: Dict[str, Any]) -> float:
        """Calculate expected performance momentum based on underlying metrics"""
        # Use team strength and position as proxies for expected performance
        team_strength = team_data.get("team_strength", 50.0)
        team_position = team_data.get("team_position", 10)

        # Team strength component (0-100 scale to 0-10)
        strength_score = team_strength / 10.0

        # League position component (inverted - lower position number = better)
        if team_position <= 4:  # Top 4
            position_score = 10.0
        elif team_position <= 8:  # Top half
            position_score = 8.0 - ((team_position - 4) * 0.5)
        elif team_position <= 14:  # Mid table
            position_score = 6.0 - ((team_position - 8) * 0.33)
        else:  # Bottom
            position_score = max(0.0, 4.0 - ((team_position - 14) * 0.67))

        # Combine strength and position
        expected_score = (strength_score * 0.6) + (position_score * 0.4)

        return min(10.0, expected_score)


class TeamFormScore(CompositeScore):
    """Team form specific scoring focusing on recent team performance"""

    description = (
        "Team form evaluation based on recent results and performance indicators"
    )

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)

        self.form_periods = config.get(
            "form_periods", [3, 6, 10]
        )  # Last 3, 6, 10 games
        self.period_weights = config.get("period_weights", [0.5, 0.3, 0.2])
        self.consistency_bonus = config.get("consistency_bonus", 1.0)

    def calculate_score(self, data: Dict[str, Any]) -> float:
        """Calculate team form score"""
        team_form = data.get("team_form", "")
        team_points = data.get("team_points", 0)
        team_played = data.get("team_played", 1)

        if not team_form and team_played == 0:
            return 5.0  # Neutral

        # Calculate form for different periods
        form_scores = []

        for period, weight in zip(self.form_periods, self.period_weights):
            if team_form and len(team_form) >= period:
                period_form = team_form[:period]  # Most recent games
                period_score = self._calculate_period_form(period_form)
                form_scores.append(period_score * weight)
            elif team_played > 0:
                # Use points per game as fallback
                ppg = team_points / team_played
                fallback_score = min(10.0, (ppg / 3.0) * 10.0)
                form_scores.append(fallback_score * weight)

        if not form_scores:
            return 5.0

        base_score = sum(form_scores)

        # Add consistency bonus
        if team_form:
            consistency_score = self._calculate_consistency_bonus(team_form)
            base_score += consistency_score

        return min(10.0, base_score)

    def _calculate_period_form(self, period_form: str) -> float:
        """Calculate form score for a specific period"""
        if not period_form:
            return 5.0

        form_points = {"W": 3, "D": 1, "L": 0}
        total_points = sum(form_points.get(result.upper(), 0) for result in period_form)
        max_points = len(period_form) * 3

        if max_points == 0:
            return 5.0

        # Normalize to 0-10 scale
        form_percentage = total_points / max_points
        return form_percentage * 10.0

    def _calculate_consistency_bonus(self, team_form: str) -> float:
        """Calculate consistency bonus based on form pattern"""
        if len(team_form) < 3:
            return 0.0

        # Count streaks
        current_result = team_form[0] if team_form else None
        streak_length = 0
        max_streak = 0

        for result in team_form:
            if result == current_result:
                streak_length += 1
            else:
                max_streak = max(max_streak, streak_length)
                current_result = result
                streak_length = 1

        max_streak = max(max_streak, streak_length)

        # Bonus for consistent performance (especially winning streaks)
        if current_result == "W" and max_streak >= 3:
            return min(self.consistency_bonus, max_streak * 0.2)
        elif current_result in ["W", "D"] and max_streak >= 4:
            return min(self.consistency_bonus * 0.5, max_streak * 0.1)

        return 0.0
