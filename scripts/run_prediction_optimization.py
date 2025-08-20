#!/usr/bin/env python3
"""
FPL Prediction Optimization Script

This script demonstrates the complete prediction engine workflow:
1. Load player data from the database
2. Calculate Player Impact Scores for all players
3. Run transfer optimization for a sample squad
4. Display recommendations with reasoning

Usage:
    python scripts/run_prediction_optimization.py [--strategy balanced] [--transfers 1] [--budget 2.0]
"""

import sys
import os
import argparse
import logging
from typing import Dict, List, Any
import json

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from prediction.optimization.algorithms.transfer_optimizer import TransferOptimizer
from prediction.scoring.master_score.player_impact_score import PlayerImpactScore
from prediction.data.prediction_data_loader import PredictionDataLoader
from config.settings import get_settings

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def create_sample_squad() -> List[Dict[str, Any]]:
    """Create a sample FPL squad for testing"""

    sample_squad = [
        # Goalkeepers
        {
            "id": "gk1",
            "name": "Alisson",
            "position": "GK",
            "team": "Liverpool",
            "price": 5.5,
            "form": 6.2,
            "total_points": 120,
            "minutes_played": 2700,
            "clean_sheets": 12,
            "saves": 85,
            "goals_conceded": 25,
            "bonus_points": 8,
            "injury_history": [],
            "age": 31,
            "rotation_risk": False,
        },
        {
            "id": "gk2",
            "name": "Raya",
            "position": "GK",
            "team": "Arsenal",
            "price": 5.0,
            "form": 5.8,
            "total_points": 110,
            "minutes_played": 2700,
            "clean_sheets": 10,
            "saves": 78,
            "goals_conceded": 28,
            "bonus_points": 6,
            "injury_history": [],
            "age": 28,
            "rotation_risk": False,
        },
        # Defenders
        {
            "id": "def1",
            "name": "Alexander-Arnold",
            "position": "DEF",
            "team": "Liverpool",
            "price": 8.5,
            "form": 7.5,
            "total_points": 180,
            "minutes_played": 2700,
            "clean_sheets": 8,
            "goals": 3,
            "assists": 12,
            "bonus_points": 15,
            "injury_history": [],
            "age": 25,
            "rotation_risk": False,
        },
        {
            "id": "def2",
            "name": "Saliba",
            "position": "DEF",
            "team": "Arsenal",
            "price": 5.5,
            "form": 6.8,
            "total_points": 140,
            "minutes_played": 2700,
            "clean_sheets": 10,
            "goals": 2,
            "assists": 1,
            "bonus_points": 8,
            "injury_history": [],
            "age": 22,
            "rotation_risk": False,
        },
        {
            "id": "def3",
            "name": "Trippier",
            "position": "DEF",
            "team": "Newcastle",
            "price": 6.5,
            "form": 6.2,
            "total_points": 130,
            "minutes_played": 2700,
            "clean_sheets": 7,
            "goals": 1,
            "assists": 8,
            "bonus_points": 10,
            "injury_history": [],
            "age": 33,
            "rotation_risk": False,
        },
        {
            "id": "def4",
            "name": "Estupinan",
            "position": "DEF",
            "team": "Brighton",
            "price": 5.0,
            "form": 5.5,
            "total_points": 95,
            "minutes_played": 2400,
            "clean_sheets": 5,
            "goals": 1,
            "assists": 4,
            "bonus_points": 5,
            "injury_history": [],
            "age": 25,
            "rotation_risk": False,
        },
        {
            "id": "def5",
            "name": "Branthwaite",
            "position": "DEF",
            "team": "Everton",
            "price": 4.0,
            "form": 4.8,
            "total_points": 75,
            "minutes_played": 2700,
            "clean_sheets": 4,
            "goals": 1,
            "assists": 0,
            "bonus_points": 3,
            "injury_history": [],
            "age": 21,
            "rotation_risk": False,
        },
        # Midfielders
        {
            "id": "mid1",
            "name": "Salah",
            "position": "MID",
            "team": "Liverpool",
            "price": 13.0,
            "form": 8.2,
            "total_points": 220,
            "minutes_played": 2700,
            "goals": 18,
            "assists": 12,
            "bonus_points": 25,
            "injury_history": [],
            "age": 31,
            "rotation_risk": False,
        },
        {
            "id": "mid2",
            "name": "Saka",
            "position": "MID",
            "team": "Arsenal",
            "price": 9.0,
            "form": 7.5,
            "total_points": 180,
            "minutes_played": 2700,
            "goals": 12,
            "assists": 10,
            "bonus_points": 18,
            "injury_history": [],
            "age": 22,
            "rotation_risk": False,
        },
        {
            "id": "mid3",
            "name": "Foden",
            "position": "MID",
            "team": "Man City",
            "price": 8.0,
            "form": 7.8,
            "total_points": 170,
            "minutes_played": 2400,
            "goals": 14,
            "assists": 8,
            "bonus_points": 15,
            "injury_history": [],
            "age": 23,
            "rotation_risk": True,
        },
        {
            "id": "mid4",
            "name": "Palmer",
            "position": "MID",
            "team": "Chelsea",
            "price": 6.0,
            "form": 6.5,
            "total_points": 120,
            "minutes_played": 2100,
            "goals": 8,
            "assists": 6,
            "bonus_points": 8,
            "injury_history": [],
            "age": 21,
            "rotation_risk": False,
        },
        {
            "id": "mid5",
            "name": "Gordon",
            "position": "MID",
            "team": "Newcastle",
            "price": 6.5,
            "form": 6.2,
            "total_points": 110,
            "minutes_played": 2400,
            "goals": 6,
            "assists": 7,
            "bonus_points": 6,
            "injury_history": [],
            "age": 22,
            "rotation_risk": False,
        },
        # Forwards
        {
            "id": "fwd1",
            "name": "Haaland",
            "position": "FWD",
            "team": "Man City",
            "price": 14.0,
            "form": 8.5,
            "total_points": 240,
            "minutes_played": 2400,
            "goals": 25,
            "assists": 5,
            "bonus_points": 30,
            "injury_history": [],
            "age": 23,
            "rotation_risk": False,
        },
        {
            "id": "fwd2",
            "name": "Watkins",
            "position": "FWD",
            "team": "Aston Villa",
            "price": 8.5,
            "form": 7.2,
            "total_points": 160,
            "minutes_played": 2700,
            "goals": 15,
            "assists": 8,
            "bonus_points": 12,
            "injury_history": [],
            "age": 28,
            "rotation_risk": False,
        },
        {
            "id": "fwd3",
            "name": "Solanke",
            "position": "FWD",
            "team": "Bournemouth",
            "price": 6.5,
            "form": 6.8,
            "total_points": 130,
            "minutes_played": 2700,
            "goals": 12,
            "assists": 4,
            "bonus_points": 8,
            "injury_history": [],
            "age": 26,
            "rotation_risk": False,
        },
    ]

    return sample_squad


def create_available_players() -> List[Dict[str, Any]]:
    """Create a pool of available players for transfers"""

    available_players = [
        # High-performing alternatives
        {
            "id": "alt_mid1",
            "name": "De Bruyne",
            "position": "MID",
            "team": "Man City",
            "price": 10.5,
            "form": 8.0,
            "total_points": 150,
            "minutes_played": 1800,
            "goals": 8,
            "assists": 15,
            "bonus_points": 20,
            "injury_history": ["Hamstring", "Knee"],
            "age": 32,
            "rotation_risk": True,
        },
        {
            "id": "alt_fwd1",
            "name": "Isak",
            "position": "FWD",
            "team": "Newcastle",
            "price": 7.5,
            "form": 7.5,
            "total_points": 140,
            "minutes_played": 2100,
            "goals": 14,
            "assists": 3,
            "bonus_points": 10,
            "injury_history": ["Hamstring"],
            "age": 24,
            "rotation_risk": False,
        },
        {
            "id": "alt_def1",
            "name": "Van Dijk",
            "position": "DEF",
            "team": "Liverpool",
            "price": 6.5,
            "form": 6.8,
            "total_points": 145,
            "minutes_played": 2700,
            "clean_sheets": 9,
            "goals": 3,
            "assists": 1,
            "bonus_points": 12,
            "injury_history": [],
            "age": 32,
            "rotation_risk": False,
        },
        {
            "id": "alt_mid2",
            "name": "Bowen",
            "position": "MID",
            "team": "West Ham",
            "price": 7.5,
            "form": 7.2,
            "total_points": 155,
            "minutes_played": 2700,
            "goals": 12,
            "assists": 8,
            "bonus_points": 12,
            "injury_history": [],
            "age": 27,
            "rotation_risk": False,
        },
        {
            "id": "alt_gk1",
            "name": "Ederson",
            "position": "GK",
            "team": "Man City",
            "price": 5.5,
            "form": 6.5,
            "total_points": 125,
            "minutes_played": 2700,
            "clean_sheets": 11,
            "saves": 65,
            "goals_conceded": 22,
            "bonus_points": 8,
            "injury_history": [],
            "age": 30,
            "rotation_risk": False,
        },
    ]

    return available_players


def display_squad_analysis(squad: List[Dict[str, Any]], scorer: PlayerImpactScore):
    """Display analysis of current squad"""

    print("\n" + "=" * 80)
    print("CURRENT SQUAD ANALYSIS")
    print("=" * 80)

    # Calculate scores for current squad
    squad_scores = []
    for player in squad:
        try:
            score_result = scorer.calculate_pis(player)
            squad_scores.append(
                {
                    "player": player,
                    "score": score_result["final_pis"],
                    "confidence": score_result["confidence"],
                    "sub_scores": score_result["sub_scores"],
                }
            )
        except Exception as e:
            logger.warning(f"Failed to score {player['name']}: {e}")
            squad_scores.append(
                {"player": player, "score": 0.0, "confidence": 0.0, "sub_scores": {}}
            )

    # Sort by score
    squad_scores.sort(key=lambda x: x["score"], reverse=True)

    # Display by position
    positions = ["GK", "DEF", "MID", "FWD"]

    for position in positions:
        print(f"\n{position} PLAYERS:")
        print("-" * 60)

        position_players = [
            s for s in squad_scores if s["player"]["position"] == position
        ]

        for player_score in position_players:
            player = player_score["player"]
            score = player_score["score"]
            confidence = player_score["confidence"]

            print(
                f"{player['name']:<20} {player['team']:<15} "
                f"Score: {score:>6.2f} Confidence: {confidence:>5.2f} "
                f"Price: £{player['price']:>5.1f}"
            )

    # Squad summary
    total_score = sum(s["score"] for s in squad_scores)
    avg_confidence = sum(s["confidence"] for s in squad_scores) / len(squad_scores)
    total_value = sum(p["price"] for p in squad)

    print(f"\nSQUAD SUMMARY:")
    print(f"Total PIS Score: {total_score:.2f}")
    print(f"Average Confidence: {avg_confidence:.2f}")
    print(f"Total Squad Value: £{total_value:.1f}m")


def display_transfer_recommendations(recommendations: List, strategy: str):
    """Display transfer recommendations"""

    print("\n" + "=" * 80)
    print(f"TRANSFER RECOMMENDATIONS ({strategy.upper()} STRATEGY)")
    print("=" * 80)

    if not recommendations:
        print("No valid transfer recommendations found.")
        return

    for i, combination in enumerate(recommendations[:5], 1):
        print(f"\n{i}. COMBINATION {i}")
        print("-" * 60)
        print(f"Expected Gain: {combination.total_expected_gain:.2f} points")
        print(f"Confidence: {combination.total_confidence:.2f}")
        print(f"Risk Score: {combination.total_risk:.2f}")
        print(f"Budget Impact: £{combination.budget_impact:.1f}m")
        print(f"Reasoning: {combination.reasoning}")

        print("\nTransfers:")
        for j, transfer in enumerate(combination.transfers, 1):
            print(
                f"  {j}. {transfer.player_out['name']} ({transfer.player_out['team']}) "
                f"→ {transfer.player_in['name']} ({transfer.player_in['team']})"
            )
            print(f"     Expected Gain: {transfer.expected_points_gain:.2f} points")
            print(f"     Confidence: {transfer.confidence_score:.2f}")
            print(f"     Risk: {transfer.risk_score:.2f}")
            print(f"     Reasoning: {transfer.reasoning}")


def main():
    """Main execution function"""

    parser = argparse.ArgumentParser(description="FPL Transfer Optimization")
    parser.add_argument(
        "--strategy",
        choices=["aggressive", "balanced", "conservative"],
        default="balanced",
        help="Optimization strategy",
    )
    parser.add_argument(
        "--transfers", type=int, default=1, help="Number of transfers available"
    )
    parser.add_argument(
        "--budget", type=float, default=2.0, help="Available budget for transfers"
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    print("FPL Transfer Optimization Engine")
    print("=" * 50)
    print(f"Strategy: {args.strategy}")
    print(f"Transfers Available: {args.transfers}")
    print(f"Budget: £{args.budget}m")

    try:
        # Initialize components
        logger.info("Initializing prediction engine components...")

        # Load settings
        settings = get_settings()

        # Initialize scorer
        scorer = PlayerImpactScore(settings.dict())

        # Create sample data
        logger.info("Creating sample squad and available players...")
        current_squad = create_sample_squad()
        available_players = create_available_players()

        # Display current squad analysis
        display_squad_analysis(current_squad, scorer)

        # Initialize optimizer
        logger.info("Initializing transfer optimizer...")
        optimizer = TransferOptimizer(settings.dict())

        # Run optimization
        logger.info("Running transfer optimization...")
        recommendations = optimizer.optimize_transfers(
            current_squad=current_squad,
            available_players=available_players,
            budget=args.budget,
            transfers_available=args.transfers,
            strategy=args.strategy,
        )

        # Display recommendations
        display_transfer_recommendations(recommendations, args.strategy)

        # Also show single transfer recommendations
        logger.info("Generating single transfer recommendations...")
        single_recs = optimizer.get_single_transfer_recommendations(
            current_squad=current_squad,
            available_players=available_players,
            budget=args.budget,
        )

        print("\n" + "=" * 80)
        print("SINGLE TRANSFER RECOMMENDATIONS")
        print("=" * 80)

        for i, rec in enumerate(single_recs[:5], 1):
            print(f"\n{i}. {rec.player_out['name']} → {rec.player_in['name']}")
            print(f"   Expected Gain: {rec.expected_points_gain:.2f} points")
            print(f"   Confidence: {rec.confidence_score:.2f}")
            print(f"   Risk: {rec.risk_score:.2f}")
            print(f"   Reasoning: {rec.reasoning}")

        print(f"\nOptimization completed successfully!")
        print(f"Generated {len(recommendations)} transfer combinations")

    except Exception as e:
        logger.error(f"Error during optimization: {e}")
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
