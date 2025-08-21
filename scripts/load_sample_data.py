#!/usr/bin/env python3
"""
Load Sample Data Script

This script loads sample FPL data into the PostgreSQL database for testing
the complete data flow: Database → Prediction Engine → Redis Cache → API
"""

import sys
import os
import asyncio
import logging
from typing import List, Dict, Any

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from storage.database import DatabaseManager
from config.settings import get_settings
from scripts.run_prediction_optimization import create_sample_squad, create_available_players

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def create_sample_players() -> List[Dict[str, Any]]:
    """Create a comprehensive list of sample players for testing."""
    
    sample_players = [
        # Goalkeepers
        {
            'fpl_id': 1,
            'name': 'Alisson',
            'team': 'Liverpool',
            'position': 'GK',
            'price': 5.5,
            'form': 6.2,
            'total_points': 120,
            'minutes_played': 2700,
            'goals': 0,
            'assists': 0,
            'clean_sheets': 12,
            'saves': 85,
            'goals_conceded': 25,
            'bonus_points': 8,
            'injury_history': [],
            'age': 31,
            'rotation_risk': False
        },
        {
            'fpl_id': 2,
            'name': 'Ederson',
            'team': 'Man City',
            'position': 'GK',
            'price': 5.5,
            'form': 6.5,
            'total_points': 125,
            'minutes_played': 2700,
            'goals': 0,
            'assists': 0,
            'clean_sheets': 11,
            'saves': 65,
            'goals_conceded': 22,
            'bonus_points': 8,
            'injury_history': [],
            'age': 30,
            'rotation_risk': False
        },
        {
            'fpl_id': 3,
            'name': 'Raya',
            'team': 'Arsenal',
            'position': 'GK',
            'price': 5.0,
            'form': 5.8,
            'total_points': 110,
            'minutes_played': 2700,
            'goals': 0,
            'assists': 0,
            'clean_sheets': 10,
            'saves': 78,
            'goals_conceded': 28,
            'bonus_points': 6,
            'injury_history': [],
            'age': 28,
            'rotation_risk': False
        },
        
        # Defenders
        {
            'fpl_id': 4,
            'name': 'Alexander-Arnold',
            'team': 'Liverpool',
            'position': 'DEF',
            'price': 8.5,
            'form': 7.5,
            'total_points': 180,
            'minutes_played': 2700,
            'goals': 3,
            'assists': 12,
            'clean_sheets': 8,
            'saves': 0,
            'goals_conceded': 0,
            'bonus_points': 15,
            'injury_history': [],
            'age': 25,
            'rotation_risk': False
        },
        {
            'fpl_id': 5,
            'name': 'Van Dijk',
            'team': 'Liverpool',
            'position': 'DEF',
            'price': 6.5,
            'form': 6.8,
            'total_points': 145,
            'minutes_played': 2700,
            'goals': 3,
            'assists': 1,
            'clean_sheets': 9,
            'saves': 0,
            'goals_conceded': 0,
            'bonus_points': 12,
            'injury_history': [],
            'age': 32,
            'rotation_risk': False
        },
        {
            'fpl_id': 6,
            'name': 'Saliba',
            'team': 'Arsenal',
            'position': 'DEF',
            'price': 5.5,
            'form': 6.8,
            'total_points': 140,
            'minutes_played': 2700,
            'goals': 2,
            'assists': 1,
            'clean_sheets': 10,
            'saves': 0,
            'goals_conceded': 0,
            'bonus_points': 8,
            'injury_history': [],
            'age': 22,
            'rotation_risk': False
        },
        {
            'fpl_id': 7,
            'name': 'Trippier',
            'team': 'Newcastle',
            'position': 'DEF',
            'price': 6.5,
            'form': 6.2,
            'total_points': 130,
            'minutes_played': 2700,
            'goals': 1,
            'assists': 8,
            'clean_sheets': 7,
            'saves': 0,
            'goals_conceded': 0,
            'bonus_points': 10,
            'injury_history': [],
            'age': 33,
            'rotation_risk': False
        },
        {
            'fpl_id': 8,
            'name': 'Estupinan',
            'team': 'Brighton',
            'position': 'DEF',
            'price': 5.0,
            'form': 5.5,
            'total_points': 95,
            'minutes_played': 2400,
            'goals': 1,
            'assists': 4,
            'clean_sheets': 5,
            'saves': 0,
            'goals_conceded': 0,
            'bonus_points': 5,
            'injury_history': [],
            'age': 25,
            'rotation_risk': False
        },
        
        # Midfielders
        {
            'fpl_id': 9,
            'name': 'Salah',
            'team': 'Liverpool',
            'position': 'MID',
            'price': 13.0,
            'form': 8.2,
            'total_points': 220,
            'minutes_played': 2700,
            'goals': 18,
            'assists': 12,
            'clean_sheets': 0,
            'saves': 0,
            'goals_conceded': 0,
            'bonus_points': 25,
            'injury_history': [],
            'age': 31,
            'rotation_risk': False
        },
        {
            'fpl_id': 10,
            'name': 'De Bruyne',
            'team': 'Man City',
            'position': 'MID',
            'price': 10.5,
            'form': 8.0,
            'total_points': 150,
            'minutes_played': 1800,
            'goals': 8,
            'assists': 15,
            'clean_sheets': 0,
            'saves': 0,
            'goals_conceded': 0,
            'bonus_points': 20,
            'injury_history': ['Hamstring', 'Knee'],
            'age': 32,
            'rotation_risk': True
        },
        {
            'fpl_id': 11,
            'name': 'Saka',
            'team': 'Arsenal',
            'position': 'MID',
            'price': 9.0,
            'form': 7.5,
            'total_points': 180,
            'minutes_played': 2700,
            'goals': 12,
            'assists': 10,
            'clean_sheets': 0,
            'saves': 0,
            'goals_conceded': 0,
            'bonus_points': 18,
            'injury_history': [],
            'age': 22,
            'rotation_risk': False
        },
        {
            'fpl_id': 12,
            'name': 'Foden',
            'team': 'Man City',
            'position': 'MID',
            'price': 8.0,
            'form': 7.8,
            'total_points': 170,
            'minutes_played': 2400,
            'goals': 14,
            'assists': 8,
            'clean_sheets': 0,
            'saves': 0,
            'goals_conceded': 0,
            'bonus_points': 15,
            'injury_history': [],
            'age': 23,
            'rotation_risk': True
        },
        {
            'fpl_id': 13,
            'name': 'Palmer',
            'team': 'Chelsea',
            'position': 'MID',
            'price': 6.0,
            'form': 6.5,
            'total_points': 120,
            'minutes_played': 2100,
            'goals': 8,
            'assists': 6,
            'clean_sheets': 0,
            'saves': 0,
            'goals_conceded': 0,
            'bonus_points': 8,
            'injury_history': [],
            'age': 21,
            'rotation_risk': False
        },
        {
            'fpl_id': 14,
            'name': 'Gordon',
            'team': 'Newcastle',
            'position': 'MID',
            'price': 6.5,
            'form': 6.2,
            'total_points': 110,
            'minutes_played': 2400,
            'goals': 6,
            'assists': 7,
            'clean_sheets': 0,
            'saves': 0,
            'goals_conceded': 0,
            'bonus_points': 6,
            'injury_history': [],
            'age': 22,
            'rotation_risk': False
        },
        {
            'fpl_id': 15,
            'name': 'Bowen',
            'team': 'West Ham',
            'position': 'MID',
            'price': 7.5,
            'form': 7.2,
            'total_points': 155,
            'minutes_played': 2700,
            'goals': 12,
            'assists': 8,
            'clean_sheets': 0,
            'saves': 0,
            'goals_conceded': 0,
            'bonus_points': 12,
            'injury_history': [],
            'age': 27,
            'rotation_risk': False
        },
        
        # Forwards
        {
            'fpl_id': 16,
            'name': 'Haaland',
            'team': 'Man City',
            'position': 'FWD',
            'price': 14.0,
            'form': 8.5,
            'total_points': 240,
            'minutes_played': 2400,
            'goals': 25,
            'assists': 5,
            'clean_sheets': 0,
            'saves': 0,
            'goals_conceded': 0,
            'bonus_points': 30,
            'injury_history': [],
            'age': 23,
            'rotation_risk': False
        },
        {
            'fpl_id': 17,
            'name': 'Watkins',
            'team': 'Aston Villa',
            'position': 'FWD',
            'price': 8.5,
            'form': 7.2,
            'total_points': 160,
            'minutes_played': 2700,
            'goals': 15,
            'assists': 8,
            'clean_sheets': 0,
            'saves': 0,
            'goals_conceded': 0,
            'bonus_points': 12,
            'injury_history': [],
            'age': 28,
            'rotation_risk': False
        },
        {
            'fpl_id': 18,
            'name': 'Solanke',
            'team': 'Bournemouth',
            'position': 'FWD',
            'price': 6.5,
            'form': 6.8,
            'total_points': 130,
            'minutes_played': 2700,
            'goals': 12,
            'assists': 4,
            'clean_sheets': 0,
            'saves': 0,
            'goals_conceded': 0,
            'bonus_points': 8,
            'injury_history': [],
            'age': 26,
            'rotation_risk': False
        },
        {
            'fpl_id': 19,
            'name': 'Isak',
            'team': 'Newcastle',
            'position': 'FWD',
            'price': 7.5,
            'form': 7.5,
            'total_points': 140,
            'minutes_played': 2100,
            'goals': 14,
            'assists': 3,
            'clean_sheets': 0,
            'saves': 0,
            'goals_conceded': 0,
            'bonus_points': 10,
            'injury_history': ['Hamstring'],
            'age': 24,
            'rotation_risk': False
        },
        {
            'fpl_id': 20,
            'name': 'Darwin',
            'team': 'Liverpool',
            'position': 'FWD',
            'price': 7.5,
            'form': 6.8,
            'total_points': 125,
            'minutes_played': 2200,
            'goals': 12,
            'assists': 6,
            'clean_sheets': 0,
            'saves': 0,
            'goals_conceded': 0,
            'bonus_points': 10,
            'injury_history': [],
            'age': 24,
            'rotation_risk': True
        }
    ]
    
    return sample_players


async def load_sample_data():
    """Load sample data into the database."""
    settings = get_settings()
    db_manager = DatabaseManager(settings.database_url)
    
    try:
        # Connect to database
        await db_manager.connect()
        logger.info("Connected to database")
        
        # Create tables
        await db_manager.create_tables()
        logger.info("Database tables created")
        
        # Load sample players
        sample_players = create_sample_players()
        logger.info(f"Loading {len(sample_players)} sample players...")
        
        inserted_count = 0
        updated_count = 0
        
        for player in sample_players:
            try:
                player_id = await db_manager.upsert_player(player)
                if player_id:
                    inserted_count += 1
                    logger.debug(f"Loaded player: {player['name']} ({player['team']})")
            except Exception as e:
                logger.error(f"Failed to load player {player['name']}: {e}")
        
        # Log data collection activity
        await db_manager.log_data_collection(
            source="sample_data_loader",
            data_type="players",
            records_processed=len(sample_players),
            records_inserted=inserted_count,
            records_updated=updated_count,
            duration_seconds=0.0,
            status="success"
        )
        
        logger.info(f"Successfully loaded {inserted_count} players into database")
        
        # Verify data
        all_players = await db_manager.get_all_players()
        logger.info(f"Database now contains {len(all_players)} players")
        
        # Show some statistics
        positions = ['GK', 'DEF', 'MID', 'FWD']
        for position in positions:
            players = await db_manager.get_players_by_position(position)
            logger.info(f"{position}: {len(players)} players")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to load sample data: {e}")
        return False
        
    finally:
        await db_manager.disconnect()


async def main():
    """Main execution function."""
    print("📊 Loading Sample FPL Data")
    print("=" * 50)
    
    success = await load_sample_data()
    
    if success:
        print("\n✅ Sample data loaded successfully!")
        print("\n📋 Next steps:")
        print("1. Start the API: docker-compose up fpl-api")
        print("2. Test the data flow: python scripts/test_complete_system.py")
        print("3. Check API endpoints: curl http://localhost:8000/api/v1/health")
        return 0
    else:
        print("\n❌ Failed to load sample data")
        return 1


if __name__ == "__main__":
    exit(asyncio.run(main())) 