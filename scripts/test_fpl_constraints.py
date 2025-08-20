#!/usr/bin/env python3
"""
Test FPL Constraint Checker

This script tests the FPL constraint checker by validating squad compositions and transfer moves.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from prediction.data.prediction_data_loader import prediction_data_loader
from prediction.optimization.constraints.fpl_constraints import (
    FPLConstraintChecker,
    SquadConstraints,
    TransferConstraints,
    Formation,
)
from storage.database import db_manager
from utils.logger import get_logger

logger = get_logger("test_fpl_constraints")


async def test_fpl_constraints():
    """Test the FPL constraint checker"""
    logger.info("Starting FPL constraint checker test")

    try:
        # Initialize database
        logger.info("Initializing database...")
        db_manager.initialize()

        # Load data
        logger.info("Loading prediction data...")
        data = await prediction_data_loader.get_prediction_data()

        logger.info(f"Loaded {len(data['players'])} players")

        # Initialize constraint checker
        logger.info("Initializing FPL constraint checker...")

        squad_constraints = SquadConstraints(
            max_players=15, max_players_per_team=3, budget_limit=100.0
        )

        transfer_constraints = TransferConstraints(
            free_transfers=1, max_transfers_per_gw=15, transfer_cost=4.0
        )

        constraint_checker = FPLConstraintChecker(
            squad_constraints, transfer_constraints
        )

        # Test 1: Valid squad composition
        logger.info("\nTest 1: Valid squad composition")

        # Create a valid squad (3-4-3 formation)
        valid_squad = []

        # Add 2 goalkeepers
        gk_players = data["players"][data["players"]["position"] == "GK"].head(2)
        for _, player in gk_players.iterrows():
            valid_squad.append(player.to_dict())

        # Add 3 defenders
        def_players = data["players"][data["players"]["position"] == "DEF"].head(3)
        for _, player in def_players.iterrows():
            valid_squad.append(player.to_dict())

        # Add 4 midfielders
        mid_players = data["players"][data["players"]["position"] == "MID"].head(4)
        for _, player in mid_players.iterrows():
            valid_squad.append(player.to_dict())

        # Add 3 forwards
        fwd_players = data["players"][data["players"]["position"] == "FWD"].head(3)
        for _, player in fwd_players.iterrows():
            valid_squad.append(player.to_dict())

        # Add 3 bench players (different positions)
        bench_players = data["players"][
            ~data["players"]["id"].isin([p["id"] for p in valid_squad])
        ].head(3)
        for _, player in bench_players.iterrows():
            valid_squad.append(player.to_dict())

        logger.info(f"Created squad with {len(valid_squad)} players")

        # Validate squad
        squad_validation = constraint_checker.validate_squad_composition(valid_squad)

        logger.info(f"Squad validation result: {squad_validation['is_valid']}")
        if squad_validation["squad_stats"]:
            stats = squad_validation["squad_stats"]
            logger.info(f"  Total players: {stats['total_players']}")
            logger.info(f"  Position counts: {stats['position_counts']}")
            logger.info(f"  Total cost: {stats['total_cost']:.1f}")
            logger.info(f"  Formation: {stats['formation']}")
            logger.info(f"  Budget remaining: {stats['budget_remaining']:.1f}")

        if squad_validation["errors"]:
            logger.error("Squad validation errors:")
            for error in squad_validation["errors"]:
                logger.error(f"  {error}")

        if squad_validation["warnings"]:
            logger.warning("Squad validation warnings:")
            for warning in squad_validation["warnings"]:
                logger.warning(f"  {warning}")

        # Test 2: Invalid squad (too many players)
        logger.info("\nTest 2: Invalid squad (too many players)")

        invalid_squad = valid_squad.copy()
        extra_player = (
            data["players"][
                ~data["players"]["id"].isin([p["id"] for p in invalid_squad])
            ]
            .iloc[0]
            .to_dict()
        )
        invalid_squad.append(extra_player)

        invalid_validation = constraint_checker.validate_squad_composition(
            invalid_squad
        )
        logger.info(
            f"Invalid squad validation result: {invalid_validation['is_valid']}"
        )

        if invalid_validation["errors"]:
            logger.error("Invalid squad errors:")
            for error in invalid_validation["errors"]:
                logger.error(f"  {error}")

        # Test 3: Valid transfer
        logger.info("\nTest 3: Valid transfer")

        # Get two midfielders for transfer
        mid_players_list = (
            data["players"][data["players"]["position"] == "MID"]
            .head(5)
            .to_dict("records")
        )

        if len(mid_players_list) >= 2:
            player_out = mid_players_list[0]
            player_in = mid_players_list[1]

            transfer = {"player_out": player_out, "player_in": player_in}

            transfer_validation = constraint_checker.validate_transfer(
                valid_squad, [transfer]
            )

            logger.info(
                f"Transfer validation result: {transfer_validation['is_valid']}"
            )
            logger.info(f"Transfer cost: {transfer_validation['transfer_cost']:.1f}")

            if transfer_validation["errors"]:
                logger.error("Transfer validation errors:")
                for error in transfer_validation["errors"]:
                    logger.error(f"  {error}")

            if transfer_validation["warnings"]:
                logger.warning("Transfer validation warnings:")
                for warning in transfer_validation["warnings"]:
                    logger.warning(f"  {warning}")

        # Test 4: Invalid transfer (too many transfers)
        logger.info("\nTest 4: Invalid transfer (too many transfers)")

        # Create multiple transfers
        multiple_transfers = []
        for i in range(5):  # More than free transfers
            if i + 2 < len(mid_players_list):
                transfer = {
                    "player_out": mid_players_list[i],
                    "player_in": mid_players_list[i + 1],
                }
                multiple_transfers.append(transfer)

        multiple_transfer_validation = constraint_checker.validate_transfer(
            valid_squad, multiple_transfers
        )

        logger.info(
            f"Multiple transfer validation result: {multiple_transfer_validation['is_valid']}"
        )
        logger.info(
            f"Transfer cost: {multiple_transfer_validation['transfer_cost']:.1f}"
        )

        if multiple_transfer_validation["errors"]:
            logger.error("Multiple transfer errors:")
            for error in multiple_transfer_validation["errors"]:
                logger.error(f"  {error}")

        # Test 5: Formation validation
        logger.info("\nTest 5: Formation validation")

        # Test different formations
        formations = [
            Formation.F_3_4_3,
            Formation.F_4_4_2,
            Formation.F_3_5_2,
            Formation.F_4_3_3,
        ]

        for formation in formations:
            requirements = constraint_checker.get_formation_requirements(formation)
            logger.info(f"Formation {formation.value} requirements: {requirements}")

        # Test 6: Budget validation
        logger.info("\nTest 6: Budget validation")

        # Create expensive squad
        expensive_squad = []
        expensive_players = data["players"].nlargest(15, "price")

        for _, player in expensive_players.iterrows():
            expensive_squad.append(player.to_dict())

        budget_validation = constraint_checker.validate_squad_composition(
            expensive_squad
        )

        logger.info(
            f"Expensive squad validation result: {budget_validation['is_valid']}"
        )

        if budget_validation["squad_stats"]:
            stats = budget_validation["squad_stats"]
            logger.info(f"  Total cost: {stats['total_cost']:.1f}")
            logger.info(f"  Budget limit: {squad_constraints.budget_limit:.1f}")
            logger.info(f"  Budget remaining: {stats['budget_remaining']:.1f}")

        if budget_validation["errors"]:
            logger.error("Budget validation errors:")
            for error in budget_validation["errors"]:
                logger.error(f"  {error}")

        # Test 7: Team limit validation
        logger.info("\nTest 7: Team limit validation")

        # Create squad with too many players from one team
        team_squad = []
        team_name = data["players"]["team"].iloc[0]
        team_players = data["players"][data["players"]["team"] == team_name].head(
            4
        )  # More than max per team

        for _, player in team_players.iterrows():
            team_squad.append(player.to_dict())

        # Add other players to complete squad
        other_players = data["players"][data["players"]["team"] != team_name].head(11)
        for _, player in other_players.iterrows():
            team_squad.append(player.to_dict())

        team_validation = constraint_checker.validate_squad_composition(team_squad)

        logger.info(f"Team limit validation result: {team_validation['is_valid']}")

        if team_validation["errors"]:
            logger.error("Team limit validation errors:")
            for error in team_validation["errors"]:
                logger.error(f"  {error}")

        logger.info("FPL constraint checker test completed successfully!")

    except Exception as e:
        logger.error(f"FPL constraint checker test failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(test_fpl_constraints())
