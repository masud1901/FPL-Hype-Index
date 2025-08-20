"""
Value Score

This module contains the Value Score (VS) algorithm that evaluates
player value proposition based on price, ownership, and differential potential.
"""

from typing import Dict, Any
import pandas as pd
import numpy as np

from ..base.score_base import CompositeScore
from utils.logger import get_logger

logger = get_logger("value_score")


class ValueScore(CompositeScore):
    """Value Score - evaluates player value proposition and differential potential"""

    description = "Player value assessment based on price efficiency, ownership, and differential potential"

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)

        # Component weights
        self.price_efficiency_weight = config.get("price_efficiency_weight", 0.4)
        self.ownership_weight = config.get("ownership_weight", 0.3)
        self.differential_weight = config.get("differential_weight", 0.2)
        self.momentum_weight = config.get("momentum_weight", 0.1)

        # Value thresholds
        self.excellent_ppm = config.get("excellent_ppm", 25.0)  # Points per million
        self.good_ppm = config.get("good_ppm", 20.0)
        self.poor_ppm = config.get("poor_ppm", 15.0)

        # Ownership thresholds
        self.high_ownership = config.get("high_ownership", 50.0)
        self.medium_ownership = config.get("medium_ownership", 20.0)
        self.low_ownership = config.get("low_ownership", 5.0)

        # Differential thresholds
        self.template_penalty = config.get("template_penalty", -1.0)
        self.differential_bonus = config.get("differential_bonus", 2.0)

    def calculate_score(self, data: Dict[str, Any]) -> float:
        """Calculate Value Score"""

        # Calculate component scores
        price_efficiency_score = self._calculate_price_efficiency(data)
        ownership_score = self._calculate_ownership_score(data)
        differential_score = self._calculate_differential_potential(data)
        momentum_score = self._calculate_value_momentum(data)

        # Weighted combination
        total_score = (
            price_efficiency_score * self.price_efficiency_weight
            + ownership_score * self.ownership_weight
            + differential_score * self.differential_weight
            + momentum_score * self.momentum_weight
        )

        return self.normalize_score(total_score)

    def _calculate_price_efficiency(self, data: Dict[str, Any]) -> float:
        """Calculate price efficiency score (points per million)"""
        price = data.get("price", 10.0)
        total_points = data.get("total_points", 0)

        if price <= 0:
            return 0.0

        points_per_million = total_points / price

        # Map to 0-10 scale
        if points_per_million >= self.excellent_ppm:
            return 10.0
        elif points_per_million >= self.good_ppm:
            # Linear interpolation between good and excellent
            ratio = (points_per_million - self.good_ppm) / (
                self.excellent_ppm - self.good_ppm
            )
            return 7.0 + (ratio * 3.0)
        elif points_per_million >= self.poor_ppm:
            # Linear interpolation between poor and good
            ratio = (points_per_million - self.poor_ppm) / (
                self.good_ppm - self.poor_ppm
            )
            return 4.0 + (ratio * 3.0)
        else:
            # Linear scaling below poor threshold
            ratio = points_per_million / self.poor_ppm
            return min(4.0, ratio * 4.0)

    def _calculate_ownership_score(self, data: Dict[str, Any]) -> float:
        """Calculate ownership-based score (lower ownership can be better for differentials)"""
        ownership = data.get("selected_by_percent", 50.0)

        # Ownership score depends on strategy context
        # For value/differential purposes, moderate ownership is often optimal

        if ownership >= self.high_ownership:
            # Very high ownership - template player, less differential value
            ownership_score = 4.0 - min(2.0, (ownership - self.high_ownership) / 25.0)
        elif ownership >= self.medium_ownership:
            # Medium ownership - good balance
            ratio = (ownership - self.medium_ownership) / (
                self.high_ownership - self.medium_ownership
            )
            ownership_score = 8.0 - (ratio * 2.0)  # 8 to 6
        elif ownership >= self.low_ownership:
            # Low-medium ownership - potential differential
            ratio = (ownership - self.low_ownership) / (
                self.medium_ownership - self.low_ownership
            )
            ownership_score = 6.0 + (ratio * 2.0)  # 6 to 8
        else:
            # Very low ownership - either trap or great differential
            # Need to check if performance justifies low ownership
            total_points = data.get("total_points", 0)
            played = data.get("played", 1)

            if played > 0:
                ppg = total_points / played
                if ppg > 4.0:  # Good performance despite low ownership
                    ownership_score = 9.0
                elif ppg > 2.0:  # Reasonable performance
                    ownership_score = 6.0
                else:  # Poor performance explains low ownership
                    ownership_score = 2.0
            else:
                ownership_score = 3.0  # Unknown

        return max(0.0, min(10.0, ownership_score))

    def _calculate_differential_potential(self, data: Dict[str, Any]) -> float:
        """Calculate differential potential score"""
        ownership = data.get("selected_by_percent", 50.0)
        total_points = data.get("total_points", 0)
        price = data.get("price", 10.0)
        played = data.get("played", 1)

        if played == 0:
            return 5.0

        ppg = total_points / played

        # Base differential score
        if ownership < self.low_ownership:
            # Very low ownership
            if ppg > 5.0:  # Excellent performance
                differential_score = 10.0
            elif ppg > 3.5:  # Good performance
                differential_score = 8.0
            elif ppg > 2.0:  # Moderate performance
                differential_score = 6.0
            else:  # Poor performance (trap)
                differential_score = 2.0
        elif ownership < self.medium_ownership:
            # Low-medium ownership
            if ppg > 4.5:  # Great performance
                differential_score = 8.0
            elif ppg > 3.0:  # Good performance
                differential_score = 7.0
            else:  # Moderate performance
                differential_score = 5.0
        elif ownership < self.high_ownership:
            # Medium-high ownership
            if ppg > 5.0:  # Excellent but popular
                differential_score = 6.0
            else:  # Popular but not exceptional
                differential_score = 4.0
        else:
            # Very high ownership (template)
            if ppg > 6.0:  # Essential player
                differential_score = 5.0  # Must have but no differential
            else:  # Overhyped
                differential_score = 2.0

        # Price adjustment - cheaper players have higher differential potential
        if price < 6.0:  # Cheap player
            price_bonus = 1.0
        elif price < 8.0:  # Mid-price
            price_bonus = 0.5
        else:  # Expensive
            price_bonus = 0.0

        final_score = differential_score + price_bonus

        return max(0.0, min(10.0, final_score))

    def _calculate_value_momentum(self, data: Dict[str, Any]) -> float:
        """Calculate value momentum based on recent trends"""
        # Use transfers in/out and form as momentum indicators
        transfers_in = data.get("transfers_in", 0)
        transfers_out = data.get("transfers_out", 0)
        form = data.get("form", 0.0)

        # Net transfers momentum
        net_transfers = transfers_in - transfers_out

        # Normalize transfers (assuming they're in thousands or similar scale)
        transfer_momentum = 0.0
        if net_transfers > 100000:  # High net transfers in
            transfer_momentum = 2.0
        elif net_transfers > 50000:  # Moderate net transfers in
            transfer_momentum = 1.0
        elif net_transfers > -50000:  # Stable
            transfer_momentum = 0.0
        elif net_transfers > -100000:  # Moderate net transfers out
            transfer_momentum = -1.0
        else:  # High net transfers out
            transfer_momentum = -2.0

        # Form momentum
        form_momentum = 0.0
        if form > 6.0:  # Excellent form
            form_momentum = 2.0
        elif form > 4.0:  # Good form
            form_momentum = 1.0
        elif form > 2.0:  # Poor form
            form_momentum = -1.0
        else:  # Very poor form
            form_momentum = -2.0

        # Combine momentums
        total_momentum = transfer_momentum + form_momentum

        # Map to 0-10 scale (5 is neutral)
        momentum_score = 5.0 + total_momentum

        return max(0.0, min(10.0, momentum_score))


class PriceEfficiencyScore(CompositeScore):
    """Price efficiency specific scoring focusing on points per million"""

    description = (
        "Price efficiency assessment based on points per million and value trends"
    )

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)

        self.ppm_weight = config.get("ppm_weight", 0.8)
        self.price_trend_weight = config.get("price_trend_weight", 0.2)

        # Position-specific PPM expectations
        self.position_ppm_expectations = config.get(
            "position_ppm_expectations",
            {
                "GK": 18.0,  # Goalkeepers typically lower PPM
                "DEF": 20.0,  # Defenders moderate PPM
                "MID": 22.0,  # Midfielders higher PPM expected
                "FWD": 20.0,  # Forwards moderate-high PPM
            },
        )

    def calculate_score(self, data: Dict[str, Any]) -> float:
        """Calculate price efficiency score"""
        price = data.get("price", 10.0)
        total_points = data.get("total_points", 0)
        position = data.get("position", "MID").upper()

        if price <= 0:
            return 0.0

        # Calculate actual PPM
        actual_ppm = total_points / price

        # Get position-specific expectation
        expected_ppm = self.position_ppm_expectations.get(position, 20.0)

        # Calculate efficiency relative to position expectation
        efficiency_ratio = actual_ppm / expected_ppm

        # Map ratio to score
        if efficiency_ratio >= 1.5:  # 50% better than expected
            ppm_score = 10.0
        elif efficiency_ratio >= 1.2:  # 20% better than expected
            ratio = (efficiency_ratio - 1.2) / 0.3
            ppm_score = 8.0 + (ratio * 2.0)
        elif efficiency_ratio >= 1.0:  # Meeting expectations
            ratio = (efficiency_ratio - 1.0) / 0.2
            ppm_score = 6.0 + (ratio * 2.0)
        elif efficiency_ratio >= 0.8:  # Slightly below expectations
            ratio = (efficiency_ratio - 0.8) / 0.2
            ppm_score = 4.0 + (ratio * 2.0)
        else:  # Well below expectations
            ratio = min(1.0, efficiency_ratio / 0.8)
            ppm_score = ratio * 4.0

        # Price trend component (simulated)
        # In real implementation, this would use historical price data
        price_trend_score = 5.0  # Neutral for now

        # Combine scores
        total_score = (
            ppm_score * self.ppm_weight + price_trend_score * self.price_trend_weight
        )

        return max(0.0, min(10.0, total_score))


class DifferentialValueScore(CompositeScore):
    """Differential value specific scoring for identifying unique picks"""

    description = (
        "Differential value assessment for identifying unique high-potential picks"
    )

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)

        self.performance_weight = config.get("performance_weight", 0.4)
        self.ownership_weight = config.get("ownership_weight", 0.3)
        self.potential_weight = config.get("potential_weight", 0.2)
        self.risk_weight = config.get("risk_weight", 0.1)

    def calculate_score(self, data: Dict[str, Any]) -> float:
        """Calculate differential value score"""
        # Performance component
        total_points = data.get("total_points", 0)
        played = data.get("played", 1)
        ppg = total_points / played if played > 0 else 0
        performance_score = min(10.0, ppg * 2.0)  # 5 PPG = 10 score

        # Ownership component (inverted - lower ownership = higher differential value)
        ownership = data.get("selected_by_percent", 50.0)
        if ownership < 5:
            ownership_score = 10.0
        elif ownership < 15:
            ownership_score = 8.0 - ((ownership - 5) / 10) * 2.0
        elif ownership < 30:
            ownership_score = 6.0 - ((ownership - 15) / 15) * 3.0
        else:
            ownership_score = max(0.0, 3.0 - ((ownership - 30) / 70) * 3.0)

        # Potential component (based on form and fixtures)
        form = data.get("form", 0.0)
        potential_score = min(10.0, form * 1.5)

        # Risk component (price relative to potential loss)
        price = data.get("price", 10.0)
        if price < 6.0:  # Low price = low risk
            risk_score = 8.0
        elif price < 8.0:  # Medium price
            risk_score = 6.0
        else:  # High price = high risk for differential
            risk_score = 4.0

        # Combine scores
        total_score = (
            performance_score * self.performance_weight
            + ownership_score * self.ownership_weight
            + potential_score * self.potential_weight
            + risk_score * self.risk_weight
        )

        return max(0.0, min(10.0, total_score))
