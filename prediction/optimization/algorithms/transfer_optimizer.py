"""
Transfer Optimizer Algorithm

This module implements the core transfer optimization logic that finds the best
transfer combinations while respecting FPL constraints and maximizing expected points.
"""

import itertools
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import pandas as pd

from ..constraints.fpl_constraints import (
    FPLConstraintChecker,
    SquadConstraints,
    TransferConstraints,
)
from ...scoring.master_score.player_impact_score import PlayerImpactScore
from ...config.scoring_weights import ScoringWeights

logger = logging.getLogger(__name__)


@dataclass
class TransferRecommendation:
    """Represents a single transfer recommendation"""

    player_out: Dict[str, Any]
    player_in: Dict[str, Any]
    expected_points_gain: float
    confidence_score: float
    risk_score: float
    reasoning: str


@dataclass
class TransferCombination:
    """Represents a combination of transfers"""

    transfers: List[TransferRecommendation]
    total_expected_gain: float
    total_confidence: float
    total_risk: float
    budget_impact: float
    formation_valid: bool
    reasoning: str


class TransferOptimizer:
    """
    Core transfer optimization engine that finds the best transfer combinations
    while respecting FPL constraints and maximizing expected points.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the transfer optimizer"""
        self.config = config or {}
        self.constraints = FPLConstraintChecker(
            SquadConstraints(), TransferConstraints()
        )
        self.scorer = PlayerImpactScore(config)
        self.weights = ScoringWeights()

        # Optimization parameters
        self.max_combinations = self.config.get("max_combinations", 1000)
        self.min_confidence_threshold = self.config.get("min_confidence", 0.6)
        self.max_risk_threshold = self.config.get("max_risk", 0.4)

    def optimize_transfers(
        self,
        current_squad: List[Dict[str, Any]],
        available_players: List[Dict[str, Any]],
        budget: float,
        transfers_available: int,
        strategy: str = "balanced",
    ) -> List[TransferCombination]:
        """
        Find optimal transfer combinations for the current squad.

        Args:
            current_squad: Current squad players
            available_players: Pool of available players to transfer in
            budget: Available budget for transfers
            transfers_available: Number of transfers available
            strategy: Optimization strategy ('aggressive', 'balanced', 'conservative')

        Returns:
            List of transfer combinations ranked by expected gain
        """
        logger.info(
            f"Starting transfer optimization with {transfers_available} transfers available"
        )

        # Calculate current squad scores
        current_scores = self._calculate_squad_scores(current_squad)

        # Get potential transfer targets
        transfer_targets = self._get_transfer_targets(available_players, strategy)

        # Generate valid transfer combinations
        valid_combinations = self._generate_valid_combinations(
            current_squad, transfer_targets, budget, transfers_available
        )

        # Score each combination
        scored_combinations = []
        for combination in valid_combinations:
            score_result = self._score_combination(
                combination, current_squad, current_scores
            )
            if score_result:
                scored_combinations.append(score_result)

        # Sort by expected gain and apply strategy filters
        scored_combinations.sort(key=lambda x: x.total_expected_gain, reverse=True)

        # Apply strategy-specific filtering
        filtered_combinations = self._apply_strategy_filter(
            scored_combinations, strategy
        )

        logger.info(
            f"Generated {len(filtered_combinations)} valid transfer combinations"
        )

        return filtered_combinations[:10]  # Return top 10 recommendations

    def _calculate_squad_scores(self, squad: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate current scores for all squad players"""
        scores = {}
        for player in squad:
            try:
                score_result = self.scorer.calculate_score(player)
                scores[player["id"]] = score_result
            except Exception as e:
                logger.warning(
                    f"Failed to calculate score for player {player.get('name', 'Unknown')}: {e}"
                )
                scores[player["id"]] = 0.0
        return scores

    def _get_transfer_targets(
        self, available_players: List[Dict[str, Any]], strategy: str
    ) -> List[Dict[str, Any]]:
        """Filter and rank available players based on strategy"""

        # Calculate scores for all available players
        scored_players = []
        for player in available_players:
            try:
                score_result = self.scorer.calculate_score(player)
                scored_players.append(
                    {
                        **player,
                        "pis_score": score_result,
                        "confidence": 0.8,  # Default confidence
                        "risk_score": self._calculate_risk_score(player),
                    }
                )
            except Exception as e:
                logger.warning(
                    f"Failed to score player {player.get('name', 'Unknown')}: {e}"
                )
                continue

        # Sort by PIS score
        scored_players.sort(key=lambda x: x["pis_score"], reverse=True)

        # Apply strategy-specific filtering
        if strategy == "aggressive":
            # Focus on high-ceiling players
            filtered_players = [
                p
                for p in scored_players
                if p["pis_score"] > 7.0 and p["confidence"] > 0.7
            ]
        elif strategy == "conservative":
            # Focus on consistent, low-risk players
            filtered_players = [
                p
                for p in scored_players
                if p["risk_score"] < 0.3 and p["confidence"] > 0.8
            ]
        else:  # balanced
            # Balance between performance and risk
            filtered_players = [
                p
                for p in scored_players
                if p["pis_score"] > 6.0 and p["risk_score"] < 0.5
            ]

        return filtered_players[:50]  # Limit to top 50 targets

    def _generate_valid_combinations(
        self,
        current_squad: List[Dict[str, Any]],
        transfer_targets: List[Dict[str, Any]],
        budget: float,
        transfers_available: int,
    ) -> List[List[Dict[str, Any]]]:
        """Generate all valid transfer combinations"""

        valid_combinations = []

        # Generate combinations for different transfer counts
        for transfer_count in range(
            1, min(transfers_available + 1, 4)
        ):  # Max 3 transfers at once

            # Get all possible transfer combinations
            transfer_combinations = list(
                itertools.combinations(transfer_targets, transfer_count)
            )

            # Limit combinations to prevent explosion
            if len(transfer_combinations) > self.max_combinations:
                transfer_combinations = transfer_combinations[: self.max_combinations]

            for combination in transfer_combinations:
                if self._is_valid_combination(current_squad, list(combination), budget):
                    valid_combinations.append(list(combination))

        return valid_combinations

    def _is_valid_combination(
        self,
        current_squad: List[Dict[str, Any]],
        transfers: List[Dict[str, Any]],
        budget: float,
    ) -> bool:
        """Check if a transfer combination is valid"""

        # Check budget constraint
        total_cost = sum(t.get("price", 0) for t in transfers)
        if total_cost > budget:
            return False

        # Check formation constraint
        if not self.constraints.check_formation(current_squad, transfers):
            return False

        # Check team constraint
        if not self.constraints.check_team_limits(current_squad, transfers):
            return False

        # Check position balance
        if not self.constraints.check_position_balance(current_squad, transfers):
            return False

        return True

    def _score_combination(
        self,
        transfers: List[Dict[str, Any]],
        current_squad: List[Dict[str, Any]],
        current_scores: Dict[str, float],
    ) -> Optional[TransferCombination]:
        """Score a transfer combination"""

        try:
            # Create transfer recommendations
            transfer_recs = []
            total_gain = 0.0
            total_confidence = 0.0
            total_risk = 0.0
            budget_impact = 0.0

            for transfer in transfers:
                # Find player to transfer out (simplified - could be more sophisticated)
                player_out = self._find_best_player_to_transfer_out(
                    current_squad, transfer
                )

                if not player_out:
                    continue

                # Calculate expected gain
                player_out_score = current_scores.get(player_out["id"], 0.0)
                player_in_score = transfer["pis_score"]
                expected_gain = player_in_score - player_out_score

                # Calculate confidence and risk
                confidence = transfer.get("confidence", 0.5)
                risk_score = transfer.get("risk_score", 0.5)

                # Create transfer recommendation
                rec = TransferRecommendation(
                    player_out=player_out,
                    player_in=transfer,
                    expected_points_gain=expected_gain,
                    confidence_score=confidence,
                    risk_score=risk_score,
                    reasoning=self._generate_transfer_reasoning(
                        player_out, transfer, expected_gain
                    ),
                )

                transfer_recs.append(rec)
                total_gain += expected_gain
                total_confidence += confidence
                total_risk += risk_score
                budget_impact += transfer.get("price", 0) - player_out.get("price", 0)

            if not transfer_recs:
                return None

            # Create combination
            combination = TransferCombination(
                transfers=transfer_recs,
                total_expected_gain=total_gain,
                total_confidence=total_confidence / len(transfer_recs),
                total_risk=total_risk / len(transfer_recs),
                budget_impact=budget_impact,
                formation_valid=True,  # Already validated
                reasoning=self._generate_combination_reasoning(
                    transfer_recs, total_gain
                ),
            )

            return combination

        except Exception as e:
            logger.error(f"Error scoring transfer combination: {e}")
            return None

    def _find_best_player_to_transfer_out(
        self, current_squad: List[Dict[str, Any]], transfer_in: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Find the best player to transfer out for a given transfer in"""

        # Filter players by position
        same_position_players = [
            p for p in current_squad if p.get("position") == transfer_in.get("position")
        ]

        if not same_position_players:
            return None

        # Find player with lowest score in same position
        worst_player = min(
            same_position_players,
            key=lambda p: p.get("pis_score", 0) if "pis_score" in p else 0,
        )

        return worst_player

    def _calculate_risk_score(self, player: Dict[str, Any]) -> float:
        """Calculate risk score for a player"""

        risk_factors = []

        # Injury history risk
        injury_history = player.get("injury_history", [])
        if len(injury_history) > 2:
            risk_factors.append(0.3)
        elif len(injury_history) > 0:
            risk_factors.append(0.1)

        # Age risk
        age = player.get("age", 25)
        if age > 32:
            risk_factors.append(0.2)
        elif age < 20:
            risk_factors.append(0.1)

        # Rotation risk
        if player.get("rotation_risk", False):
            risk_factors.append(0.2)

        # Fixture congestion risk
        if player.get("fixture_congestion", 0) > 3:
            risk_factors.append(0.1)

        # Calculate total risk (capped at 1.0)
        total_risk = min(sum(risk_factors), 1.0)

        return total_risk

    def _generate_transfer_reasoning(
        self,
        player_out: Dict[str, Any],
        player_in: Dict[str, Any],
        expected_gain: float,
    ) -> str:
        """Generate reasoning for a transfer"""

        reasons = []

        if expected_gain > 2.0:
            reasons.append("Significant points improvement expected")
        elif expected_gain > 0.5:
            reasons.append("Moderate improvement expected")

        # Add position-specific reasoning
        position = player_in.get("position", "Unknown")
        if position == "GK":
            reasons.append("Better save performance and clean sheet potential")
        elif position == "DEF":
            reasons.append("Improved defensive returns and attacking threat")
        elif position == "MID":
            reasons.append("Enhanced creativity and goal threat")
        elif position == "FWD":
            reasons.append("Better finishing and goal-scoring potential")

        return "; ".join(reasons) if reasons else "General improvement"

    def _generate_combination_reasoning(
        self, transfers: List[TransferRecommendation], total_gain: float
    ) -> str:
        """Generate reasoning for a transfer combination"""

        if total_gain > 5.0:
            return "High-impact transfer combination with significant expected gains"
        elif total_gain > 2.0:
            return "Moderate improvement across multiple positions"
        else:
            return "Incremental improvements to squad balance"

    def _apply_strategy_filter(
        self, combinations: List[TransferCombination], strategy: str
    ) -> List[TransferCombination]:
        """Apply strategy-specific filtering to combinations"""

        if strategy == "aggressive":
            # Focus on high-gain, higher-risk combinations
            return [
                c
                for c in combinations
                if c.total_expected_gain > 3.0 and c.total_confidence > 0.6
            ]
        elif strategy == "conservative":
            # Focus on low-risk, consistent combinations
            return [
                c
                for c in combinations
                if c.total_risk < 0.3 and c.total_confidence > 0.8
            ]
        else:  # balanced
            # Balance between gain and risk
            return [
                c
                for c in combinations
                if c.total_expected_gain > 1.0 and c.total_risk < 0.5
            ]

    def get_single_transfer_recommendations(
        self,
        current_squad: List[Dict[str, Any]],
        available_players: List[Dict[str, Any]],
        budget: float,
    ) -> List[TransferRecommendation]:
        """Get single transfer recommendations (simplified version)"""

        # Get transfer targets
        transfer_targets = self._get_transfer_targets(available_players, "balanced")

        recommendations = []

        for target in transfer_targets[:20]:  # Top 20 targets
            player_out = self._find_best_player_to_transfer_out(current_squad, target)

            if player_out:
                # Check budget constraint
                cost_difference = target.get("price", 0) - player_out.get("price", 0)
                if cost_difference <= budget:
                    # Calculate expected gain
                    current_scores = self._calculate_squad_scores(current_squad)
                    player_out_score = current_scores.get(player_out["id"], 0.0)
                    expected_gain = target["pis_score"] - player_out_score

                    if expected_gain > 0.5:  # Only recommend if significant gain
                        rec = TransferRecommendation(
                            player_out=player_out,
                            player_in=target,
                            expected_points_gain=expected_gain,
                            confidence_score=target.get("confidence", 0.5),
                            risk_score=target.get("risk_score", 0.5),
                            reasoning=self._generate_transfer_reasoning(
                                player_out, target, expected_gain
                            ),
                        )
                        recommendations.append(rec)

        # Sort by expected gain
        recommendations.sort(key=lambda x: x.expected_points_gain, reverse=True)

        return recommendations[:5]  # Return top 5
