"""
Form Consistency Score

This module contains the Form Consistency Score (FCS) algorithm that evaluates
player performance trends and consistency over recent gameweeks.
"""

from typing import Dict, Any, List
import pandas as pd
import numpy as np

from ..base.score_base import CompositeScore
from utils.logger import get_logger

logger = get_logger("form_consistency_score")


class FormConsistencyScore(CompositeScore):
    """Form Consistency Score - evaluates recent form and performance consistency"""

    description = (
        "Player form and consistency evaluation based on recent performance trends"
    )

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)

        # Form evaluation parameters
        self.lookback_gameweeks = config.get("lookback_gameweeks", 6)
        self.recent_weight = config.get("recent_weight", 0.6)  # Weight for recent form
        self.consistency_weight = config.get(
            "consistency_weight", 0.4
        )  # Weight for consistency

        # Form thresholds
        self.excellent_form = config.get("excellent_form", 7.0)
        self.good_form = config.get("good_form", 5.0)
        self.poor_form = config.get("poor_form", 3.0)

        # Consistency thresholds
        self.high_consistency = config.get("high_consistency", 1.5)  # Low variance
        self.medium_consistency = config.get("medium_consistency", 2.5)

        # Trend analysis
        self.trend_weight = config.get("trend_weight", 0.2)
        self.momentum_decay = config.get("momentum_decay", 0.8)

    def calculate_score(self, data: Dict[str, Any]) -> float:
        """Calculate Form Consistency Score"""

        # Get recent form data
        recent_form = self._get_recent_form(data)
        form_score = self._calculate_form_score(recent_form)

        # Calculate consistency score
        consistency_score = self._calculate_consistency_score(recent_form)

        # Calculate trend score
        trend_score = self._calculate_trend_score(recent_form)

        # Combine scores
        total_score = (
            form_score * self.recent_weight
            + consistency_score * self.consistency_weight
            + trend_score * self.trend_weight
        )

        # Normalize to ensure total weights = 1
        weight_sum = self.recent_weight + self.consistency_weight + self.trend_weight
        total_score = total_score / weight_sum

        return self.normalize_score(total_score)

    def _get_recent_form(self, data: Dict[str, Any]) -> List[float]:
        """Extract recent form data from player data"""
        # Use FPL form as base, but enhance with point history if available
        form_value = data.get("form", 0.0)
        total_points = data.get("total_points", 0)
        played = data.get("played", 1)

        # If we have detailed history, use it (placeholder for future enhancement)
        # For now, simulate recent form based on available data
        recent_form = self._simulate_recent_form(form_value, total_points, played)

        return recent_form

    def _simulate_recent_form(
        self, form_value: float, total_points: int, played: int
    ) -> List[float]:
        """Simulate recent form data from available stats"""
        if played == 0:
            return [0.0] * self.lookback_gameweeks

        # Use form as base and add some variation
        base_performance = total_points / played

        # Create simulated recent performances around form value
        recent_form = []
        for i in range(min(self.lookback_gameweeks, played)):
            # Add random variation around form value
            noise = np.random.normal(0, 1.0)  # Small random variation
            simulated_performance = max(0, form_value + noise)
            recent_form.append(simulated_performance)

        # If we have fewer games than lookback, pad with zeros
        while len(recent_form) < self.lookback_gameweeks:
            recent_form.append(0.0)

        return recent_form

    def _calculate_form_score(self, recent_form: List[float]) -> float:
        """Calculate recent form score"""
        if not recent_form or all(f == 0 for f in recent_form):
            return 0.0

        # Weight recent performances more heavily
        weights = [self.momentum_decay**i for i in range(len(recent_form))]
        weights.reverse()  # Most recent gets highest weight

        # Calculate weighted average
        weighted_sum = sum(form * weight for form, weight in zip(recent_form, weights))
        weight_sum = sum(weights)

        if weight_sum == 0:
            return 0.0

        average_form = weighted_sum / weight_sum

        # Map to 0-10 scale
        if average_form >= self.excellent_form:
            return 10.0
        elif average_form >= self.good_form:
            # Linear interpolation between good and excellent
            ratio = (average_form - self.good_form) / (
                self.excellent_form - self.good_form
            )
            return 7.0 + (ratio * 3.0)
        elif average_form >= self.poor_form:
            # Linear interpolation between poor and good
            ratio = (average_form - self.poor_form) / (self.good_form - self.poor_form)
            return 3.0 + (ratio * 4.0)
        else:
            # Linear scaling from 0 to 3
            ratio = average_form / self.poor_form
            return max(0.0, ratio * 3.0)

    def _calculate_consistency_score(self, recent_form: List[float]) -> float:
        """Calculate consistency score based on performance variance"""
        if not recent_form or len(recent_form) < 2:
            return 5.0  # Neutral score if insufficient data

        # Filter out zero values (games not played)
        non_zero_form = [f for f in recent_form if f > 0]

        if len(non_zero_form) < 2:
            return 5.0  # Neutral score

        # Calculate coefficient of variation (std dev / mean)
        mean_form = np.mean(non_zero_form)
        std_form = np.std(non_zero_form)

        if mean_form == 0:
            return 0.0

        cv = std_form / mean_form

        # Lower coefficient of variation = higher consistency
        if cv <= self.high_consistency:
            consistency_score = 10.0
        elif cv <= self.medium_consistency:
            # Linear interpolation
            ratio = (cv - self.high_consistency) / (
                self.medium_consistency - self.high_consistency
            )
            consistency_score = 10.0 - (ratio * 3.0)  # 10 to 7
        else:
            # Higher variance = lower consistency
            ratio = min(1.0, (cv - self.medium_consistency) / self.medium_consistency)
            consistency_score = 7.0 - (ratio * 7.0)  # 7 to 0

        return max(0.0, consistency_score)

    def _calculate_trend_score(self, recent_form: List[float]) -> float:
        """Calculate trend score based on performance direction"""
        if not recent_form or len(recent_form) < 3:
            return 5.0  # Neutral score

        # Filter out zeros and ensure we have enough data
        non_zero_form = [(i, f) for i, f in enumerate(recent_form) if f > 0]

        if len(non_zero_form) < 3:
            return 5.0

        # Calculate linear trend
        x_values = [i for i, _ in non_zero_form]
        y_values = [f for _, f in non_zero_form]

        # Simple linear regression slope
        n = len(x_values)
        if n < 2:
            return 5.0

        x_mean = np.mean(x_values)
        y_mean = np.mean(y_values)

        numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(x_values, y_values))
        denominator = sum((x - x_mean) ** 2 for x in x_values)

        if denominator == 0:
            return 5.0

        slope = numerator / denominator

        # Convert slope to trend score
        # Positive slope = improving form, negative = declining form
        if slope > 0.5:  # Strong upward trend
            trend_score = 8.0 + min(2.0, slope)  # 8-10 range
        elif slope > 0:  # Mild upward trend
            trend_score = 5.0 + (slope * 6.0)  # 5-8 range
        elif slope > -0.5:  # Mild downward trend
            trend_score = 5.0 + (slope * 6.0)  # 2-5 range
        else:  # Strong downward trend
            trend_score = max(0.0, 2.0 + slope)  # 0-2 range

        return max(0.0, min(10.0, trend_score))


class FormMomentumScore(CompositeScore):
    """Form momentum specific scoring focusing on recent trajectory"""

    description = "Player form momentum based on recent performance trajectory"

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)

        self.momentum_periods = config.get(
            "momentum_periods", [1, 3, 5]
        )  # Last 1, 3, 5 games
        self.period_weights = config.get("period_weights", [0.5, 0.3, 0.2])

    def calculate_score(self, data: Dict[str, Any]) -> float:
        """Calculate form momentum score"""
        form_value = data.get("form", 0.0)
        total_points = data.get("total_points", 0)
        played = data.get("played", 1)

        if played == 0:
            return 0.0

        # Get recent performances (simulated)
        recent_form = self._simulate_recent_form(form_value, total_points, played)

        # Calculate momentum for different periods
        momentum_scores = []

        for period, weight in zip(self.momentum_periods, self.period_weights):
            if len(recent_form) >= period:
                period_form = recent_form[:period]  # Most recent games
                period_momentum = self._calculate_period_momentum(period_form)
                momentum_scores.append(period_momentum * weight)

        if not momentum_scores:
            return 5.0  # Neutral

        total_momentum = sum(momentum_scores)
        return self.normalize_score(total_momentum)

    def _simulate_recent_form(
        self, form_value: float, total_points: int, played: int
    ) -> List[float]:
        """Simulate recent form (same as FormConsistencyScore for consistency)"""
        if played == 0:
            return []

        base_performance = total_points / played
        recent_form = []

        for i in range(min(6, played)):  # Last 6 games
            noise = np.random.normal(0, 0.5)
            simulated_performance = max(0, form_value + noise)
            recent_form.append(simulated_performance)

        return recent_form

    def _calculate_period_momentum(self, period_form: List[float]) -> float:
        """Calculate momentum for a specific period"""
        if not period_form:
            return 5.0

        if len(period_form) == 1:
            # Single game - just normalize the performance
            return min(10.0, period_form[0])

        # Calculate trend within period
        x_values = list(range(len(period_form)))
        y_values = period_form

        # Linear regression slope
        n = len(x_values)
        x_mean = sum(x_values) / n
        y_mean = sum(y_values) / n

        numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(x_values, y_values))
        denominator = sum((x - x_mean) ** 2 for x in x_values)

        if denominator == 0:
            return min(10.0, y_mean)  # No trend, use average

        slope = numerator / denominator

        # Combine average performance with trend
        avg_performance = y_mean
        trend_bonus = slope * 2.0  # Amplify trend effect

        momentum_score = avg_performance + trend_bonus
        return max(0.0, min(10.0, momentum_score))
