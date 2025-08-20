"""
Player Impact Score

This module contains the master Player Impact Score (PIS) calculator that combines
all sub-scores into the final prediction score.
"""

from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np

from ..base.score_base import MasterScore
from ..composite_scores.advanced_quality_score import AdvancedQualityScore
from ..composite_scores.form_consistency_score import FormConsistencyScore
from ..composite_scores.team_momentum_score import TeamMomentumScore
from ..composite_scores.fixture_score import FixtureScore
from ..composite_scores.value_score import ValueScore
from utils.logger import get_logger

logger = get_logger("player_impact_score")


class PlayerImpactScore(MasterScore):
    """Master Player Impact Score - combines all sub-scores into final prediction"""

    description = "Master Player Impact Score combining all sub-scores with interaction bonuses and risk penalties"

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)

        # Sub-score weights (these sum to 1.0)
        self.sub_score_weights = config.get(
            "sub_score_weights",
            {
                "AdvancedQualityScore": 0.35,  # 35% - Core quality assessment
                "FormConsistencyScore": 0.25,  # 25% - Recent form and consistency
                "TeamMomentumScore": 0.15,  # 15% - Team performance context
                "FixtureScore": 0.15,  # 15% - Upcoming fixture difficulty
                "ValueScore": 0.10,  # 10% - Price efficiency and differential
            },
        )

        # Interaction bonus thresholds and values
        self.interaction_bonuses = config.get(
            "interaction_bonuses",
            {
                "quality_form_threshold": 7.0,  # Both AQS and FCS above this
                "quality_form_bonus": 0.5,  # Bonus for high quality + form
                "form_fixture_threshold": 6.5,  # Both FCS and FxS above this
                "form_fixture_bonus": 0.3,  # Bonus for good form + fixtures
                "quality_value_threshold": 6.0,  # Both AQS and VS above this
                "quality_value_bonus": 0.2,  # Bonus for quality + value
                "team_form_threshold": 6.0,  # Both TMS and FCS above this
                "team_form_bonus": 0.2,  # Bonus for team momentum + form
            },
        )

        # Risk penalty factors
        self.risk_penalties = config.get(
            "risk_penalties",
            {
                "injury_risk_threshold": 0.3,  # High injury risk threshold
                "injury_penalty": -0.5,  # Penalty for injury risk
                "rotation_risk_threshold": 0.4,  # High rotation risk threshold
                "rotation_penalty": -0.3,  # Penalty for rotation risk
                "ownership_risk_threshold": 0.1,  # Very low ownership threshold
                "ownership_penalty": -0.2,  # Penalty for very low ownership
                "price_risk_threshold": 12.0,  # Very high price threshold
                "price_penalty": -0.2,  # Penalty for very expensive players
            },
        )

        # Confidence calculation parameters
        self.confidence_factors = config.get(
            "confidence_factors",
            {
                "data_quality_weight": 0.4,  # Weight for data quality
                "sample_size_weight": 0.3,  # Weight for sample size
                "consistency_weight": 0.3,  # Weight for score consistency
            },
        )

        # Sub-score instances
        self.sub_scorers = {
            "AdvancedQualityScore": AdvancedQualityScore(config.get("aqs_config", {})),
            "FormConsistencyScore": FormConsistencyScore(config.get("fcs_config", {})),
            "TeamMomentumScore": TeamMomentumScore(config.get("tms_config", {})),
            "FixtureScore": FixtureScore(config.get("fxs_config", {})),
            "ValueScore": ValueScore(config.get("vs_config", {})),
        }

    def calculate_score(self, data: Dict[str, Any]) -> float:
        """Calculate master Player Impact Score"""

        # Calculate all sub-scores
        sub_scores = self._calculate_sub_scores(data)

        # Calculate base score from weighted sub-scores
        base_score = self.calculate_base_score(sub_scores)

        # Calculate interaction bonuses
        interaction_bonus = self.calculate_interaction_bonus(sub_scores)

        # Calculate risk penalties
        risk_penalty = self.calculate_risk_penalty(data)

        # Calculate confidence multiplier
        confidence_multiplier = self.calculate_confidence_multiplier(data, sub_scores)

        # Combine all components
        final_score = (
            base_score + interaction_bonus + risk_penalty
        ) * confidence_multiplier

        # Normalize to 0-15 scale (allowing for bonuses)
        final_score = max(0.0, min(15.0, final_score))

        logger.debug(
            f"PIS calculation: base={base_score:.2f}, bonus={interaction_bonus:.2f}, "
            f"penalty={risk_penalty:.2f}, confidence={confidence_multiplier:.2f}, "
            f"final={final_score:.2f}"
        )

        return final_score

    def _calculate_sub_scores(self, data: Dict[str, Any]) -> Dict[str, float]:
        """Calculate all sub-scores"""
        sub_scores = {}

        for score_name, scorer in self.sub_scorers.items():
            try:
                score_value = scorer.calculate_with_validation(data)
                sub_scores[score_name] = score_value
                logger.debug(f"Calculated {score_name}: {score_value:.2f}")
            except Exception as e:
                logger.error(f"Error calculating {score_name}: {e}")
                sub_scores[score_name] = 0.0

        return sub_scores

    def calculate_interaction_bonus(self, sub_scores: Dict[str, float]) -> float:
        """Calculate interaction bonus between sub-scores"""
        total_bonus = 0.0

        # Quality + Form interaction
        aqs = sub_scores.get("AdvancedQualityScore", 0.0)
        fcs = sub_scores.get("FormConsistencyScore", 0.0)
        if (
            aqs >= self.interaction_bonuses["quality_form_threshold"]
            and fcs >= self.interaction_bonuses["quality_form_threshold"]
        ):
            total_bonus += self.interaction_bonuses["quality_form_bonus"]
            logger.debug(
                f"Quality+Form bonus: {self.interaction_bonuses['quality_form_bonus']:.2f}"
            )

        # Form + Fixture interaction
        fxs = sub_scores.get("FixtureScore", 0.0)
        if (
            fcs >= self.interaction_bonuses["form_fixture_threshold"]
            and fxs >= self.interaction_bonuses["form_fixture_threshold"]
        ):
            total_bonus += self.interaction_bonuses["form_fixture_bonus"]
            logger.debug(
                f"Form+Fixture bonus: {self.interaction_bonuses['form_fixture_bonus']:.2f}"
            )

        # Quality + Value interaction
        vs = sub_scores.get("ValueScore", 0.0)
        if (
            aqs >= self.interaction_bonuses["quality_value_threshold"]
            and vs >= self.interaction_bonuses["quality_value_threshold"]
        ):
            total_bonus += self.interaction_bonuses["quality_value_bonus"]
            logger.debug(
                f"Quality+Value bonus: {self.interaction_bonuses['quality_value_bonus']:.2f}"
            )

        # Team + Form interaction
        tms = sub_scores.get("TeamMomentumScore", 0.0)
        if (
            tms >= self.interaction_bonuses["team_form_threshold"]
            and fcs >= self.interaction_bonuses["team_form_threshold"]
        ):
            total_bonus += self.interaction_bonuses["team_form_bonus"]
            logger.debug(
                f"Team+Form bonus: {self.interaction_bonuses['team_form_bonus']:.2f}"
            )

        return total_bonus

    def calculate_risk_penalty(self, data: Dict[str, Any]) -> float:
        """Calculate risk penalty based on player risk factors"""
        total_penalty = 0.0

        # Injury risk penalty (simulated - would use actual injury data)
        injury_risk = self._calculate_injury_risk(data)
        if injury_risk >= self.risk_penalties["injury_risk_threshold"]:
            total_penalty += self.risk_penalties["injury_penalty"]
            logger.debug(
                f"Injury risk penalty: {self.risk_penalties['injury_penalty']:.2f}"
            )

        # Rotation risk penalty
        rotation_risk = self._calculate_rotation_risk(data)
        if rotation_risk >= self.risk_penalties["rotation_risk_threshold"]:
            total_penalty += self.risk_penalties["rotation_penalty"]
            logger.debug(
                f"Rotation risk penalty: {self.risk_penalties['rotation_penalty']:.2f}"
            )

        # Ownership risk penalty
        ownership = data.get("selected_by_percent", 50.0)
        if ownership <= self.risk_penalties["ownership_risk_threshold"]:
            total_penalty += self.risk_penalties["ownership_penalty"]
            logger.debug(
                f"Ownership risk penalty: {self.risk_penalties['ownership_penalty']:.2f}"
            )

        # Price risk penalty
        price = data.get("price", 10.0)
        if price >= self.risk_penalties["price_risk_threshold"]:
            total_penalty += self.risk_penalties["price_penalty"]
            logger.debug(
                f"Price risk penalty: {self.risk_penalties['price_penalty']:.2f}"
            )

        return total_penalty

    def calculate_confidence_multiplier(
        self, data: Dict[str, Any], sub_scores: Dict[str, float]
    ) -> float:
        """Calculate confidence multiplier based on data quality and consistency"""

        # Data quality component
        data_quality = self._calculate_data_quality(data)

        # Sample size component
        sample_size = self._calculate_sample_size_confidence(data)

        # Consistency component
        consistency = self._calculate_score_consistency(sub_scores)

        # Weighted combination
        confidence = (
            data_quality * self.confidence_factors["data_quality_weight"]
            + sample_size * self.confidence_factors["sample_size_weight"]
            + consistency * self.confidence_factors["consistency_weight"]
        )

        # Normalize to 0.5-1.5 range (50% to 150% confidence)
        confidence = 0.5 + (confidence * 1.0)

        logger.debug(
            f"Confidence: data_quality={data_quality:.2f}, "
            f"sample_size={sample_size:.2f}, consistency={consistency:.2f}, "
            f"final={confidence:.2f}"
        )

        return confidence

    def _calculate_injury_risk(self, data: Dict[str, Any]) -> float:
        """Calculate injury risk (simulated)"""
        # In real implementation, this would use injury history and medical data
        # For now, use form and minutes as proxies

        form = data.get("form", 0.0)
        played = data.get("played", 1)
        total_points = data.get("total_points", 0)

        # Lower form and fewer minutes = higher injury risk
        if played > 0:
            points_per_game = total_points / played
        else:
            points_per_game = 0.0

        # Simulate injury risk based on performance patterns
        if form < 3.0 and points_per_game < 2.0:
            injury_risk = 0.4  # High risk
        elif form < 5.0 or points_per_game < 3.0:
            injury_risk = 0.2  # Medium risk
        else:
            injury_risk = 0.05  # Low risk

        return injury_risk

    def _calculate_rotation_risk(self, data: Dict[str, Any]) -> float:
        """Calculate rotation risk"""
        position = data.get("position", "MID").upper()
        selected_by_percent = data.get("selected_by_percent", 50.0)
        total_points = data.get("total_points", 0)
        played = data.get("played", 1)

        if played > 0:
            points_per_game = total_points / played
        else:
            points_per_game = 0.0

        # Position-based base risk
        position_risk = {"GK": 0.1, "DEF": 0.2, "MID": 0.3, "FWD": 0.25}

        base_risk = position_risk.get(position, 0.25)

        # Performance adjustment
        if points_per_game > 5.0:
            performance_adjustment = -0.1
        elif points_per_game < 3.0:
            performance_adjustment = 0.15
        else:
            performance_adjustment = 0.0

        # Ownership adjustment
        if selected_by_percent > 50.0:
            ownership_adjustment = -0.05
        elif selected_by_percent < 10.0:
            ownership_adjustment = 0.1
        else:
            ownership_adjustment = 0.0

        total_risk = base_risk + performance_adjustment + ownership_adjustment
        return max(0.0, min(1.0, total_risk))

    def _calculate_data_quality(self, data: Dict[str, Any]) -> float:
        """Calculate data quality score"""
        # Check for missing or invalid data
        required_fields = ["total_points", "form", "price", "selected_by_percent"]
        missing_fields = 0

        for field in required_fields:
            if field not in data or data[field] is None:
                missing_fields += 1

        # Calculate quality score (0-1)
        quality_score = 1.0 - (missing_fields / len(required_fields))

        # Additional quality checks
        if data.get("played", 0) == 0:
            quality_score *= 0.5  # Penalty for no games played

        return quality_score

    def _calculate_sample_size_confidence(self, data: Dict[str, Any]) -> float:
        """Calculate confidence based on sample size"""
        played = data.get("played", 1)

        # More games = higher confidence
        if played >= 20:
            confidence = 1.0
        elif played >= 15:
            confidence = 0.9
        elif played >= 10:
            confidence = 0.8
        elif played >= 5:
            confidence = 0.7
        else:
            confidence = 0.5

        return confidence

    def _calculate_score_consistency(self, sub_scores: Dict[str, float]) -> float:
        """Calculate consistency across sub-scores"""
        if not sub_scores:
            return 0.5

        values = list(sub_scores.values())

        # Calculate coefficient of variation
        mean_score = np.mean(values)
        std_score = np.std(values)

        if mean_score == 0:
            return 0.5

        cv = std_score / mean_score

        # Lower CV = higher consistency
        if cv <= 0.2:
            consistency = 1.0
        elif cv <= 0.4:
            consistency = 0.8
        elif cv <= 0.6:
            consistency = 0.6
        else:
            consistency = 0.4

        return consistency

    def get_sub_scores(self, data: Dict[str, Any]) -> Dict[str, float]:
        """Get all sub-scores for analysis"""
        return self._calculate_sub_scores(data)

    def get_score_breakdown(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Get detailed score breakdown for analysis"""
        sub_scores = self._calculate_sub_scores(data)
        base_score = self.calculate_base_score(sub_scores)
        interaction_bonus = self.calculate_interaction_bonus(sub_scores)
        risk_penalty = self.calculate_risk_penalty(data)
        confidence_multiplier = self.calculate_confidence_multiplier(data, sub_scores)

        final_score = (
            base_score + interaction_bonus + risk_penalty
        ) * confidence_multiplier
        final_score = max(0.0, min(15.0, final_score))

        return {
            "sub_scores": sub_scores,
            "base_score": base_score,
            "interaction_bonus": interaction_bonus,
            "risk_penalty": risk_penalty,
            "confidence_multiplier": confidence_multiplier,
            "final_score": final_score,
            "weights": self.sub_score_weights.copy(),
        }
