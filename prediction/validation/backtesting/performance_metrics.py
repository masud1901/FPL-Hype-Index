"""
Performance Metrics Calculator

This module provides comprehensive performance analysis for backtest results,
including correlation metrics, precision metrics, and calibration scores.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
import pandas as pd
from scipy import stats
from sklearn.metrics import mean_squared_error, mean_absolute_error

logger = logging.getLogger(__name__)


class PerformanceMetrics:
    """
    Comprehensive performance metrics calculator for FPL prediction validation.

    This class provides various metrics to evaluate the performance of the prediction
    engine, including correlation analysis, precision metrics, and calibration scores.
    """

    def __init__(self):
        """Initialize the performance metrics calculator"""
        pass

    def calculate_all_metrics(
        self,
        predicted_scores: List[float],
        actual_points: List[float],
        player_names: Optional[List[str]] = None,
        gameweeks: Optional[List[int]] = None,
    ) -> Dict[str, float]:
        """
        Calculate all performance metrics for the prediction model.

        Args:
            predicted_scores: List of predicted Player Impact Scores
            actual_points: List of actual FPL points scored
            player_names: Optional list of player names for detailed analysis
            gameweeks: Optional list of gameweek numbers

        Returns:
            Dictionary containing all calculated metrics
        """
        if len(predicted_scores) != len(actual_points):
            raise ValueError(
                "Predicted scores and actual points must have the same length"
            )

        if not predicted_scores or not actual_points:
            return {}

        metrics = {}

        # Basic correlation metrics
        metrics.update(
            self._calculate_correlation_metrics(predicted_scores, actual_points)
        )

        # Precision metrics
        metrics.update(
            self._calculate_precision_metrics(predicted_scores, actual_points)
        )

        # Calibration metrics
        metrics.update(
            self._calculate_calibration_metrics(predicted_scores, actual_points)
        )

        # Error metrics
        metrics.update(self._calculate_error_metrics(predicted_scores, actual_points))

        # Ranking metrics
        metrics.update(self._calculate_ranking_metrics(predicted_scores, actual_points))

        # Position-specific metrics
        if player_names:
            metrics.update(
                self._calculate_position_metrics(
                    predicted_scores, actual_points, player_names
                )
            )

        return metrics

    def _calculate_correlation_metrics(
        self, predicted_scores: List[float], actual_points: List[float]
    ) -> Dict[str, float]:
        """Calculate correlation-based metrics"""

        # Convert to numpy arrays
        pred = np.array(predicted_scores)
        actual = np.array(actual_points)

        # Remove any NaN values
        valid_mask = ~(np.isnan(pred) | np.isnan(actual))
        pred_clean = pred[valid_mask]
        actual_clean = actual[valid_mask]

        if len(pred_clean) < 2:
            return {}

        metrics = {}

        # Pearson correlation
        try:
            pearson_corr, pearson_p = stats.pearsonr(pred_clean, actual_clean)
            metrics["pearson_correlation"] = pearson_corr
            metrics["pearson_p_value"] = pearson_p
        except Exception as e:
            logger.warning(f"Error calculating Pearson correlation: {e}")
            metrics["pearson_correlation"] = 0.0
            metrics["pearson_p_value"] = 1.0

        # Spearman correlation (rank correlation)
        try:
            spearman_corr, spearman_p = stats.spearmanr(pred_clean, actual_clean)
            metrics["spearman_correlation"] = spearman_corr
            metrics["spearman_p_value"] = spearman_p
        except Exception as e:
            logger.warning(f"Error calculating Spearman correlation: {e}")
            metrics["spearman_correlation"] = 0.0
            metrics["spearman_p_value"] = 1.0

        # Kendall's tau
        try:
            kendall_tau, kendall_p = stats.kendalltau(pred_clean, actual_clean)
            metrics["kendall_tau"] = kendall_tau
            metrics["kendall_p_value"] = kendall_p
        except Exception as e:
            logger.warning(f"Error calculating Kendall's tau: {e}")
            metrics["kendall_tau"] = 0.0
            metrics["kendall_p_value"] = 1.0

        return metrics

    def _calculate_precision_metrics(
        self, predicted_scores: List[float], actual_points: List[float]
    ) -> Dict[str, float]:
        """Calculate precision-based metrics"""

        # Convert to numpy arrays
        pred = np.array(predicted_scores)
        actual = np.array(actual_points)

        # Remove any NaN values
        valid_mask = ~(np.isnan(pred) | np.isnan(actual))
        pred_clean = pred[valid_mask]
        actual_clean = actual[valid_mask]

        if len(pred_clean) < 10:
            return {}

        metrics = {}

        # Top-N precision metrics
        for n in [5, 10, 20]:
            try:
                # Get top N predicted players
                top_n_indices = np.argsort(pred_clean)[-n:]

                # Get actual top N players
                actual_top_n_indices = np.argsort(actual_clean)[-n:]

                # Calculate overlap
                overlap = len(set(top_n_indices) & set(actual_top_n_indices))
                precision = overlap / n

                metrics[f"top_{n}_precision"] = precision
                metrics[f"top_{n}_overlap"] = overlap

            except Exception as e:
                logger.warning(f"Error calculating top-{n} precision: {e}")
                metrics[f"top_{n}_precision"] = 0.0
                metrics[f"top_{n}_overlap"] = 0

        # Hit rate for high-scoring players
        try:
            # Define high-scoring threshold (top 25%)
            high_score_threshold = np.percentile(actual_clean, 75)

            # Players predicted to be high-scoring
            predicted_high = pred_clean > np.percentile(pred_clean, 75)

            # Players who actually scored high
            actual_high = actual_clean > high_score_threshold

            # Hit rate
            hit_rate = np.sum(predicted_high & actual_high) / np.sum(predicted_high)
            metrics["high_score_hit_rate"] = hit_rate

            # Recall
            recall = np.sum(predicted_high & actual_high) / np.sum(actual_high)
            metrics["high_score_recall"] = recall

        except Exception as e:
            logger.warning(f"Error calculating hit rate: {e}")
            metrics["high_score_hit_rate"] = 0.0
            metrics["high_score_recall"] = 0.0

        return metrics

    def _calculate_calibration_metrics(
        self, predicted_scores: List[float], actual_points: List[float]
    ) -> Dict[str, float]:
        """Calculate calibration metrics"""

        # Convert to numpy arrays
        pred = np.array(predicted_scores)
        actual = np.array(actual_points)

        # Remove any NaN values
        valid_mask = ~(np.isnan(pred) | np.isnan(actual))
        pred_clean = pred[valid_mask]
        actual_clean = actual[valid_mask]

        if len(pred_clean) < 10:
            return {}

        metrics = {}

        # Calibration score (how well predicted scores match actual points)
        try:
            # Bin predictions and calculate average actual points per bin
            num_bins = min(10, len(pred_clean) // 5)
            if num_bins < 2:
                return {}

            bin_edges = np.linspace(pred_clean.min(), pred_clean.max(), num_bins + 1)
            bin_indices = np.digitize(pred_clean, bin_edges) - 1

            calibration_error = 0.0
            bin_counts = 0

            for i in range(num_bins):
                bin_mask = bin_indices == i
                if np.sum(bin_mask) > 0:
                    pred_bin_avg = np.mean(pred_clean[bin_mask])
                    actual_bin_avg = np.mean(actual_clean[bin_mask])
                    calibration_error += abs(pred_bin_avg - actual_bin_avg)
                    bin_counts += 1

            if bin_counts > 0:
                avg_calibration_error = calibration_error / bin_counts
                metrics["calibration_error"] = avg_calibration_error
                metrics["calibration_score"] = 1.0 / (
                    1.0 + avg_calibration_error
                )  # Higher is better
            else:
                metrics["calibration_error"] = float("inf")
                metrics["calibration_score"] = 0.0

        except Exception as e:
            logger.warning(f"Error calculating calibration metrics: {e}")
            metrics["calibration_error"] = float("inf")
            metrics["calibration_score"] = 0.0

        # Reliability diagram metrics
        try:
            # Calculate reliability diagram
            reliability_data = self._calculate_reliability_diagram(
                pred_clean, actual_clean
            )
            metrics["reliability_score"] = reliability_data.get(
                "reliability_score", 0.0
            )
            metrics["confidence_accuracy"] = reliability_data.get(
                "confidence_accuracy", 0.0
            )

        except Exception as e:
            logger.warning(f"Error calculating reliability metrics: {e}")
            metrics["reliability_score"] = 0.0
            metrics["confidence_accuracy"] = 0.0

        return metrics

    def _calculate_error_metrics(
        self, predicted_scores: List[float], actual_points: List[float]
    ) -> Dict[str, float]:
        """Calculate error-based metrics"""

        # Convert to numpy arrays
        pred = np.array(predicted_scores)
        actual = np.array(actual_points)

        # Remove any NaN values
        valid_mask = ~(np.isnan(pred) | np.isnan(actual))
        pred_clean = pred[valid_mask]
        actual_clean = actual[valid_mask]

        if len(pred_clean) < 2:
            return {}

        metrics = {}

        # Mean Absolute Error
        try:
            mae = mean_absolute_error(actual_clean, pred_clean)
            metrics["mean_absolute_error"] = mae
        except Exception as e:
            logger.warning(f"Error calculating MAE: {e}")
            metrics["mean_absolute_error"] = float("inf")

        # Mean Squared Error
        try:
            mse = mean_squared_error(actual_clean, pred_clean)
            metrics["mean_squared_error"] = mse
            metrics["root_mean_squared_error"] = np.sqrt(mse)
        except Exception as e:
            logger.warning(f"Error calculating MSE: {e}")
            metrics["mean_squared_error"] = float("inf")
            metrics["root_mean_squared_error"] = float("inf")

        # Mean Absolute Percentage Error
        try:
            mape = (
                np.mean(np.abs((actual_clean - pred_clean) / (actual_clean + 1e-8)))
                * 100
            )
            metrics["mean_absolute_percentage_error"] = mape
        except Exception as e:
            logger.warning(f"Error calculating MAPE: {e}")
            metrics["mean_absolute_percentage_error"] = float("inf")

        # R-squared
        try:
            ss_res = np.sum((actual_clean - pred_clean) ** 2)
            ss_tot = np.sum((actual_clean - np.mean(actual_clean)) ** 2)
            r_squared = 1 - (ss_res / ss_tot)
            metrics["r_squared"] = r_squared
        except Exception as e:
            logger.warning(f"Error calculating R-squared: {e}")
            metrics["r_squared"] = 0.0

        return metrics

    def _calculate_ranking_metrics(
        self, predicted_scores: List[float], actual_points: List[float]
    ) -> Dict[str, float]:
        """Calculate ranking-based metrics"""

        # Convert to numpy arrays
        pred = np.array(predicted_scores)
        actual = np.array(actual_points)

        # Remove any NaN values
        valid_mask = ~(np.isnan(pred) | np.isnan(actual))
        pred_clean = pred[valid_mask]
        actual_clean = actual[valid_mask]

        if len(pred_clean) < 10:
            return {}

        metrics = {}

        # Ranking accuracy
        try:
            # Get predicted and actual rankings
            pred_ranks = np.argsort(np.argsort(pred_clean))
            actual_ranks = np.argsort(np.argsort(actual_clean))

            # Calculate ranking correlation
            rank_corr = np.corrcoef(pred_ranks, actual_ranks)[0, 1]
            metrics["ranking_correlation"] = (
                rank_corr if not np.isnan(rank_corr) else 0.0
            )

            # Calculate ranking accuracy (percentage of correct relative rankings)
            correct_rankings = 0
            total_comparisons = 0

            for i in range(len(pred_ranks)):
                for j in range(i + 1, len(pred_ranks)):
                    pred_order = pred_ranks[i] < pred_ranks[j]
                    actual_order = actual_ranks[i] < actual_ranks[j]

                    if pred_order == actual_order:
                        correct_rankings += 1
                    total_comparisons += 1

            if total_comparisons > 0:
                ranking_accuracy = correct_rankings / total_comparisons
                metrics["ranking_accuracy"] = ranking_accuracy
            else:
                metrics["ranking_accuracy"] = 0.0

        except Exception as e:
            logger.warning(f"Error calculating ranking metrics: {e}")
            metrics["ranking_correlation"] = 0.0
            metrics["ranking_accuracy"] = 0.0

        return metrics

    def _calculate_position_metrics(
        self,
        predicted_scores: List[float],
        actual_points: List[float],
        player_names: List[str],
    ) -> Dict[str, float]:
        """Calculate position-specific metrics"""

        # This would require position information for each player
        # For now, we'll return empty dict as this is a placeholder
        # In a real implementation, you would need player position data

        return {}

    def _calculate_reliability_diagram(
        self, predicted_scores: np.ndarray, actual_points: np.ndarray
    ) -> Dict[str, float]:
        """Calculate reliability diagram metrics"""

        try:
            # Create confidence bins
            num_bins = 10
            bin_edges = np.linspace(0, 1, num_bins + 1)

            # Normalize predictions to [0, 1] range
            pred_normalized = (predicted_scores - predicted_scores.min()) / (
                predicted_scores.max() - predicted_scores.min()
            )

            # Calculate reliability
            reliability_scores = []
            confidence_levels = []

            for i in range(num_bins):
                bin_mask = (pred_normalized >= bin_edges[i]) & (
                    pred_normalized < bin_edges[i + 1]
                )

                if np.sum(bin_mask) > 0:
                    # Calculate actual frequency of high performance
                    bin_actual = actual_points[bin_mask]
                    high_performance_threshold = np.percentile(actual_points, 75)
                    actual_frequency = np.mean(bin_actual > high_performance_threshold)

                    # Expected frequency (confidence level)
                    expected_frequency = (bin_edges[i] + bin_edges[i + 1]) / 2

                    reliability_scores.append(actual_frequency)
                    confidence_levels.append(expected_frequency)

            if reliability_scores:
                # Calculate reliability score (how well calibrated the predictions are)
                reliability_error = np.mean(
                    np.abs(np.array(reliability_scores) - np.array(confidence_levels))
                )
                reliability_score = 1.0 / (1.0 + reliability_error)

                # Calculate confidence accuracy
                confidence_accuracy = np.corrcoef(
                    reliability_scores, confidence_levels
                )[0, 1]
                if np.isnan(confidence_accuracy):
                    confidence_accuracy = 0.0

                return {
                    "reliability_score": reliability_score,
                    "confidence_accuracy": confidence_accuracy,
                }

        except Exception as e:
            logger.warning(f"Error calculating reliability diagram: {e}")

        return {"reliability_score": 0.0, "confidence_accuracy": 0.0}

    def calculate_backtest_metrics(
        self, gameweek_results: List[Dict[str, Any]]
    ) -> Dict[str, float]:
        """
        Calculate metrics specific to backtest results.

        Args:
            gameweek_results: List of gameweek result dictionaries

        Returns:
            Dictionary of backtest-specific metrics
        """
        if not gameweek_results:
            return {}

        metrics = {}

        # Extract data
        points_list = [gw["total_points"] for gw in gameweek_results]
        transfers_list = [gw["transfers_made"] for gw in gameweek_results]
        transfer_hits_list = [gw["transfer_hits"] for gw in gameweek_results]

        # Basic statistics
        metrics["total_points"] = sum(points_list)
        metrics["average_points_per_gameweek"] = np.mean(points_list)
        metrics["points_standard_deviation"] = np.std(points_list)
        metrics["best_gameweek"] = max(points_list)
        metrics["worst_gameweek"] = min(points_list)

        # Consistency metrics
        avg_points = np.mean(points_list)
        positive_weeks = sum(1 for p in points_list if p > avg_points)
        metrics["consistency_ratio"] = positive_weeks / len(points_list)

        # Transfer efficiency
        total_transfers = sum(transfers_list)
        total_transfer_hits = sum(transfer_hits_list)
        metrics["total_transfers"] = total_transfers
        metrics["total_transfer_hits"] = total_transfer_hits

        if total_transfers > 0:
            metrics["transfer_efficiency"] = (
                metrics["total_points"] - total_transfer_hits
            ) / total_transfers
        else:
            metrics["transfer_efficiency"] = 0.0

        # Streak analysis
        metrics.update(self._calculate_streak_metrics(points_list))

        return metrics

    def _calculate_streak_metrics(self, points_list: List[float]) -> Dict[str, float]:
        """Calculate streak-related metrics"""

        if not points_list:
            return {}

        metrics = {}

        # Calculate streaks
        current_streak = 1
        max_positive_streak = 0
        max_negative_streak = 0
        current_positive_streak = 0
        current_negative_streak = 0

        avg_points = np.mean(points_list)

        for i in range(1, len(points_list)):
            if points_list[i] > avg_points:
                if points_list[i - 1] > avg_points:
                    current_positive_streak += 1
                    current_negative_streak = 0
                else:
                    current_positive_streak = 1
                    current_negative_streak = 0
            else:
                if points_list[i - 1] <= avg_points:
                    current_negative_streak += 1
                    current_positive_streak = 0
                else:
                    current_negative_streak = 1
                    current_positive_streak = 0

            max_positive_streak = max(max_positive_streak, current_positive_streak)
            max_negative_streak = max(max_negative_streak, current_negative_streak)

        metrics["max_positive_streak"] = max_positive_streak
        metrics["max_negative_streak"] = max_negative_streak

        return metrics

    def generate_metrics_report(
        self, metrics: Dict[str, float], title: str = "Performance Metrics Report"
    ) -> str:
        """Generate a formatted report of all metrics"""

        report = []
        report.append("=" * 80)
        report.append(title)
        report.append("=" * 80)
        report.append("")

        # Group metrics by category
        categories = {
            "Correlation Metrics": [
                "pearson_correlation",
                "spearman_correlation",
                "kendall_tau",
            ],
            "Precision Metrics": [
                "top_5_precision",
                "top_10_precision",
                "top_20_precision",
                "high_score_hit_rate",
            ],
            "Calibration Metrics": [
                "calibration_score",
                "reliability_score",
                "confidence_accuracy",
            ],
            "Error Metrics": [
                "mean_absolute_error",
                "root_mean_squared_error",
                "r_squared",
            ],
            "Ranking Metrics": ["ranking_correlation", "ranking_accuracy"],
            "Backtest Metrics": [
                "total_points",
                "average_points_per_gameweek",
                "transfer_efficiency",
            ],
        }

        for category, metric_names in categories.items():
            report.append(category.upper())
            report.append("-" * len(category))

            for metric_name in metric_names:
                if metric_name in metrics:
                    value = metrics[metric_name]
                    if isinstance(value, float):
                        if abs(value) < 0.001:
                            formatted_value = f"{value:.6f}"
                        elif abs(value) < 0.01:
                            formatted_value = f"{value:.4f}"
                        else:
                            formatted_value = f"{value:.3f}"
                    else:
                        formatted_value = str(value)

                    report.append(
                        f"{metric_name.replace('_', ' ').title()}: {formatted_value}"
                    )

            report.append("")

        report.append("=" * 80)

        return "\n".join(report)
