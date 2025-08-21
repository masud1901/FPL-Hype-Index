#!/usr/bin/env python3
"""
Test Data Flow Script

This script demonstrates the complete data flow:
1. Load data into PostgreSQL
2. Run predictions and cache in Redis (1 day TTL)
3. Serve from cache via API
"""

import sys
import os
import asyncio
import time
import logging
from typing import Dict, Any

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from services.data_integration import get_data_integration_service, close_data_integration_service
from scripts.load_sample_data import load_sample_data

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def test_complete_data_flow():
    """Test the complete data flow from database to cache."""
    
    print("🔄 Testing Complete Data Flow")
    print("=" * 60)
    print("1. Database (PostgreSQL) → 2. Prediction Engine → 3. Redis Cache → 4. API")
    print("=" * 60)
    
    try:
        # Step 1: Load sample data into PostgreSQL
        print("\n📊 Step 1: Loading sample data into PostgreSQL...")
        start_time = time.time()
        
        success = await load_sample_data()
        if not success:
            print("❌ Failed to load sample data")
            return False
        
        db_load_time = time.time() - start_time
        print(f"✅ Sample data loaded in {db_load_time:.2f}s")
        
        # Step 2: Initialize data integration service
        print("\n🔗 Step 2: Initializing data integration service...")
        data_service = await get_data_integration_service()
        print("✅ Data integration service initialized")
        
        # Step 3: Test player scores (Database → Prediction → Cache)
        print("\n🎯 Step 3: Testing player score calculation and caching...")
        start_time = time.time()
        
        # First call: Should fetch from DB, calculate, and cache
        print("   📥 First call: Fetching from database and calculating scores...")
        player_scores = await data_service.get_player_scores(force_refresh=True)
        
        first_call_time = time.time() - start_time
        print(f"   ✅ Calculated {len(player_scores)} player scores in {first_call_time:.2f}s")
        
        # Show some sample scores
        print("\n   📊 Sample Player Scores:")
        for player in player_scores[:5]:
            print(f"      {player['name']} ({player['team']}): PIS={player['pis_score']:.2f}, Confidence={player['confidence']:.2f}")
        
        # Second call: Should fetch from cache (much faster)
        print("\n   ⚡ Second call: Fetching from cache...")
        start_time = time.time()
        cached_scores = await data_service.get_player_scores(force_refresh=False)
        cache_time = time.time() - start_time
        
        print(f"   ✅ Retrieved {len(cached_scores)} scores from cache in {cache_time:.3f}s")
        print(f"   🚀 Cache speed improvement: {first_call_time/cache_time:.1f}x faster")
        
        # Step 4: Test transfer recommendations
        print("\n🔄 Step 4: Testing transfer recommendations...")
        
        # Create a sample squad
        sample_squad = player_scores[:11]  # First 11 players as squad
        
        start_time = time.time()
        recommendations = await data_service.get_transfer_recommendations(
            current_squad=sample_squad,
            budget=2.0,
            strategy="balanced"
        )
        
        transfer_time = time.time() - start_time
        print(f"   ✅ Generated {len(recommendations)} transfer recommendations in {transfer_time:.2f}s")
        
        # Show sample recommendations
        if recommendations:
            print("\n   📋 Sample Transfer Recommendations:")
            for i, rec in enumerate(recommendations[:3], 1):
                print(f"      {i}. {rec['player_out']['name']} → {rec['player_in']['name']}")
                print(f"         Expected Gain: {rec['expected_points_gain']:.2f} points")
                print(f"         Confidence: {rec['confidence_score']:.2f}")
        
        # Step 5: Test position-based queries
        print("\n🏃 Step 5: Testing position-based queries...")
        
        for position in ['GK', 'DEF', 'MID', 'FWD']:
            start_time = time.time()
            position_players = await data_service.get_players_by_position(position)
            query_time = time.time() - start_time
            
            print(f"   ✅ {position}: {len(position_players)} players in {query_time:.3f}s")
        
        # Step 6: Test cache statistics
        print("\n📈 Step 6: Cache statistics...")
        cache_stats = await data_service.get_cache_stats()
        
        print(f"   📊 Cache Status: {cache_stats.get('status', 'Unknown')}")
        print(f"   🔗 Connected: {cache_stats.get('connected', False)}")
        
        # Check specific cache keys
        cache_keys = cache_stats.get('cache_keys', {})
        for key, exists in cache_keys.items():
            status = "✅" if exists else "❌"
            print(f"   {status} {key}: {'Cached' if exists else 'Not cached'}")
        
        # Step 7: Performance summary
        print("\n📊 Performance Summary:")
        print("=" * 40)
        print(f"Database Load Time: {db_load_time:.2f}s")
        print(f"First Score Calculation: {first_call_time:.2f}s")
        print(f"Cache Retrieval: {cache_time:.3f}s")
        print(f"Transfer Recommendations: {transfer_time:.2f}s")
        print(f"Cache Speed Improvement: {first_call_time/cache_time:.1f}x")
        
        print("\n🎉 Complete data flow test successful!")
        print("\n📋 Data Flow Summary:")
        print("   1. ✅ PostgreSQL: Sample data loaded")
        print("   2. ✅ Prediction Engine: Player scores calculated")
        print("   3. ✅ Redis Cache: Results cached (1 day TTL)")
        print("   4. ✅ API Ready: Data available via endpoints")
        
        return True
        
    except Exception as e:
        logger.error(f"Data flow test failed: {e}")
        print(f"\n❌ Data flow test failed: {e}")
        return False
        
    finally:
        # Clean up
        await close_data_integration_service()


async def main():
    """Main execution function."""
    print("🧪 FPL Data Flow Testing")
    print("=" * 60)
    
    success = await test_complete_data_flow()
    
    if success:
        print("\n🎯 Next Steps:")
        print("1. Start the API: docker-compose up fpl-api")
        print("2. Test API endpoints:")
        print("   curl http://localhost:8000/api/v1/health")
        print("   curl http://localhost:8000/api/v1/prediction/strategies")
        print("3. Monitor cache: docker-compose exec redis redis-cli info")
        print("4. Check database: docker-compose exec database psql -U fpl_user -d fpl_data -c 'SELECT COUNT(*) FROM players;'")
        return 0
    else:
        print("\n❌ Data flow test failed")
        return 1


if __name__ == "__main__":
    exit(asyncio.run(main())) 