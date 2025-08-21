#!/usr/bin/env python3
"""
Simple Test Script

This script tests the basic data flow using the existing database system.
"""

import sys
import os
import asyncio
import logging
from typing import Dict, Any

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from storage.database import db_manager
from storage.repositories import PlayerRepository
from storage.models import Player, Team
from config.settings import get_settings
from utils.cache import get_cache

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def create_sample_players():
    """Create sample player data for testing."""
    return [
        {
            "id": 1,
            "full_name": "Alisson",
            "team_name": "Liverpool",
            "position": "GK",
            "price": 5.5,
            "form_float": 6.2,
            "total_points": 120,
            "selected_by_percent_float": 15.5,
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
            "form": "6.2",
            "first_name": "Alisson",
            "second_name": "Becker",
        },
        {
            "id": 2,
            "full_name": "Salah",
            "team_name": "Liverpool",
            "position": "MID",
            "price": 13.0,
            "form_float": 8.2,
            "total_points": 220,
            "selected_by_percent_float": 45.2,
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
            "form": "8.2",
            "first_name": "Mohamed",
            "second_name": "Salah",
        },
        {
            "id": 3,
            "full_name": "Haaland",
            "team_name": "Man City",
            "position": "FWD",
            "price": 14.0,
            "form_float": 8.5,
            "total_points": 240,
            "selected_by_percent_float": 52.1,
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
            "form": "8.5",
            "first_name": "Erling",
            "second_name": "Haaland",
        },
    ]


async def test_database_flow():
    """Test the database flow with sample data."""

    print("🧪 Testing Database Flow")
    print("=" * 50)

    try:
        # Initialize database
        print("📊 Initializing database...")
        db_manager.initialize()
        print("✅ Database initialized")

        # Create tables
        print("🏗️ Creating tables...")
        db_manager.create_tables()
        print("✅ Tables created")

        # Test cache
        print("⚡ Testing Redis cache...")
        cache = get_cache()
        test_data = {"test": "data", "number": 42}
        cache.set("test_key", test_data, ttl=60)
        retrieved = cache.get("test_key")
        assert retrieved == test_data
        print("✅ Redis cache working")

        # Test player repository
        print("👥 Testing player repository...")
        player_repo = PlayerRepository()

        # Get a sync session
        session = db_manager.get_sync_session()

        # Create sample players
        sample_players = create_sample_players()
        created_players = []

        for player_data in sample_players:
            try:
                player = player_repo.create_or_update_player(session, player_data)
                created_players.append(player)
                print(f"  ✅ Created player: {player.name} ({player.team})")
            except Exception as e:
                print(
                    f"  ❌ Failed to create player {player_data.get('full_name')}: {e}"
                )

        # Commit the session
        session.commit()
        session.close()

        print(f"✅ Created {len(created_players)} players")

        # Test retrieving players
        print("📥 Testing player retrieval...")
        session = db_manager.get_sync_session()
        all_players = session.query(Player).all()
        print(f"✅ Retrieved {len(all_players)} players from database")

        # Show some player details
        for player in all_players[:3]:
            print(
                f"  📊 {player.name} ({player.team}): {player.total_points} points, £{player.price}m"
            )

        session.close()

        print("\n🎉 Database flow test successful!")
        return True

    except Exception as e:
        logger.error(f"Database flow test failed: {e}")
        print(f"\n❌ Database flow test failed: {e}")
        return False


async def main():
    """Main execution function."""
    print("🧪 Simple Database Test")
    print("=" * 50)

    success = await test_database_flow()

    if success:
        print("\n🎯 Next Steps:")
        print("1. Test API endpoints: curl http://localhost:8001/api/v1/health")
        print(
            "2. Check database: docker compose exec database psql -U fpl_user -d fpl_data -c 'SELECT COUNT(*) FROM players;'"
        )
        print("3. Check cache: docker compose exec redis redis-cli keys '*'")
        return 0
    else:
        print("\n❌ Test failed")
        return 1


if __name__ == "__main__":
    exit(asyncio.run(main()))
