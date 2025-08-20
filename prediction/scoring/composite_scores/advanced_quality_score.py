"""
Advanced Quality Score

This module contains the Advanced Quality Score (AQS) algorithm that provides
position-specific quality assessment using advanced metrics.
"""

from typing import Dict, Any
import pandas as pd

from ..base.score_base import CompositeScore
from ..position_specific.goalkeeper_score import GoalkeeperScore
from ..position_specific.defender_score import DefenderScore
from ..position_specific.midfielder_score import MidfielderScore
from ..position_specific.forward_score import ForwardScore
from utils.logger import get_logger

logger = get_logger("advanced_quality_score")


class AdvancedQualityScore(CompositeScore):
    """Advanced Quality Score - position-specific quality assessment"""

    description = "Position-specific quality assessment using advanced metrics and Bayesian adjustments"

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)

        # Position-specific scorer instances
        self.position_scorers = {
            "GK": GoalkeeperScore(config.get("goalkeeper_config", {})),
            "DEF": DefenderScore(config.get("defender_config", {})),
            "MID": MidfielderScore(config.get("midfielder_config", {})),
            "FWD": ForwardScore(config.get("forward_config", {})),
        }

        # Quality enhancement factors
        self.bayesian_adjustment = config.get("bayesian_adjustment", True)
        self.sequence_enhancement = config.get("sequence_enhancement", True)
        self.sample_size_threshold = config.get("sample_size_threshold", 5)

        # Prior expectations by position (used for Bayesian adjustment)
        self.position_priors = config.get(
            "position_priors", {"GK": 4.0, "DEF": 4.5, "MID": 5.0, "FWD": 4.5}
        )

    def calculate_score(self, data: Dict[str, Any]) -> float:
        """Calculate Advanced Quality Score for a player"""
        position = data.get("position", "MID").upper()

        # Get base position-specific score
        base_score = self._calculate_position_score(data, position)

        # Apply Bayesian adjustment if enabled
        if self.bayesian_adjustment:
            base_score = self._apply_bayesian_adjustment(base_score, data, position)

        # Apply sequence-based enhancement if enabled
        if self.sequence_enhancement:
            base_score = self._apply_sequence_enhancement(base_score, data)

        # Apply contextual adjustments
        adjusted_score = self._apply_contextual_adjustments(base_score, data)

        return self.normalize_score(adjusted_score)

    def _calculate_position_score(self, data: Dict[str, Any], position: str) -> float:
        """Calculate base position-specific score"""
        if position not in self.position_scorers:
            logger.warning(f"Unknown position: {position}, using MID scorer")
            position = "MID"

        scorer = self.position_scorers[position]
        return scorer.calculate_with_validation(data)

    def _apply_bayesian_adjustment(
        self, base_score: float, data: Dict[str, Any], position: str
    ) -> float:
        """Apply Bayesian adjustment to account for sample size"""
        played = data.get("played", 1)

        # If sample size is large enough, trust the data more
        if played >= self.sample_size_threshold:
            confidence = min(1.0, played / (self.sample_size_threshold * 2))
        else:
            confidence = played / self.sample_size_threshold

        # Get prior expectation for position
        prior = self.position_priors.get(position, 5.0)

        # Bayesian weighted average
        adjusted_score = (confidence * base_score) + ((1 - confidence) * prior)

        logger.debug(
            f"Bayesian adjustment: {base_score:.2f} -> {adjusted_score:.2f} (confidence: {confidence:.2f})"
        )

        return adjusted_score

    def _apply_sequence_enhancement(
        self, base_score: float, data: Dict[str, Any]
    ) -> float:
        """Apply sequence-based enhancement for buildup play value"""
        # Enhanced xG concept - value buildup play and pre-shot actions

        # Use creativity and influence as proxies for buildup contribution
        creativity = data.get("creativity", 0.0)
        influence = data.get("influence", 0.0)
        assists = data.get("assists", 0)
        played = data.get("played", 1)

        if played == 0:
            return base_score

        # Calculate buildup contribution score
        creativity_per_game = creativity / played
        influence_per_game = influence / played
        assists_per_game = assists / played

        # Sequence enhancement based on buildup metrics
        buildup_score = (
            min(2.0, creativity_per_game / 50.0)  # Up to 2 points from creativity
            + min(1.5, influence_per_game / 100.0)  # Up to 1.5 points from influence
            + min(1.0, assists_per_game * 5.0)  # Up to 1 point from assists
        )

        # Apply enhancement as a percentage boost
        enhancement_factor = 1.0 + (buildup_score / 20.0)  # Up to 22.5% boost

        enhanced_score = base_score * enhancement_factor

        logger.debug(
            f"Sequence enhancement: {base_score:.2f} -> {enhanced_score:.2f} (factor: {enhancement_factor:.3f})"
        )

        return enhanced_score

    def _apply_contextual_adjustments(
        self, base_score: float, data: Dict[str, Any]
    ) -> float:
        """Apply contextual adjustments based on team and situation"""
        # Team strength adjustment
        team_strength = data.get("team_strength", 50.0)

        # Players in stronger teams might have inflated stats
        if team_strength > 70.0:
            # Slight penalty for strong team inflation
            team_adjustment = -0.1 * ((team_strength - 70.0) / 30.0)
        elif team_strength < 30.0:
            # Bonus for performing well in weak team
            team_adjustment = 0.15 * ((30.0 - team_strength) / 30.0)
        else:
            team_adjustment = 0.0

        # Minutes played adjustment (penalize limited playing time)
        total_points = data.get("total_points", 0)
        played = data.get("played", 1)

        if played > 0:
            points_per_game = total_points / played
            # If points per game is very low, might indicate limited minutes
            if points_per_game < 2.0:
                minutes_penalty = -0.5
            elif points_per_game < 3.0:
                minutes_penalty = -0.2
            else:
                minutes_penalty = 0.0
        else:
            minutes_penalty = -1.0

        adjusted_score = base_score + team_adjustment + minutes_penalty

        logger.debug(
            f"Contextual adjustment: {base_score:.2f} -> {adjusted_score:.2f} "
            f"(team: {team_adjustment:.2f}, minutes: {minutes_penalty:.2f})"
        )

        return adjusted_score


class PositionSpecificQualityScore(CompositeScore):
    """Position-specific quality score with detailed breakdown"""

    description = (
        "Detailed position-specific quality assessment with component breakdown"
    )

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)

        # Component weights by position
        self.position_weights = config.get(
            "position_weights",
            {
                "GK": {
                    "save_performance": 0.4,
                    "clean_sheet_potential": 0.3,
                    "distribution": 0.2,
                    "bonus_potential": 0.1,
                },
                "DEF": {
                    "clean_sheet_potential": 0.4,
                    "attacking_returns": 0.3,
                    "defensive_actions": 0.2,
                    "bonus_potential": 0.1,
                },
                "MID": {
                    "goal_threat": 0.3,
                    "creativity": 0.3,
                    "defensive_contribution": 0.2,
                    "bonus_potential": 0.2,
                },
                "FWD": {
                    "finishing": 0.4,
                    "goal_threat": 0.3,
                    "assist_potential": 0.2,
                    "bonus_potential": 0.1,
                },
            },
        )

    def calculate_score(self, data: Dict[str, Any]) -> float:
        """Calculate position-specific quality score with breakdown"""
        position = data.get("position", "MID").upper()

        if position == "GK":
            return self._calculate_goalkeeper_quality(data)
        elif position == "DEF":
            return self._calculate_defender_quality(data)
        elif position == "MID":
            return self._calculate_midfielder_quality(data)
        elif position == "FWD":
            return self._calculate_forward_quality(data)
        else:
            return self._calculate_midfielder_quality(data)  # Default

    def _calculate_goalkeeper_quality(self, data: Dict[str, Any]) -> float:
        """Calculate goalkeeper quality with detailed breakdown"""
        weights = self.position_weights["GK"]

        # Save performance
        saves = data.get("saves", 0)
        played = max(data.get("played", 1), 1)
        saves_per_game = saves / played
        save_score = min(10.0, saves_per_game * 2.0)  # 5 saves per game = 10

        # Clean sheet potential
        clean_sheets = data.get("clean_sheets", 0)
        cs_rate = clean_sheets / played
        cs_score = min(10.0, cs_rate * 20.0)  # 50% CS rate = 10

        # Distribution (use influence as proxy)
        influence = data.get("influence", 0.0)
        dist_score = min(10.0, (influence / played) / 20.0)

        # Bonus potential
        bonus = data.get("bonus", 0)
        bonus_score = min(10.0, (bonus / played) * 10.0)

        # Weighted combination
        quality_score = (
            save_score * weights["save_performance"]
            + cs_score * weights["clean_sheet_potential"]
            + dist_score * weights["distribution"]
            + bonus_score * weights["bonus_potential"]
        )

        return quality_score

    def _calculate_defender_quality(self, data: Dict[str, Any]) -> float:
        """Calculate defender quality with detailed breakdown"""
        weights = self.position_weights["DEF"]

        played = max(data.get("played", 1), 1)

        # Clean sheet potential
        clean_sheets = data.get("clean_sheets", 0)
        cs_rate = clean_sheets / played
        cs_score = min(10.0, cs_rate * 15.0)  # 67% CS rate = 10

        # Attacking returns
        goals = data.get("goals_scored", 0)
        assists = data.get("assists", 0)
        attacking_returns = (goals * 2) + assists  # Goals worth more
        attack_score = min(10.0, attacking_returns * 1.0)

        # Defensive actions (use influence as proxy)
        influence = data.get("influence", 0.0)
        def_score = min(10.0, (influence / played) / 15.0)

        # Bonus potential
        bonus = data.get("bonus", 0)
        bonus_score = min(10.0, (bonus / played) * 20.0)

        # Weighted combination
        quality_score = (
            cs_score * weights["clean_sheet_potential"]
            + attack_score * weights["attacking_returns"]
            + def_score * weights["defensive_actions"]
            + bonus_score * weights["bonus_potential"]
        )

        return quality_score

    def _calculate_midfielder_quality(self, data: Dict[str, Any]) -> float:
        """Calculate midfielder quality with detailed breakdown"""
        weights = self.position_weights["MID"]

        played = max(data.get("played", 1), 1)

        # Goal threat
        goals = data.get("goals_scored", 0)
        threat = data.get("threat", 0.0)
        goal_score = min(10.0, goals * 1.0 + (threat / played) / 30.0)

        # Creativity
        assists = data.get("assists", 0)
        creativity = data.get("creativity", 0.0)
        creativity_score = min(10.0, assists * 0.8 + (creativity / played) / 25.0)

        # Defensive contribution
        influence = data.get("influence", 0.0)
        def_score = min(10.0, (influence / played) / 20.0)

        # Bonus potential
        bonus = data.get("bonus", 0)
        bonus_score = min(10.0, (bonus / played) * 25.0)

        # Weighted combination
        quality_score = (
            goal_score * weights["goal_threat"]
            + creativity_score * weights["creativity"]
            + def_score * weights["defensive_contribution"]
            + bonus_score * weights["bonus_potential"]
        )

        return quality_score

    def _calculate_forward_quality(self, data: Dict[str, Any]) -> float:
        """Calculate forward quality with detailed breakdown"""
        weights = self.position_weights["FWD"]

        played = max(data.get("played", 1), 1)

        # Finishing
        goals = data.get("goals_scored", 0)
        finishing_score = min(10.0, goals * 0.5)  # 20 goals = 10

        # Goal threat
        threat = data.get("threat", 0.0)
        threat_score = min(10.0, (threat / played) / 25.0)

        # Assist potential
        assists = data.get("assists", 0)
        assist_score = min(10.0, assists * 1.0)

        # Bonus potential
        bonus = data.get("bonus", 0)
        bonus_score = min(10.0, (bonus / played) * 30.0)

        # Weighted combination
        quality_score = (
            finishing_score * weights["finishing"]
            + threat_score * weights["goal_threat"]
            + assist_score * weights["assist_potential"]
            + bonus_score * weights["bonus_potential"]
        )

        return quality_score
