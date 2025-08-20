#!/usr/bin/env python3
"""
FPL Prediction Backtest Script

This script runs comprehensive backtest simulations to validate the prediction
engine's performance against historical data.

Usage:
    python scripts/run_prediction_backtest.py [--start-gw 1] [--end-gw 10] [--strategy balanced]
    python scripts/run_prediction_backtest.py --compare-strategies --start-gw 1 --end-gw 10
"""

import sys
import os
import argparse
import logging
import json
from typing import Dict, List, Any
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from prediction.validation.backtesting.backtest_engine import BacktestEngine
from prediction.validation.backtesting.performance_metrics import PerformanceMetrics
from scripts.run_prediction_optimization import (
    create_sample_squad,
    create_available_players,
)
from config.settings import get_settings

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def create_strategy_configs() -> Dict[str, Dict[str, Any]]:
    """Create different strategy configurations for testing"""

    strategies = {
        "balanced": {
            "name": "Balanced Strategy",
            "strategy": "balanced",
            "max_transfers_per_week": 1,
            "min_confidence_threshold": 0.6,
            "max_risk_threshold": 0.4,
            "use_wildcard": False,
            "use_free_hit": False,
            "use_triple_captain": False,
            "use_bench_boost": False,
        },
        "aggressive": {
            "name": "Aggressive Strategy",
            "strategy": "aggressive",
            "max_transfers_per_week": 2,
            "min_confidence_threshold": 0.5,
            "max_risk_threshold": 0.6,
            "use_wildcard": False,
            "use_free_hit": False,
            "use_triple_captain": False,
            "use_bench_boost": False,
        },
        "conservative": {
            "name": "Conservative Strategy",
            "strategy": "conservative",
            "max_transfers_per_week": 1,
            "min_confidence_threshold": 0.8,
            "max_risk_threshold": 0.2,
            "use_wildcard": False,
            "use_free_hit": False,
            "use_triple_captain": False,
            "use_bench_boost": False,
        },
        "high_risk": {
            "name": "High Risk Strategy",
            "strategy": "aggressive",
            "max_transfers_per_week": 3,
            "min_confidence_threshold": 0.4,
            "max_risk_threshold": 0.8,
            "use_wildcard": False,
            "use_free_hit": False,
            "use_triple_captain": False,
            "use_bench_boost": False,
        },
        "no_transfers": {
            "name": "No Transfers Strategy",
            "strategy": "balanced",
            "max_transfers_per_week": 0,
            "min_confidence_threshold": 1.0,
            "max_risk_threshold": 0.0,
            "use_wildcard": False,
            "use_free_hit": False,
            "use_triple_captain": False,
            "use_bench_boost": False,
        },
    }

    return strategies


def run_single_backtest(
    start_gameweek: int,
    end_gameweek: int,
    strategy_config: Dict[str, Any],
    initial_squad: List[Dict[str, Any]],
    available_players: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Run a single backtest with the given configuration"""

    logger.info(f"Running backtest with strategy: {strategy_config['name']}")

    # Initialize backtest engine
    settings = get_settings()
    engine = BacktestEngine(settings.dict())

    # Run backtest
    result = engine.run_backtest(
        start_gameweek=start_gameweek,
        end_gameweek=end_gameweek,
        initial_squad=initial_squad,
        strategy_config=strategy_config,
        available_players=available_players,
    )

    return result


def run_strategy_comparison(
    start_gameweek: int,
    end_gameweek: int,
    initial_squad: List[Dict[str, Any]],
    available_players: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Run backtests for multiple strategies and compare results"""

    logger.info("Running strategy comparison backtest")

    # Get strategy configurations
    strategies = create_strategy_configs()

    # Initialize backtest engine
    settings = get_settings()
    engine = BacktestEngine(settings.dict())

    # Run backtests for all strategies
    strategy_results = engine.compare_strategies(
        start_gameweek=start_gameweek,
        end_gameweek=end_gameweek,
        initial_squad=initial_squad,
        strategies=list(strategies.values()),
        available_players=available_players,
    )

    return strategy_results


def display_backtest_results(result, strategy_name: str = "Backtest"):
    """Display backtest results in a formatted way"""

    print(f"\n{'='*80}")
    print(f"{strategy_name.upper()} RESULTS")
    print(f"{'='*80}")

    # Summary
    print(f"\nSUMMARY:")
    print(f"  Period: GW{result.start_gameweek} - GW{result.end_gameweek}")
    print(f"  Total Points: {result.total_points:.1f}")
    print(f"  Average Points per Gameweek: {result.average_points_per_gameweek:.1f}")
    print(f"  Total Transfers: {result.total_transfers}")
    print(f"  Total Transfer Hits: {result.total_transfer_hits}")
    print(f"  Final Squad Value: £{result.final_squad_value:.1f}m")

    # Performance metrics
    print(f"\nPERFORMANCE METRICS:")
    for metric, value in result.performance_metrics.items():
        if isinstance(value, float):
            print(f"  {metric.replace('_', ' ').title()}: {value:.3f}")
        else:
            print(f"  {metric.replace('_', ' ').title()}: {value}")

    # Gameweek breakdown
    print(f"\nGAMEWEEK BREAKDOWN:")
    print(
        f"{'GW':<4} {'Points':<8} {'Squad':<8} {'Bench':<8} {'Captain':<8} {'Transfers':<10}"
    )
    print("-" * 50)

    for gw_result in result.gameweek_results:
        print(
            f"{gw_result.gameweek:<4} {gw_result.total_points:<8.1f} "
            f"{gw_result.squad_points:<8.1f} {gw_result.bench_points:<8.1f} "
            f"{gw_result.captain_points:<8.1f} {gw_result.transfers_made:<10}"
        )


def display_strategy_comparison(results: Dict[str, Any]):
    """Display comparison of multiple strategy results"""

    print(f"\n{'='*100}")
    print("STRATEGY COMPARISON RESULTS")
    print(f"{'='*100}")

    # Create comparison table
    print(
        f"\n{'Strategy':<20} {'Total Points':<15} {'Avg Points':<15} {'Transfers':<12} {'Transfer Hits':<15} {'Efficiency':<12}"
    )
    print("-" * 100)

    # Sort strategies by total points
    sorted_strategies = sorted(
        results.items(), key=lambda x: x[1].total_points, reverse=True
    )

    for strategy_name, result in sorted_strategies:
        efficiency = result.performance_metrics.get("transfer_efficiency", 0.0)
        print(
            f"{strategy_name:<20} {result.total_points:<15.1f} "
            f"{result.average_points_per_gameweek:<15.1f} "
            f"{result.total_transfers:<12} {result.total_transfer_hits:<15} "
            f"{efficiency:<12.2f}"
        )

    # Winner analysis
    if sorted_strategies:
        winner_name, winner_result = sorted_strategies[0]
        print(f"\n🏆 WINNER: {winner_name}")
        print(f"   Total Points: {winner_result.total_points:.1f}")
        print(f"   Average Points: {winner_result.average_points_per_gameweek:.1f}")
        print(
            f"   Transfer Efficiency: {winner_result.performance_metrics.get('transfer_efficiency', 0.0):.2f}"
        )

        # Strategy insights
        print(f"\nSTRATEGY INSIGHTS:")
        for strategy_name, result in sorted_strategies:
            points_diff = result.total_points - sorted_strategies[-1][1].total_points
            print(f"  {strategy_name}: {points_diff:+.1f} points vs worst strategy")


def save_results_to_file(results: Dict[str, Any], filename: str):
    """Save backtest results to a JSON file"""

    # Convert results to serializable format
    serializable_results = {}

    for strategy_name, result in results.items():
        serializable_results[strategy_name] = {
            "start_gameweek": result.start_gameweek,
            "end_gameweek": result.end_gameweek,
            "total_points": result.total_points,
            "average_points_per_gameweek": result.average_points_per_gameweek,
            "total_transfers": result.total_transfers,
            "total_transfer_hits": result.total_transfer_hits,
            "final_squad_value": result.final_squad_value,
            "performance_metrics": result.performance_metrics,
            "strategy_config": result.strategy_config,
            "gameweek_results": [
                {
                    "gameweek": gw.gameweek,
                    "total_points": gw.total_points,
                    "squad_points": gw.squad_points,
                    "bench_points": gw.bench_points,
                    "captain_points": gw.captain_points,
                    "transfers_made": gw.transfers_made,
                    "transfer_hits": gw.transfer_hits,
                    "squad_value": gw.squad_value,
                    "captain_choice": gw.captain_choice,
                    "vice_captain_choice": gw.vice_captain_choice,
                }
                for gw in result.gameweek_results
            ],
        }

    # Save to file
    with open(filename, "w") as f:
        json.dump(serializable_results, f, indent=2)

    print(f"\nResults saved to: {filename}")


def generate_performance_report(results: Dict[str, Any]) -> str:
    """Generate a comprehensive performance report"""

    # Initialize metrics calculator
    metrics_calculator = PerformanceMetrics()

    report = []
    report.append("FPL PREDICTION ENGINE PERFORMANCE REPORT")
    report.append("=" * 80)
    report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("")

    # Overall summary
    total_strategies = len(results)
    total_points_range = [r.total_points for r in results.values()]
    avg_points_range = [r.average_points_per_gameweek for r in results.values()]

    report.append("OVERALL SUMMARY")
    report.append("-" * 40)
    report.append(f"Strategies Tested: {total_strategies}")
    report.append(
        f"Points Range: {min(total_points_range):.1f} - {max(total_points_range):.1f}"
    )
    report.append(
        f"Average Points Range: {min(avg_points_range):.1f} - {max(avg_points_range):.1f}"
    )
    report.append("")

    # Strategy rankings
    sorted_strategies = sorted(
        results.items(), key=lambda x: x[1].total_points, reverse=True
    )

    report.append("STRATEGY RANKINGS")
    report.append("-" * 40)
    for i, (strategy_name, result) in enumerate(sorted_strategies, 1):
        report.append(
            f"{i}. {strategy_name}: {result.total_points:.1f} points "
            f"(avg: {result.average_points_per_gameweek:.1f})"
        )
    report.append("")

    # Performance analysis
    report.append("PERFORMANCE ANALYSIS")
    report.append("-" * 40)

    # Best strategy analysis
    best_strategy_name, best_result = sorted_strategies[0]
    report.append(f"Best Strategy: {best_strategy_name}")
    report.append(f"  Total Points: {best_result.total_points:.1f}")
    report.append(f"  Average Points: {best_result.average_points_per_gameweek:.1f}")
    report.append(
        f"  Transfer Efficiency: {best_result.performance_metrics.get('transfer_efficiency', 0.0):.2f}"
    )
    report.append(
        f"  Consistency Score: {best_result.performance_metrics.get('consistency_score', 0.0):.3f}"
    )
    report.append("")

    # Strategy comparison
    report.append("STRATEGY COMPARISON")
    report.append("-" * 40)
    worst_result = sorted_strategies[-1][1]
    for strategy_name, result in sorted_strategies:
        points_diff = result.total_points - worst_result.total_points
        report.append(f"{strategy_name}: {points_diff:+.1f} points vs worst strategy")
    report.append("")

    # Recommendations
    report.append("RECOMMENDATIONS")
    report.append("-" * 40)
    report.append(f"1. Primary Strategy: {best_strategy_name}")
    report.append(
        f"2. Best for Consistency: {best_strategy_name} "
        f"(consistency: {best_result.performance_metrics.get('consistency_score', 0.0):.3f})"
    )

    # Find most efficient strategy
    most_efficient = max(
        results.items(),
        key=lambda x: x[1].performance_metrics.get("transfer_efficiency", 0.0),
    )
    report.append(
        f"3. Most Transfer Efficient: {most_efficient[0]} "
        f"(efficiency: {most_efficient[1].performance_metrics.get('transfer_efficiency', 0.0):.2f})"
    )

    return "\n".join(report)


def main():
    """Main execution function"""

    parser = argparse.ArgumentParser(description="FPL Prediction Backtest")
    parser.add_argument("--start-gw", type=int, default=1, help="Starting gameweek")
    parser.add_argument("--end-gw", type=int, default=10, help="Ending gameweek")
    parser.add_argument(
        "--strategy",
        choices=["balanced", "aggressive", "conservative", "high_risk", "no_transfers"],
        default="balanced",
        help="Strategy to test",
    )
    parser.add_argument(
        "--compare-strategies", action="store_true", help="Compare all strategies"
    )
    parser.add_argument(
        "--save-results", type=str, default=None, help="Save results to JSON file"
    )
    parser.add_argument(
        "--generate-report",
        type=str,
        default=None,
        help="Generate performance report to file",
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    print("FPL Prediction Backtest Engine")
    print("=" * 50)
    print(f"Period: GW{args.start_gw} - GW{args.end_gw}")

    if args.compare_strategies:
        print("Mode: Strategy Comparison")
    else:
        print(f"Strategy: {args.strategy}")

    try:
        # Create sample data
        logger.info("Creating sample squad and available players...")
        initial_squad = create_sample_squad()
        available_players = create_available_players()

        if args.compare_strategies:
            # Run strategy comparison
            results = run_strategy_comparison(
                start_gameweek=args.start_gw,
                end_gameweek=args.end_gw,
                initial_squad=initial_squad,
                available_players=available_players,
            )

            # Display results
            display_strategy_comparison(results)

            # Save results if requested
            if args.save_results:
                save_results_to_file(results, args.save_results)

            # Generate report if requested
            if args.generate_report:
                report = generate_performance_report(results)
                with open(args.generate_report, "w") as f:
                    f.write(report)
                print(f"\nPerformance report saved to: {args.generate_report}")

        else:
            # Run single strategy backtest
            strategies = create_strategy_configs()
            strategy_config = strategies[args.strategy]

            result = run_single_backtest(
                start_gameweek=args.start_gw,
                end_gameweek=args.end_gw,
                strategy_config=strategy_config,
                initial_squad=initial_squad,
                available_players=available_players,
            )

            # Display results
            display_backtest_results(result, strategy_config["name"])

            # Save results if requested
            if args.save_results:
                save_results_to_file({args.strategy: result}, args.save_results)

        print(f"\nBacktest completed successfully!")

    except Exception as e:
        logger.error(f"Error during backtest: {e}")
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
