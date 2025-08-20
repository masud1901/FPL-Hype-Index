#!/usr/bin/env python3
"""
Test Feature Engineering System

This script tests the feature engineering system by loading data and calculating features.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from prediction.data.prediction_data_loader import prediction_data_loader
from prediction.features.base.feature_registry import feature_registry
from storage.database import db_manager
from prediction.features.player_features.form_features import FormConsistencyFeature
from prediction.features.player_features.quality_features import QualityFeature
from prediction.features.player_features.fixture_features import (
    FixtureDifficultyFeature,
)
from prediction.features.player_features.value_features import ValueFeature
from prediction.features.team_features.momentum_features import TeamMomentumFeature
from prediction.features.team_features.schedule_features import TeamScheduleFeature
from utils.logger import get_logger

logger = get_logger("test_feature_engineering")


async def test_feature_engineering():
    """Test the feature engineering system"""
    logger.info("Starting feature engineering test")

    try:
        # Initialize database
        logger.info("Initializing database...")
        db_manager.initialize()

        # Load data
        logger.info("Loading prediction data...")
        data = await prediction_data_loader.get_prediction_data()

        logger.info(f"Loaded {len(data['players'])} players")
        logger.info(f"Loaded {len(data['teams'])} teams")
        logger.info(f"Loaded {len(data['fixtures'])} fixtures")

        # Register features
        logger.info("Registering features...")

        # Player features
        feature_registry.register_feature(
            FormConsistencyFeature,
            {
                "lookback_gameweeks": 6,
                "weights": [0.3, 0.25, 0.2, 0.15, 0.08, 0.02],
                "volatility_threshold": 1.0,
                "ceiling_threshold": 8.0,
            },
        )

        feature_registry.register_feature(QualityFeature, {"position_weights": {}})

        feature_registry.register_feature(
            FixtureDifficultyFeature,
            {"lookahead_gameweeks": 5, "home_advantage": 0.5, "away_penalty": -0.5},
        )

        feature_registry.register_feature(
            ValueFeature,
            {
                "points_per_million_threshold": 20.0,
                "price_efficiency_weight": 0.7,
                "ownership_penalty": 0.1,
            },
        )

        # Team features
        feature_registry.register_feature(
            TeamMomentumFeature,
            {
                "recent_results_weight": 0.4,
                "goal_difference_weight": 0.3,
                "expected_performance_weight": 0.3,
                "lookback_gameweeks": 5,
            },
        )

        feature_registry.register_feature(
            TeamScheduleFeature,
            {"lookahead_gameweeks": 5, "home_advantage": 0.5, "away_penalty": -0.5},
        )

        logger.info(
            f"Registered {len(feature_registry.get_all_feature_names())} features"
        )

        # Calculate all features
        logger.info("Calculating all features...")
        all_features = feature_registry.calculate_all_features(data)

        logger.info(f"Calculated {len(all_features)} features")

        # Display feature information
        logger.info("Feature information:")
        feature_info = feature_registry.get_feature_info()
        for feature_name, info in feature_info.items():
            logger.info(f"  {feature_name}: {info['description']} ({info['type']})")

        # Test individual features
        logger.info("Testing individual features...")

        # Test form consistency feature
        form_feature = feature_registry.get_feature_instance("FormConsistencyFeature")
        if form_feature:
            form_values = form_feature.calculate_with_validation(data)
            logger.info(
                f"Form consistency feature: {len(form_values)} values, range: {form_values.min():.2f}-{form_values.max():.2f}"
            )

        # Test quality feature
        quality_feature = feature_registry.get_feature_instance("QualityFeature")
        if quality_feature:
            quality_values = quality_feature.calculate_with_validation(data)
            logger.info(
                f"Quality feature: {len(quality_values)} values, range: {quality_values.min():.2f}-{quality_values.max():.2f}"
            )

        # Test fixture difficulty feature
        fixture_feature = feature_registry.get_feature_instance(
            "FixtureDifficultyFeature"
        )
        if fixture_feature:
            fixture_values = fixture_feature.calculate_with_validation(data)
            logger.info(
                f"Fixture difficulty feature: {len(fixture_values)} values, range: {fixture_values.min():.2f}-{fixture_values.max():.2f}"
            )

        # Test value feature
        value_feature = feature_registry.get_feature_instance("ValueFeature")
        if value_feature:
            value_values = value_feature.calculate_with_validation(data)
            logger.info(
                f"Value feature: {len(value_values)} values, range: {value_values.min():.2f}-{value_values.max():.2f}"
            )

        # Test team features
        team_momentum_feature = feature_registry.get_feature_instance(
            "TeamMomentumFeature"
        )
        if team_momentum_feature:
            momentum_values = team_momentum_feature.calculate_with_validation(data)
            logger.info(
                f"Team momentum feature: {len(momentum_values)} values, range: {momentum_values.min():.2f}-{momentum_values.max():.2f}"
            )

        team_schedule_feature = feature_registry.get_feature_instance(
            "TeamScheduleFeature"
        )
        if team_schedule_feature:
            schedule_values = team_schedule_feature.calculate_with_validation(data)
            logger.info(
                f"Team schedule feature: {len(schedule_values)} values, range: {schedule_values.min():.2f}-{schedule_values.max():.2f}"
            )

        # Test feature types
        logger.info("Testing feature types...")
        player_features = feature_registry.get_features_by_type("player")
        team_features = feature_registry.get_features_by_type("team")
        contextual_features = feature_registry.get_features_by_type("contextual")

        logger.info(f"Player features: {player_features}")
        logger.info(f"Team features: {team_features}")
        logger.info(f"Contextual features: {contextual_features}")

        # Test feature calculation by type
        logger.info("Testing feature calculation by type...")
        player_feature_results = feature_registry.calculate_features_by_type(
            data, "player"
        )
        team_feature_results = feature_registry.calculate_features_by_type(data, "team")

        logger.info(f"Player feature results: {len(player_feature_results)} features")
        logger.info(f"Team feature results: {len(team_feature_results)} features")

        # Display sample results
        logger.info("Sample feature results:")
        for feature_name, feature_values in all_features.items():
            if feature_values is not None and len(feature_values) > 0:
                logger.info(
                    f"  {feature_name}: mean={feature_values.mean():.2f}, std={feature_values.std():.2f}"
                )

        logger.info("Feature engineering test completed successfully!")

    except Exception as e:
        logger.error(f"Feature engineering test failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(test_feature_engineering())
