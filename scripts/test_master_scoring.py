#!/usr/bin/env python3
"""
Test Master Scoring System

This script tests the master Player Impact Score system by loading data and calculating final predictions.
"""

import asyncio
import sys
import os
import numpy as np
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from prediction.data.prediction_data_loader import prediction_data_loader
from prediction.scoring.master_score.player_impact_score import PlayerImpactScore
from prediction.scoring.master_score.confidence_calculator import ConfidenceCalculator
from storage.database import db_manager
from utils.logger import get_logger

logger = get_logger("test_master_scoring")


async def test_master_scoring():
    """Test the master scoring system"""
    logger.info("Starting master scoring system test")

    try:
        # Initialize database
        logger.info("Initializing database...")
        db_manager.initialize()

        # Load data
        logger.info("Loading prediction data...")
        data = await prediction_data_loader.get_prediction_data()

        logger.info(f"Loaded {len(data['players'])} players")

        # Initialize master scoring system
        logger.info("Initializing master scoring system...")

        pis_config = {
            "sub_score_weights": {
                "AdvancedQualityScore": 0.35,
                "FormConsistencyScore": 0.25,
                "TeamMomentumScore": 0.15,
                "FixtureScore": 0.15,
                "ValueScore": 0.10,
            },
            "interaction_bonuses": {
                "quality_form_threshold": 7.0,
                "quality_form_bonus": 0.5,
                "form_fixture_threshold": 6.5,
                "form_fixture_bonus": 0.3,
                "quality_value_threshold": 6.0,
                "quality_value_bonus": 0.2,
                "team_form_threshold": 6.0,
                "team_form_bonus": 0.2,
            },
            "risk_penalties": {
                "injury_risk_threshold": 0.3,
                "injury_penalty": -0.5,
                "rotation_risk_threshold": 0.4,
                "rotation_penalty": -0.3,
                "ownership_risk_threshold": 0.1,
                "ownership_penalty": -0.2,
                "price_risk_threshold": 12.0,
                "price_penalty": -0.2,
            },
        }

        confidence_config = {
            "data_quality_weight": 0.3,
            "sample_size_weight": 0.25,
            "consistency_weight": 0.25,
            "model_confidence_weight": 0.2,
            "high_confidence_threshold": 0.8,
            "medium_confidence_threshold": 0.6,
            "low_confidence_threshold": 0.4,
            "min_confidence_threshold": 0.3,
        }

        pis_calculator = PlayerImpactScore(pis_config)
        confidence_calculator = ConfidenceCalculator(confidence_config)

        # Test master scoring for each position
        positions = ["GK", "DEF", "MID", "FWD"]

        for position in positions:
            logger.info(f"\nTesting {position} master scoring...")

            # Get players for this position
            position_players = data["players"][data["players"]["position"] == position]
            logger.info(f"Found {len(position_players)} {position} players")

            if len(position_players) == 0:
                continue

            # Test scoring for first few players
            test_players = position_players.head(3)

            for _, player in test_players.iterrows():
                player_data = player.to_dict()
                logger.info(f"  Testing player: {player_data.get('name', 'Unknown')}")

                # Calculate Player Impact Score
                pis_score = pis_calculator.calculate_with_validation(player_data)

                # Get score breakdown
                breakdown = pis_calculator.get_score_breakdown(player_data)

                # Calculate confidence
                confidence_data = confidence_calculator.calculate_confidence(
                    player_data, breakdown["sub_scores"], pis_score
                )

                # Display results
                logger.info(f"    PIS Score: {pis_score:.2f}")
                logger.info(
                    f"    Confidence: {confidence_data['total_confidence']:.1%} ({confidence_data['confidence_level']})"
                )
                logger.info(f"    Base Score: {breakdown['base_score']:.2f}")
                logger.info(
                    f"    Interaction Bonus: {breakdown['interaction_bonus']:.2f}"
                )
                logger.info(f"    Risk Penalty: {breakdown['risk_penalty']:.2f}")
                logger.info(
                    f"    Confidence Multiplier: {breakdown['confidence_multiplier']:.2f}"
                )

        # Test top players analysis
        logger.info("\nTesting top players analysis...")

        # Get top players by total points
        top_players = data["players"].nlargest(10, "total_points")

        logger.info("Top 10 players by total points:")
        for _, player in top_players.iterrows():
            player_data = player.to_dict()

            # Calculate PIS and confidence
            pis_score = pis_calculator.calculate_with_validation(player_data)
            breakdown = pis_calculator.get_score_breakdown(player_data)
            confidence_data = confidence_calculator.calculate_confidence(
                player_data, breakdown["sub_scores"], pis_score
            )

            logger.info(
                f"  {player_data.get('name', 'Unknown')}: "
                f"Points={player_data.get('total_points', 0)}, "
                f"PIS={pis_score:.2f}, "
                f"Confidence={confidence_data['total_confidence']:.1%}"
            )

        # Test confidence validation
        logger.info("\nTesting confidence validation...")

        # Get a sample player
        sample_player = data["players"].iloc[0].to_dict()
        pis_score = pis_calculator.calculate_with_validation(sample_player)
        breakdown = pis_calculator.get_score_breakdown(sample_player)
        confidence_data = confidence_calculator.calculate_confidence(
            sample_player, breakdown["sub_scores"], pis_score
        )

        # Validate confidence
        is_valid = confidence_calculator.validate_prediction_confidence(confidence_data)
        logger.info(f"Sample player confidence validation: {is_valid}")

        # Get confidence summary
        confidence_summary = confidence_calculator.get_confidence_summary(
            confidence_data
        )
        logger.info(f"Confidence summary:\n{confidence_summary}")

        # Test score correlation
        logger.info("\nTesting score correlation analysis...")

        # Calculate PIS for all players
        all_pis_scores = []
        all_total_points = []

        for _, player in data["players"].iterrows():
            player_data = player.to_dict()
            pis_score = pis_calculator.calculate_with_validation(player_data)
            total_points = player_data.get("total_points", 0)

            all_pis_scores.append(pis_score)
            all_total_points.append(total_points)

        # Calculate correlation
        correlation = np.corrcoef(all_pis_scores, all_total_points)[0, 1]
        logger.info(f"PIS vs Total Points correlation: {correlation:.3f}")

        # Test sub-score analysis
        logger.info("\nTesting sub-score analysis...")

        # Get a sample player for detailed analysis
        sample_player = data["players"].iloc[0].to_dict()
        sub_scores = pis_calculator.get_sub_scores(sample_player)

        logger.info(f"Sample player sub-scores:")
        for score_name, score_value in sub_scores.items():
            logger.info(f"  {score_name}: {score_value:.2f}")

        logger.info("Master scoring system test completed successfully!")

    except Exception as e:
        logger.error(f"Master scoring system test failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(test_master_scoring())
