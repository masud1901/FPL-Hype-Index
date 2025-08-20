"""
Backtesting Engine

This module implements a comprehensive backtesting framework to validate the prediction
engine's performance against historical FPL data.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

from ...optimization.algorithms.transfer_optimizer import TransferOptimizer
from ...scoring.master_score.player_impact_score import PlayerImpactScore
from ...config.scoring_weights import ScoringWeights

logger = logging.getLogger(__name__)


@dataclass
class GameweekResult:
    """Represents the results of a single gameweek"""

    gameweek: int
    squad_points: float
    bench_points: float
    captain_points: float
    transfers_made: int
    transfer_hits: int
    total_points: float
    squad_value: float
    transfers: List[Dict[str, Any]]
    captain_choice: str
    vice_captain_choice: str


@dataclass
class BacktestResult:
    """Represents the complete results of a backtest"""

    start_gameweek: int
    end_gameweek: int
    total_points: float
    average_points_per_gameweek: float
    total_transfers: int
    total_transfer_hits: int
    final_squad_value: float
    gameweek_results: List[GameweekResult]
    performance_metrics: Dict[str, float]
    strategy_config: Dict[str, Any]


class BacktestEngine:
    """
    Comprehensive backtesting framework for validating FPL prediction strategies.

    This engine simulates FPL performance over historical gameweeks, making transfer
    decisions based on the prediction engine's recommendations and calculating the
    resulting points.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the backtesting engine"""
        self.config = config or {}
        self.optimizer = TransferOptimizer(config)
        self.scorer = PlayerImpactScore(config)
        self.weights = ScoringWeights()

        # Backtesting parameters
        self.default_strategy = self.config.get("default_strategy", "balanced")
        self.max_transfers_per_week = self.config.get("max_transfers_per_week", 2)
        self.min_confidence_threshold = self.config.get("min_confidence", 0.6)
        self.max_risk_threshold = self.config.get("max_risk", 0.4)

    def run_backtest(
        self,
        start_gameweek: int,
        end_gameweek: int,
        initial_squad: List[Dict[str, Any]],
        strategy_config: Optional[Dict[str, Any]] = None,
        available_players: Optional[List[Dict[str, Any]]] = None,
    ) -> BacktestResult:
        """
        Run a complete backtest simulation over the specified gameweek range.

        Args:
            start_gameweek: Starting gameweek number
            end_gameweek: Ending gameweek number
            initial_squad: Initial squad to start with
            strategy_config: Strategy configuration for transfer decisions
            available_players: Pool of available players for transfers

        Returns:
            Complete backtest results with performance metrics
        """
        logger.info(f"Starting backtest from GW{start_gameweek} to GW{end_gameweek}")

        # Initialize strategy configuration
        strategy_config = strategy_config or self._get_default_strategy_config()

        # Initialize tracking variables
        current_squad = initial_squad.copy()
        gameweek_results = []
        total_points = 0.0
        total_transfers = 0
        total_transfer_hits = 0

        # Run simulation gameweek by gameweek
        for gameweek in range(start_gameweek, end_gameweek + 1):
            logger.info(f"Processing Gameweek {gameweek}")

            # Get actual gameweek results
            gameweek_data = self._get_gameweek_data(gameweek)

            # Calculate points for current squad
            squad_points, bench_points, captain_points = (
                self._calculate_gameweek_points(current_squad, gameweek_data)
            )

            # Make transfer decisions based on strategy
            transfers = self._make_transfer_decisions(
                current_squad, gameweek, strategy_config, available_players
            )

            # Apply transfers and calculate hits
            transfer_hits = self._calculate_transfer_hits(len(transfers))
            current_squad = self._apply_transfers(current_squad, transfers)

            # Calculate total points for this gameweek
            gameweek_total = (
                squad_points + bench_points + captain_points - transfer_hits
            )

            # Record gameweek result
            gameweek_result = GameweekResult(
                gameweek=gameweek,
                squad_points=squad_points,
                bench_points=bench_points,
                captain_points=captain_points,
                transfers_made=len(transfers),
                transfer_hits=transfer_hits,
                total_points=gameweek_total,
                squad_value=self._calculate_squad_value(current_squad),
                transfers=transfers,
                captain_choice=self._get_captain_choice(current_squad),
                vice_captain_choice=self._get_vice_captain_choice(current_squad),
            )

            gameweek_results.append(gameweek_result)

            # Update totals
            total_points += gameweek_total
            total_transfers += len(transfers)
            total_transfer_hits += transfer_hits

            logger.info(
                f"GW{gameweek}: {gameweek_total:.1f} points "
                f"({squad_points:.1f} + {bench_points:.1f} + {captain_points:.1f} - {transfer_hits})"
            )

        # Calculate performance metrics
        performance_metrics = self._calculate_performance_metrics(
            gameweek_results, total_points, total_transfers, total_transfer_hits
        )

        # Create final result
        result = BacktestResult(
            start_gameweek=start_gameweek,
            end_gameweek=end_gameweek,
            total_points=total_points,
            average_points_per_gameweek=total_points
            / (end_gameweek - start_gameweek + 1),
            total_transfers=total_transfers,
            total_transfer_hits=total_transfer_hits,
            final_squad_value=self._calculate_squad_value(current_squad),
            gameweek_results=gameweek_results,
            performance_metrics=performance_metrics,
            strategy_config=strategy_config,
        )

        logger.info(
            f"Backtest completed. Total points: {total_points:.1f}, "
            f"Average: {result.average_points_per_gameweek:.1f}"
        )

        return result

    def _get_default_strategy_config(self) -> Dict[str, Any]:
        """Get default strategy configuration"""
        return {
            "strategy": "balanced",
            "max_transfers_per_week": self.max_transfers_per_week,
            "min_confidence_threshold": self.min_confidence_threshold,
            "max_risk_threshold": self.max_risk_threshold,
            "use_wildcard": False,
            "use_free_hit": False,
            "use_triple_captain": False,
            "use_bench_boost": False,
        }

    def _get_gameweek_data(self, gameweek: int) -> Dict[str, Any]:
        """
        Get actual gameweek data for scoring calculations.

        In a real implementation, this would load from the database.
        For now, we'll simulate realistic gameweek results.
        """
        # Simulate gameweek data - in reality this would come from the database
        gameweek_data = {
            "gameweek": gameweek,
            "player_performances": {},
            "fixtures": [],
            "deadline": datetime.now() + timedelta(days=7),
        }

        # Generate realistic player performances
        # This is a simplified simulation - real implementation would use actual data
        for i in range(1, 101):  # Simulate 100 players
            player_id = f"player_{i}"

            # Simulate performance based on position and form
            position = ["GK", "DEF", "MID", "FWD"][i % 4]

            if position == "GK":
                points = np.random.normal(4.0, 2.0)  # GK typically score 2-6 points
                points = max(0, min(10, points))  # Cap between 0-10
            elif position == "DEF":
                points = np.random.normal(5.0, 3.0)  # DEF typically score 2-8 points
                points = max(0, min(12, points))
            elif position == "MID":
                points = np.random.normal(6.0, 4.0)  # MID typically score 2-10 points
                points = max(0, min(15, points))
            else:  # FWD
                points = np.random.normal(5.5, 4.5)  # FWD typically score 2-12 points
                points = max(0, min(15, points))

            gameweek_data["player_performances"][player_id] = {
                "points": points,
                "minutes": np.random.choice([0, 45, 60, 90], p=[0.1, 0.1, 0.1, 0.7]),
                "goals": int(points // 4) if position in ["MID", "FWD"] else 0,
                "assists": int((points % 4) // 3) if position in ["MID", "FWD"] else 0,
                "clean_sheet": points > 4 if position in ["GK", "DEF"] else False,
                "bonus": int(points // 3) if points > 6 else 0,
            }

        return gameweek_data

    def _calculate_gameweek_points(
        self, squad: List[Dict[str, Any]], gameweek_data: Dict[str, Any]
    ) -> Tuple[float, float, float]:
        """
        Calculate points for the current squad in a gameweek.

        Returns:
            Tuple of (squad_points, bench_points, captain_points)
        """
        squad_points = 0.0
        bench_points = 0.0
        captain_points = 0.0

        # Sort squad by expected points (simplified captain selection)
        squad_with_scores = []
        for player in squad:
            # Get player performance from gameweek data
            player_id = player.get("id", "unknown")
            performance = gameweek_data["player_performances"].get(player_id, {})
            points = performance.get("points", 0.0)

            squad_with_scores.append(
                {
                    "player": player,
                    "points": points,
                    "position": player.get("position", "Unknown"),
                }
            )

        # Sort by points for captain selection
        squad_with_scores.sort(key=lambda x: x["points"], reverse=True)

        # Calculate squad points (top 11 players)
        for i, player_score in enumerate(squad_with_scores):
            if i < 11:  # Starting 11
                points = player_score["points"]
                squad_points += points

                # Captain gets double points
                if i == 0:  # Highest scoring player is captain
                    captain_points = points
                    squad_points += points  # Add captain bonus
                elif i == 1:  # Second highest is vice captain
                    if captain_points == 0:  # If captain didn't play
                        captain_points = points
                        squad_points += points
            else:  # Bench players
                bench_points += player_score["points"]

        return squad_points, bench_points, captain_points

    def _make_transfer_decisions(
        self,
        current_squad: List[Dict[str, Any]],
        gameweek: int,
        strategy_config: Dict[str, Any],
        available_players: Optional[List[Dict[str, Any]]],
    ) -> List[Dict[str, Any]]:
        """
        Make transfer decisions based on the strategy configuration.

        Returns:
            List of transfer decisions
        """
        # Skip transfers if we've reached the limit
        if strategy_config.get("max_transfers_per_week", 2) <= 0:
            return []

        # Get available players if not provided
        if available_players is None:
            available_players = self._get_available_players()

        # Get transfer recommendations
        try:
            recommendations = self.optimizer.optimize_transfers(
                current_squad=current_squad,
                available_players=available_players,
                budget=2.0,  # Assume 2.0m budget
                transfers_available=strategy_config.get("max_transfers_per_week", 2),
                strategy=strategy_config.get("strategy", "balanced"),
            )

            # Apply confidence and risk filters
            filtered_recommendations = []
            for rec in recommendations:
                if rec.total_confidence >= strategy_config.get(
                    "min_confidence_threshold", 0.6
                ) and rec.total_risk <= strategy_config.get("max_risk_threshold", 0.4):
                    filtered_recommendations.append(rec)

            # Return transfers from the best recommendation
            if filtered_recommendations:
                best_rec = filtered_recommendations[0]
                return [transfer.__dict__ for transfer in best_rec.transfers]

        except Exception as e:
            logger.warning(f"Error making transfer decisions for GW{gameweek}: {e}")

        return []

    def _get_available_players(self) -> List[Dict[str, Any]]:
        """Get pool of available players for transfers"""
        # In a real implementation, this would load from the database
        # For now, return a simplified list
        available_players = []

        # Generate some sample players
        teams = [
            "Arsenal",
            "Chelsea",
            "Liverpool",
            "Man City",
            "Man United",
            "Tottenham",
            "Newcastle",
            "Aston Villa",
            "Brighton",
            "West Ham",
        ]

        positions = ["GK", "DEF", "MID", "FWD"]

        for i in range(50):  # 50 available players
            position = positions[i % 4]
            team = teams[i % len(teams)]

            player = {
                "id": f"available_{i}",
                "name": f"Player {i}",
                "position": position,
                "team": team,
                "price": 5.0 + (i % 10) * 0.5,
                "form": 5.0 + np.random.normal(0, 1.5),
                "total_points": 50 + i * 2,
                "minutes_played": 2000 + i * 50,
                "injury_history": [],
                "age": 25 + (i % 10),
                "rotation_risk": i % 5 == 0,
            }

            # Add position-specific stats
            if position == "GK":
                player.update(
                    {
                        "clean_sheets": 5 + i % 5,
                        "saves": 50 + i * 3,
                        "goals_conceded": 20 + i % 10,
                    }
                )
            elif position == "DEF":
                player.update(
                    {"clean_sheets": 4 + i % 4, "goals": i % 3, "assists": i % 4}
                )
            elif position == "MID":
                player.update({"goals": 3 + i % 5, "assists": 4 + i % 6})
            else:  # FWD
                player.update({"goals": 5 + i % 8, "assists": 2 + i % 4})

            available_players.append(player)

        return available_players

    def _apply_transfers(
        self, current_squad: List[Dict[str, Any]], transfers: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Apply transfers to the current squad"""
        new_squad = current_squad.copy()

        for transfer in transfers:
            player_out = transfer.get("player_out", {})
            player_in = transfer.get("player_in", {})

            # Remove player out
            new_squad = [p for p in new_squad if p.get("id") != player_out.get("id")]

            # Add player in
            new_squad.append(player_in)

        return new_squad

    def _calculate_transfer_hits(self, num_transfers: int) -> int:
        """Calculate transfer hits (penalty points)"""
        if num_transfers <= 1:
            return 0
        else:
            return (num_transfers - 1) * 4  # 4 points per extra transfer

    def _calculate_squad_value(self, squad: List[Dict[str, Any]]) -> float:
        """Calculate total squad value"""
        return sum(player.get("price", 0) for player in squad)

    def _get_captain_choice(self, squad: List[Dict[str, Any]]) -> str:
        """Get captain choice (simplified - highest scoring player)"""
        if not squad:
            return "None"

        # Sort by form/expected points
        sorted_squad = sorted(squad, key=lambda p: p.get("form", 0), reverse=True)
        return sorted_squad[0].get("name", "Unknown")

    def _get_vice_captain_choice(self, squad: List[Dict[str, Any]]) -> str:
        """Get vice captain choice (second highest scoring player)"""
        if len(squad) < 2:
            return "None"

        # Sort by form/expected points
        sorted_squad = sorted(squad, key=lambda p: p.get("form", 0), reverse=True)
        return sorted_squad[1].get("name", "Unknown")

    def _calculate_performance_metrics(
        self,
        gameweek_results: List[GameweekResult],
        total_points: float,
        total_transfers: int,
        total_transfer_hits: int,
    ) -> Dict[str, float]:
        """Calculate comprehensive performance metrics"""

        if not gameweek_results:
            return {}

        # Basic metrics
        num_gameweeks = len(gameweek_results)
        avg_points = total_points / num_gameweeks

        # Consistency metrics
        points_list = [gw.total_points for gw in gameweek_results]
        points_std = np.std(points_list)
        consistency_score = 1.0 / (1.0 + points_std)  # Higher is better

        # Transfer efficiency
        transfer_efficiency = 0.0
        if total_transfers > 0:
            transfer_efficiency = (total_points - total_transfer_hits) / total_transfers

        # Streak analysis
        positive_weeks = sum(
            1 for gw in gameweek_results if gw.total_points > avg_points
        )
        consistency_ratio = positive_weeks / num_gameweeks

        # Value for money
        final_squad_value = gameweek_results[-1].squad_value if gameweek_results else 0
        value_efficiency = (
            total_points / final_squad_value if final_squad_value > 0 else 0
        )

        metrics = {
            "total_points": total_points,
            "average_points_per_gameweek": avg_points,
            "total_transfers": total_transfers,
            "total_transfer_hits": total_transfer_hits,
            "transfer_efficiency": transfer_efficiency,
            "consistency_score": consistency_score,
            "consistency_ratio": consistency_ratio,
            "value_efficiency": value_efficiency,
            "points_standard_deviation": points_std,
            "best_gameweek": max(points_list),
            "worst_gameweek": min(points_list),
            "positive_weeks": positive_weeks,
            "negative_weeks": num_gameweeks - positive_weeks,
        }

        return metrics

    def compare_strategies(
        self,
        start_gameweek: int,
        end_gameweek: int,
        initial_squad: List[Dict[str, Any]],
        strategies: List[Dict[str, Any]],
        available_players: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, BacktestResult]:
        """
        Compare multiple strategies against each other.

        Args:
            strategies: List of strategy configurations to compare

        Returns:
            Dictionary mapping strategy names to their results
        """
        results = {}

        for i, strategy in enumerate(strategies):
            strategy_name = strategy.get("name", f"Strategy_{i+1}")
            logger.info(f"Testing strategy: {strategy_name}")

            try:
                result = self.run_backtest(
                    start_gameweek=start_gameweek,
                    end_gameweek=end_gameweek,
                    initial_squad=initial_squad,
                    strategy_config=strategy,
                    available_players=available_players,
                )
                results[strategy_name] = result

            except Exception as e:
                logger.error(f"Error testing strategy {strategy_name}: {e}")

        return results

    def generate_backtest_report(self, result: BacktestResult) -> str:
        """Generate a comprehensive backtest report"""

        report = []
        report.append("=" * 80)
        report.append("FPL PREDICTION ENGINE BACKTEST REPORT")
        report.append("=" * 80)
        report.append("")

        # Summary
        report.append("SUMMARY")
        report.append("-" * 40)
        report.append(f"Period: GW{result.start_gameweek} - GW{result.end_gameweek}")
        report.append(f"Total Points: {result.total_points:.1f}")
        report.append(
            f"Average Points per Gameweek: {result.average_points_per_gameweek:.1f}"
        )
        report.append(f"Total Transfers: {result.total_transfers}")
        report.append(f"Total Transfer Hits: {result.total_transfer_hits}")
        report.append(f"Final Squad Value: £{result.final_squad_value:.1f}m")
        report.append("")

        # Performance Metrics
        report.append("PERFORMANCE METRICS")
        report.append("-" * 40)
        for metric, value in result.performance_metrics.items():
            if isinstance(value, float):
                report.append(f"{metric.replace('_', ' ').title()}: {value:.3f}")
            else:
                report.append(f"{metric.replace('_', ' ').title()}: {value}")
        report.append("")

        # Gameweek Breakdown
        report.append("GAMEWEEK BREAKDOWN")
        report.append("-" * 40)
        report.append(
            f"{'GW':<4} {'Points':<8} {'Squad':<8} {'Bench':<8} {'Captain':<8} {'Transfers':<10}"
        )
        report.append("-" * 50)

        for gw_result in result.gameweek_results:
            report.append(
                f"{gw_result.gameweek:<4} {gw_result.total_points:<8.1f} "
                f"{gw_result.squad_points:<8.1f} {gw_result.bench_points:<8.1f} "
                f"{gw_result.captain_points:<8.1f} {gw_result.transfers_made:<10}"
            )

        report.append("")
        report.append("=" * 80)

        return "\n".join(report)
