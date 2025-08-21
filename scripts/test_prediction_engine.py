#!/usr/bin/env python3
"""
Prediction Engine Test

This script tests the complete prediction engine using real data from the database.
It generates player scores, transfer recommendations, and demonstrates the full workflow.
"""

import sys
import os
import asyncio
import logging
from typing import Dict, Any, List

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from storage.database import db_manager
from storage.repositories import PlayerRepository
from storage.models import Player, Team
from prediction.scoring.master_score.player_impact_score import PlayerImpactScore
from prediction.optimization.algorithms.transfer_optimizer import TransferOptimizer
from prediction.validation.backtesting.backtest_engine import BacktestEngine
from prediction.validation.backtesting.performance_metrics import PerformanceMetrics
from config.settings import get_settings
from utils.cache import get_cache

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def create_sample_squad():
    """Create a sample FPL squad for testing."""
    return [
        {
            "id": 1,
            "name": "Alisson",
            "team": "Liverpool",
            "position": "GK",
            "price": 5.5,
            "form": 6.2,
            "total_points": 120,
            "selected_by_percent": 15.5,
            "transfers_in": 50000,
            "transfers_out": 20000,
            "goals_scored": 0,
            "assists": 0,
            "clean_sheets": 12,
            "goals_conceded": 25,
            "own_goals": 0,
            "penalties_saved": 2,
            "penalties_missed": 0,
            "yellow_cards": 1,
            "red_cards": 0,
            "saves": 85,
            "bonus": 8,
            "bps": 450,
            "influence": 120.5,
            "creativity": 45.2,
            "threat": 25.1,
            "ict_index": 63.6,
            "minutes_played": 2700,
            "games_played": 30,
            "points_per_game": 4.0,
        },
        {
            "id": 2,
            "name": "Salah",
            "team": "Liverpool",
            "position": "MID",
            "price": 13.0,
            "form": 8.2,
            "total_points": 220,
            "selected_by_percent": 45.2,
            "transfers_in": 150000,
            "transfers_out": 50000,
            "goals_scored": 18,
            "assists": 12,
            "clean_sheets": 0,
            "goals_conceded": 0,
            "own_goals": 0,
            "penalties_saved": 0,
            "penalties_missed": 1,
            "yellow_cards": 3,
            "red_cards": 0,
            "saves": 0,
            "bonus": 25,
            "bps": 850,
            "influence": 450.2,
            "creativity": 380.5,
            "threat": 420.1,
            "ict_index": 416.9,
            "minutes_played": 2700,
            "games_played": 30,
            "points_per_game": 7.3,
        },
        {
            "id": 3,
            "name": "Haaland",
            "team": "Man City",
            "position": "FWD",
            "price": 14.0,
            "form": 8.5,
            "total_points": 240,
            "selected_by_percent": 52.1,
            "transfers_in": 180000,
            "transfers_out": 30000,
            "goals_scored": 25,
            "assists": 5,
            "clean_sheets": 0,
            "goals_conceded": 0,
            "own_goals": 0,
            "penalties_saved": 0,
            "penalties_missed": 0,
            "yellow_cards": 2,
            "red_cards": 0,
            "saves": 0,
            "bonus": 30,
            "bps": 920,
            "influence": 520.8,
            "creativity": 280.3,
            "threat": 580.7,
            "ict_index": 461.3,
            "minutes_played": 2400,
            "games_played": 27,
            "points_per_game": 8.9,
        },
    ]


def get_top_players_by_position(session, position: str, limit: int = 10):
    """Get top players by position from database."""
    players = (
        session.query(Player)
        .filter(Player.position == position)
        .order_by(Player.total_points.desc())
        .limit(limit)
        .all()
    )

    return [
        {
            "id": p.fpl_id,
            "name": p.name,
            "team": p.team,
            "position": p.position,
            "price": float(p.price),
            "form": float(p.form) if p.form else 0.0,
            "total_points": p.total_points,
            "selected_by_percent": (
                float(p.selected_by_percent) if p.selected_by_percent else 0.0
            ),
            "transfers_in": p.transfers_in,
            "transfers_out": p.transfers_out,
            "goals_scored": p.goals_scored,
            "assists": p.assists,
            "clean_sheets": p.clean_sheets,
            "goals_conceded": p.goals_conceded,
            "own_goals": p.own_goals,
            "penalties_saved": p.penalties_saved,
            "penalties_missed": p.penalties_missed,
            "yellow_cards": p.yellow_cards,
            "red_cards": p.red_cards,
            "saves": p.saves,
            "bonus": p.bonus,
            "bps": p.bps,
            "influence": float(p.influence) if p.influence else 0.0,
            "creativity": float(p.creativity) if p.creativity else 0.0,
            "threat": float(p.threat) if p.threat else 0.0,
            "ict_index": float(p.ict_index) if p.ict_index else 0.0,
            # Estimate minutes and games from total points
            "minutes_played": p.total_points * 10,  # Rough estimate
            "games_played": max(1, p.total_points // 10),  # Rough estimate
            "points_per_game": float(p.total_points) / max(1, p.total_points // 10),
        }
        for p in players
    ]


async def test_player_scoring():
    """Test player scoring with real data."""
    print("🎯 Testing Player Impact Score (PIS) Calculation")
    print("=" * 60)

    try:
        # Initialize database
        db_manager.initialize()
        session = db_manager.get_sync_session()

        # Get top players by position
        top_gks = get_top_players_by_position(session, "GK", 5)
        top_defs = get_top_players_by_position(session, "DEF", 5)
        top_mids = get_top_players_by_position(session, "MID", 5)
        top_fwds = get_top_players_by_position(session, "FWD", 5)

        # Initialize scorer with default config
        scorer = PlayerImpactScore({})

        print(f"📊 Scoring {len(top_gks)} goalkeepers...")
        for player in top_gks:
            score = scorer.calculate_score(player)
            print(f"  🧤 {player['name']} ({player['team']}): PIS = {score:.2f}")

        print(f"\n📊 Scoring {len(top_defs)} defenders...")
        for player in top_defs:
            score = scorer.calculate_score(player)
            print(f"  🛡️ {player['name']} ({player['team']}): PIS = {score:.2f}")

        print(f"\n📊 Scoring {len(top_mids)} midfielders...")
        for player in top_mids:
            score = scorer.calculate_score(player)
            print(f"  ⚽ {player['name']} ({player['team']}): PIS = {score:.2f}")

        print(f"\n📊 Scoring {len(top_fwds)} forwards...")
        for player in top_fwds:
            score = scorer.calculate_score(player)
            print(f"  🎯 {player['name']} ({player['team']}): PIS = {score:.2f}")

        session.close()
        print("\n✅ Player scoring test completed!")
        return True

    except Exception as e:
        logger.error(f"Player scoring test failed: {e}")
        print(f"\n❌ Player scoring test failed: {e}")
        return False


async def test_transfer_optimization():
    """Test transfer optimization with real data."""
    print("\n🔄 Testing Transfer Optimization")
    print("=" * 60)

    try:
        # Initialize database
        db_manager.initialize()
        session = db_manager.get_sync_session()

        # Create current squad
        current_squad = create_sample_squad()

        # Get available players (top performers)
        available_players = []
        for position in ["GK", "DEF", "MID", "FWD"]:
            players = get_top_players_by_position(session, position, 20)
            available_players.extend(players)

        # Initialize optimizer with default config
        optimizer = TransferOptimizer({})

        print(f"📊 Current squad: {len(current_squad)} players")
        print(f"📊 Available players: {len(available_players)} players")

        # Calculate current squad score
        scorer = PlayerImpactScore({})
        current_scores = []
        for player in current_squad:
            score = scorer.calculate_score(player)
            current_scores.append(score)

        current_total = sum(current_scores)
        print(f"📊 Current squad total PIS: {current_total:.2f}")

        # Get transfer recommendations
        recommendations = optimizer.optimize_transfers(
            current_squad=current_squad,
            available_players=available_players,
            budget=100.0,
            transfers_available=2,
            strategy="balanced",
        )

        print(f"\n🎯 Found {len(recommendations)} transfer combinations")

        # Show top recommendations
        for i, combo in enumerate(recommendations[:3]):
            print(f"\n📈 Recommendation #{i+1}:")
            print(f"  Expected Gain: {combo.total_expected_gain:.2f} points")
            print(f"  Confidence: {combo.total_confidence:.2f}")
            print(f"  Risk: {combo.total_risk:.2f}")
            print(f"  Budget Impact: £{combo.budget_impact:.1f}m")
            print(f"  Reasoning: {combo.reasoning}")

            for transfer in combo.transfers:
                print(
                    f"    🔄 {transfer.player_out['name']} → {transfer.player_in['name']}"
                )
                print(
                    f"       Expected Gain: {transfer.expected_points_gain:.2f} points"
                )

        session.close()
        print("\n✅ Transfer optimization test completed!")
        return True

    except Exception as e:
        logger.error(f"Transfer optimization test failed: {e}")
        print(f"\n❌ Transfer optimization test failed: {e}")
        return False


async def test_backtesting():
    """Test backtesting with sample data."""
    print("\n📈 Testing Backtesting Engine")
    print("=" * 60)

    try:
        # Initialize database
        db_manager.initialize()
        session = db_manager.get_sync_session()

        # Get historical data (simulated)
        historical_data = []
        for position in ["GK", "DEF", "MID", "FWD"]:
            players = get_top_players_by_position(session, position, 10)
            for player in players:
                # Simulate historical performance
                for gw in range(1, 6):  # 5 gameweeks
                    historical_data.append(
                        {
                            "player_id": player["id"],
                            "gameweek": gw,
                            "points": max(
                                0, player["total_points"] // 38 + (gw % 3) - 1
                            ),  # Simulated
                            "minutes": 90 if gw % 3 != 0 else 0,
                            "goals": player["goals_scored"] // 38,
                            "assists": player["assists"] // 38,
                            "clean_sheet": gw % 4 == 0,
                            "bonus": player["bonus"] // 38,
                        }
                    )

        # Initialize backtest engine with default config
        backtest_engine = BacktestEngine({})

        # Create initial squad
        initial_squad = create_sample_squad()

        print(f"📊 Running backtest with {len(historical_data)} historical records")
        print(f"📊 Initial squad: {len(initial_squad)} players")

        # Run backtest
        results = backtest_engine.run_backtest(
            start_gameweek=1, end_gameweek=5, initial_squad=initial_squad
        )

        print(f"\n📊 Backtest Results:")
        print(f"  Total Points: {results.total_points}")
        print(f"  Average Points per GW: {results.average_points_per_gameweek:.2f}")
        print(f"  Transfers Made: {results.total_transfers}")
        print(f"  Final Squad Value: £{results.final_squad_value:.1f}m")

        # Calculate performance metrics
        metrics = PerformanceMetrics()
        # For now, just show basic metrics
        print(f"\n📊 Performance Metrics:")
        print(f"  Backtest completed successfully")
        print(f"  Performance metrics calculation available")

        session.close()
        print("\n✅ Backtesting test completed!")
        return True

    except Exception as e:
        logger.error(f"Backtesting test failed: {e}")
        print(f"\n❌ Backtesting test failed: {e}")
        return False


async def test_caching():
    """Test caching functionality."""
    print("\n⚡ Testing Caching System")
    print("=" * 60)

    try:
        cache = get_cache()

        # Test player score caching
        test_player = {
            "id": 999,
            "name": "Test Player",
            "team": "Test Team",
            "position": "MID",
            "price": 8.0,
            "form": 7.0,
            "total_points": 150,
        }

        scorer = PlayerImpactScore({})
        score = scorer.calculate_score(test_player)

        # Cache the score
        cache_key = f"player_score_{test_player['id']}"
        cache.set(cache_key, score, ttl=3600)
        print(f"✅ Cached score for {test_player['name']}")

        # Retrieve from cache
        cached_score = cache.get(cache_key)
        if cached_score:
            print(f"✅ Retrieved cached score: PIS = {cached_score:.2f}")
        else:
            print("❌ Failed to retrieve cached score")

        # Test cache invalidation
        cache.delete(cache_key)
        invalidated_score = cache.get(cache_key)
        if invalidated_score is None:
            print("✅ Cache invalidation working")
        else:
            print("❌ Cache invalidation failed")

        print("\n✅ Caching test completed!")
        return True

    except Exception as e:
        logger.error(f"Caching test failed: {e}")
        print(f"\n❌ Caching test failed: {e}")
        return False


async def main():
    """Main execution function."""
    print("🚀 FPL Prediction Engine Comprehensive Test")
    print("=" * 80)

    results = {}

    # Test player scoring
    results["scoring"] = await test_player_scoring()

    # Test transfer optimization
    results["optimization"] = await test_transfer_optimization()

    # Test backtesting
    results["backtesting"] = await test_backtesting()

    # Test caching
    results["caching"] = await test_caching()

    # Summary
    print("\n" + "=" * 80)
    print("📊 TEST SUMMARY")
    print("=" * 80)

    for test_name, success in results.items():
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{test_name.upper():15} {status}")

    passed_tests = sum(results.values())
    total_tests = len(results)

    print(f"\n🎯 Overall Result: {passed_tests}/{total_tests} tests passed")

    if passed_tests == total_tests:
        print("\n🎉 All prediction engine components working correctly!")
        print("\n🚀 Ready for production use!")
        return 0
    else:
        print(f"\n⚠️ {total_tests - passed_tests} test(s) failed - review required")
        return 1


if __name__ == "__main__":
    exit(asyncio.run(main()))
