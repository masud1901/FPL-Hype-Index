#!/usr/bin/env python3
"""
Test Scoring System

This script tests the scoring system by loading data and calculating position-specific scores.
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
from prediction.scoring.position_specific.goalkeeper_score import GoalkeeperScore
from prediction.scoring.position_specific.defender_score import DefenderScore
from prediction.scoring.position_specific.midfielder_score import MidfielderScore
from prediction.scoring.position_specific.forward_score import ForwardScore
from storage.database import db_manager
from utils.logger import get_logger

logger = get_logger("test_scoring_system")


async def test_scoring_system():
    """Test the scoring system"""
    logger.info("Starting scoring system test")

    try:
        # Initialize database
        logger.info("Initializing database...")
        db_manager.initialize()

        # Load data
        logger.info("Loading prediction data...")
        data = await prediction_data_loader.get_prediction_data()

        logger.info(f"Loaded {len(data['players'])} players")

        # Register position-specific scores
        logger.info("Registering position-specific scores...")

        score_registry.register_score(
            GoalkeeperScore,
            {
                "save_performance_weight": 0.4,
                "clean_sheet_weight": 0.3,
                "distribution_weight": 0.2,
                "bonus_weight": 0.1,
            },
        )

        score_registry.register_score(
            DefenderScore,
            {
                "clean_sheet_weight": 0.4,
                "attacking_weight": 0.3,
                "defensive_weight": 0.2,
                "bonus_weight": 0.1,
            },
        )

        score_registry.register_score(
            MidfielderScore,
            {
                "goal_threat_weight": 0.3,
                "creativity_weight": 0.3,
                "defensive_weight": 0.2,
                "bonus_weight": 0.2,
            },
        )

        score_registry.register_score(
            ForwardScore,
            {
                "finishing_weight": 0.4,
                "goal_threat_weight": 0.3,
                "assist_weight": 0.2,
                "bonus_weight": 0.1,
            },
        )

        logger.info(f"Registered {len(score_registry.get_all_score_names())} scores")

        # Test scores for each position
        positions = ["GK", "DEF", "MID", "FWD"]

        for position in positions:
            logger.info(f"\nTesting {position} scoring...")

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

                # Calculate position-specific scores
                position_scores = score_registry.calculate_position_scores(
                    player_data, position
                )

                for score_name, score_value in position_scores.items():
                    logger.info(f"    {score_name}: {score_value:.2f}")

        # Test score registry functions
        logger.info("\nTesting score registry functions...")

        # Get scores by type
        position_scores = score_registry.get_scores_by_type("position")
        logger.info(f"Position scores: {position_scores}")

        # Get score info
        score_info = score_registry.get_score_info()
        logger.info("Score information:")
        for score_name, info in score_info.items():
            logger.info(
                f"  {score_name}: {info.get('description', 'No description')} (Position: {info.get('position', 'ALL')})"
            )

        # Test individual score calculation
        logger.info("\nTesting individual score calculations...")

        # Get a sample midfielder
        midfielders = data["players"][data["players"]["position"] == "MID"]
        if len(midfielders) > 0:
            sample_player = midfielders.iloc[0].to_dict()

            midfielder_score = score_registry.get_score_instance("MidfielderScore")
            if midfielder_score:
                score_value = midfielder_score.calculate_with_validation(sample_player)
                logger.info(f"Sample midfielder score: {score_value:.2f}")
                logger.info(f"Player: {sample_player.get('name', 'Unknown')}")
                logger.info(f"Goals: {sample_player.get('goals_scored', 0)}")
                logger.info(f"Assists: {sample_player.get('assists', 0)}")
                logger.info(f"Creativity: {sample_player.get('creativity', 0)}")

        logger.info("Scoring system test completed successfully!")

    except Exception as e:
        logger.error(f"Scoring system test failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(test_scoring_system())
