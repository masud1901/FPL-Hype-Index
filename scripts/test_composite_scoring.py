#!/usr/bin/env python3
"""
Test Composite Scoring System

This script tests the composite scoring algorithms by loading data and calculating composite scores.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from prediction.data.prediction_data_loader import prediction_data_loader
from prediction.scoring.base.score_registry import score_registry
from prediction.scoring.composite_scores.advanced_quality_score import (
    AdvancedQualityScore,
)
from prediction.scoring.composite_scores.form_consistency_score import (
    FormConsistencyScore,
)
from prediction.scoring.composite_scores.team_momentum_score import TeamMomentumScore
from prediction.scoring.composite_scores.fixture_score import FixtureScore
from prediction.scoring.composite_scores.value_score import ValueScore
from storage.database import db_manager
from utils.logger import get_logger

logger = get_logger("test_composite_scoring")


async def test_composite_scoring():
    """Test the composite scoring system"""
    logger.info("Starting composite scoring system test")

    try:
        # Initialize database
        logger.info("Initializing database...")
        db_manager.initialize()

        # Load data
        logger.info("Loading prediction data...")
        data = await prediction_data_loader.get_prediction_data()

        logger.info(f"Loaded {len(data['players'])} players")

        # Register composite scores
        logger.info("Registering composite scores...")

        score_registry.register_score(
            AdvancedQualityScore,
            {
                "bayesian_adjustment": True,
                "sequence_enhancement": True,
                "sample_size_threshold": 5,
                "position_priors": {"GK": 4.0, "DEF": 4.5, "MID": 5.0, "FWD": 4.5},
            },
        )

        score_registry.register_score(
            FormConsistencyScore,
            {
                "lookback_gameweeks": 6,
                "recent_weight": 0.6,
                "consistency_weight": 0.4,
                "excellent_form": 7.0,
                "good_form": 5.0,
                "poor_form": 3.0,
            },
        )

        score_registry.register_score(
            TeamMomentumScore,
            {
                "results_weight": 0.4,
                "goals_weight": 0.3,
                "defensive_weight": 0.2,
                "expected_weight": 0.1,
                "lookback_games": 6,
            },
        )

        score_registry.register_score(
            FixtureScore,
            {
                "difficulty_weight": 0.5,
                "venue_weight": 0.2,
                "scheduling_weight": 0.2,
                "rotation_weight": 0.1,
                "lookahead_gameweeks": 5,
            },
        )

        score_registry.register_score(
            ValueScore,
            {
                "price_efficiency_weight": 0.4,
                "ownership_weight": 0.3,
                "differential_weight": 0.2,
                "momentum_weight": 0.1,
                "excellent_ppm": 25.0,
                "good_ppm": 20.0,
                "poor_ppm": 15.0,
            },
        )

        logger.info(f"Registered {len(score_registry.get_all_score_names())} scores")

        # Test composite scores for each position
        positions = ["GK", "DEF", "MID", "FWD"]

        for position in positions:
            logger.info(f"\nTesting {position} composite scoring...")

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

                # Calculate composite scores
                composite_scores = score_registry.calculate_scores_by_type(
                    player_data, "composite"
                )

                for score_name, score_value in composite_scores.items():
                    logger.info(f"    {score_name}: {score_value:.2f}")

        # Test score registry functions
        logger.info("\nTesting composite score registry functions...")

        # Get scores by type
        composite_scores = score_registry.get_scores_by_type("composite")
        logger.info(f"Composite scores: {composite_scores}")

        # Get score info
        score_info = score_registry.get_score_info()
        logger.info("Composite score information:")
        for score_name, info in score_info.items():
            if info.get("type") == "composite":
                logger.info(
                    f"  {score_name}: {info.get('description', 'No description')}"
                )

        # Test individual composite score calculation
        logger.info("\nTesting individual composite score calculations...")

        # Get a sample midfielder
        midfielders = data["players"][data["players"]["position"] == "MID"]
        if len(midfielders) > 0:
            sample_player = midfielders.iloc[0].to_dict()

            # Test Advanced Quality Score
            aqs_score = score_registry.get_score_instance("AdvancedQualityScore")
            if aqs_score:
                score_value = aqs_score.calculate_with_validation(sample_player)
                logger.info(f"Advanced Quality Score: {score_value:.2f}")
                logger.info(f"Player: {sample_player.get('name', 'Unknown')}")
                logger.info(f"Position: {sample_player.get('position', 'Unknown')}")
                logger.info(f"Total Points: {sample_player.get('total_points', 0)}")
                logger.info(f"Form: {sample_player.get('form', 0)}")

            # Test Form Consistency Score
            fcs_score = score_registry.get_score_instance("FormConsistencyScore")
            if fcs_score:
                score_value = fcs_score.calculate_with_validation(sample_player)
                logger.info(f"Form Consistency Score: {score_value:.2f}")

            # Test Team Momentum Score
            tms_score = score_registry.get_score_instance("TeamMomentumScore")
            if tms_score:
                score_value = tms_score.calculate_with_validation(sample_player)
                logger.info(f"Team Momentum Score: {score_value:.2f}")

            # Test Fixture Score
            fxs_score = score_registry.get_score_instance("FixtureScore")
            if fxs_score:
                score_value = fxs_score.calculate_with_validation(sample_player)
                logger.info(f"Fixture Score: {score_value:.2f}")

            # Test Value Score
            vs_score = score_registry.get_score_instance("ValueScore")
            if vs_score:
                score_value = vs_score.calculate_with_validation(sample_player)
                logger.info(f"Value Score: {score_value:.2f}")

        # Test score correlation analysis
        logger.info("\nTesting score correlation analysis...")

        # Get top players by total points
        top_players = data["players"].nlargest(10, "total_points")

        logger.info("Top 10 players by total points:")
        for _, player in top_players.iterrows():
            player_data = player.to_dict()
            composite_scores = score_registry.calculate_scores_by_type(
                player_data, "composite"
            )

            logger.info(
                f"  {player_data.get('name', 'Unknown')}: "
                f"Points={player_data.get('total_points', 0)}, "
                f"AQS={composite_scores.get('AdvancedQualityScore', 0):.2f}, "
                f"FCS={composite_scores.get('FormConsistencyScore', 0):.2f}, "
                f"TMS={composite_scores.get('TeamMomentumScore', 0):.2f}, "
                f"FxS={composite_scores.get('FixtureScore', 0):.2f}, "
                f"VS={composite_scores.get('ValueScore', 0):.2f}"
            )

        logger.info("Composite scoring system test completed successfully!")

    except Exception as e:
        logger.error(f"Composite scoring system test failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(test_composite_scoring())
