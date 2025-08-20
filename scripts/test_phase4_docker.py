#!/usr/bin/env python3
"""
Docker test script for Phase 4 scrapers.

This script is designed to run inside the Docker container and test:
- Database connectivity
- All Phase 4 scrapers (Transfermarkt, WhoScored, Football-Data)
- Data validation and processing
- Integration with the orchestration system
"""

import asyncio
import sys
import os
from datetime import datetime
from typing import Dict, Any, List

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import config
from utils.logger import get_logger, setup_logging
from orchestration.coordinator import DataCoordinator
from storage.database import db_manager

# Ensure logging is set up
setup_logging()


async def test_database_connection():
    """Test database connectivity."""
    logger = get_logger(__name__)
    logger.info("Testing database connection")
    
    try:
        # Initialize database
        db_manager.initialize()
        db_manager.create_tables()
        
        # Test connection
        with db_manager.get_sync_session() as session:
            # Simple query to test connection
            from sqlalchemy import text
            result = session.execute(text("SELECT 1"))
            logger.info("Database connection successful")
            return True
            
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False


async def test_scraper_imports():
    """Test that all scrapers can be imported correctly."""
    logger = get_logger(__name__)
    logger.info("Testing scraper imports")
    
    scrapers_to_test = [
        "transfermarkt",
        "whoscored", 
        "football_data"
    ]
    
    results = {}
    
    for scraper_name in scrapers_to_test:
        try:
            # Test import
            coordinator = DataCoordinator()
            scraper_class = coordinator._get_scraper_class(scraper_name)
            
            # Test instantiation
            scraper = scraper_class(config.scraper.__dict__)
            
            results[scraper_name] = {
                "status": "success",
                "message": "Import and instantiation successful"
            }
            
            logger.info(f"{scraper_name} scraper import test passed")
            
        except Exception as e:
            results[scraper_name] = {
                "status": "failed",
                "error": str(e)
            }
            logger.error(f"{scraper_name} scraper import test failed: {e}")
    
    return results


async def test_scraper_data_validation():
    """Test data validation for each scraper."""
    logger = get_logger(__name__)
    logger.info("Testing scraper data validation")
    
    # Create sample data for validation testing
    sample_data = {
        "transfermarkt": {
            "players": [
                {
                    "id": "12345",
                    "name": "Test Player",
                    "position": "Forward",
                    "age": 25,
                    "market_value": 1000000,
                    "contract_until": "2025",
                    "last_club": "Test Club",
                    "source": "transfermarkt"
                }
            ] * 100,  # Create 100 players
            "teams": [
                {
                    "id": "123",
                    "name": "Test Team",
                    "url": "https://test.com",
                    "league": "Premier League",
                    "season": "2024/25"
                }
            ] * 20,  # Create 20 teams
            "transfers": [
                {
                    "player_name": "Test Player",
                    "position": "Forward",
                    "age": 25,
                    "transfer_type": "in",
                    "fee": 1000000,
                    "date": "2024-01-01",
                    "source": "transfermarkt"
                }
            ],
            "scraped_at": datetime.now().isoformat(),
            "source": "transfermarkt",
            "season": "2024/25",
            "league": "Premier League"
        },
        "whoscored": {
            "players": [
                {
                    "id": "12345",
                    "name": "Test Player",
                    "position": "Forward",
                    "age": 25,
                    "rating": 7.5,
                    "appearances": 10,
                    "source": "whoscored"
                }
            ] * 100,  # Create 100 players
            "teams": [
                {
                    "id": "123",
                    "name": "Test Team",
                    "url": "https://test.com",
                    "league": "Premier League",
                    "season": "2024/25"
                }
            ] * 20,  # Create 20 teams
            "matches": [
                {
                    "date": "2024-01-01",
                    "home_team": "Team A",
                    "away_team": "Team B",
                    "home_score": 2,
                    "away_score": 1,
                    "competition": "Premier League",
                    "result": "Home Win",
                    "source": "whoscored"
                }
            ],
            "scraped_at": datetime.now().isoformat(),
            "source": "whoscored",
            "season": "2024/25",
            "league": "Premier League"
        },
        "football_data": {
            "teams": [
                {
                    "id": 123,
                    "name": "Test Team",
                    "short_name": "TEST",
                    "tla": "TST",
                    "crest": "https://test.com/crest.png",
                    "source": "football_data"
                }
            ] * 20,  # Create 20 teams
            "matches": [
                {
                    "id": 456,
                    "home_team": {"id": 123, "name": "Team A"},
                    "away_team": {"id": 124, "name": "Team B"},
                    "score": {"full_time": {"home": 2, "away": 1}},
                    "status": "FINISHED",
                    "stage": "REGULAR_SEASON",
                    "source": "football_data"
                }
            ],
            "fixtures": [
                {
                    "id": 789,
                    "home_team": {"id": 123, "name": "Team A"},
                    "away_team": {"id": 124, "name": "Team B"},
                    "status": "SCHEDULED",
                    "stage": "REGULAR_SEASON",
                    "source": "football_data"
                }
            ],
            "scraped_at": datetime.now().isoformat(),
            "source": "football_data",
            "season": "2024/25",
            "league_name": "Premier League"
        }
    }
    
    from processors.data_validator import DataValidator
    validator = DataValidator()
    
    results = {}
    
    for scraper_name, data in sample_data.items():
        try:
            validation_result = await validator.validate(data, scraper_name)
            
            if validation_result["is_valid"]:
                results[scraper_name] = {
                    "status": "success",
                    "message": "Data validation passed",
                    "issues_count": validation_result["total_issues"]
                }
                logger.info(f"{scraper_name} data validation passed")
            else:
                results[scraper_name] = {
                    "status": "failed",
                    "message": "Data validation failed",
                    "issues": validation_result["issues"]
                }
                logger.error(f"{scraper_name} data validation failed: {validation_result['issues']}")
                
        except Exception as e:
            results[scraper_name] = {
                "status": "failed",
                "error": str(e)
            }
            logger.error(f"{scraper_name} data validation test failed: {e}")
    
    return results


async def test_coordinator_integration():
    """Test coordinator integration with new scrapers."""
    logger = get_logger(__name__)
    logger.info("Testing coordinator integration")
    
    try:
        coordinator = DataCoordinator()
        
        # Test that scrapers are registered
        available_scrapers = coordinator.get_available_scrapers()
        phase4_scrapers = ["transfermarkt", "whoscored", "football_data"]
        
        missing_scrapers = [s for s in phase4_scrapers if s not in available_scrapers]
        
        if missing_scrapers:
            return {
                "status": "failed",
                "error": f"Missing scrapers in coordinator: {missing_scrapers}"
            }
        
        logger.info("All Phase 4 scrapers are registered in coordinator")
        
        # Test scraper class loading (without running)
        for scraper_name in phase4_scrapers:
            try:
                scraper_class = coordinator._get_scraper_class(scraper_name)
                logger.info(f"{scraper_name} scraper class loaded successfully")
            except Exception as e:
                return {
                    "status": "failed",
                    "error": f"Failed to load {scraper_name} scraper class: {e}"
                }
        
        return {
            "status": "success",
            "message": "Coordinator integration test passed",
            "available_scrapers": available_scrapers
        }
        
    except Exception as e:
        logger.error(f"Coordinator integration test failed: {e}")
        return {
            "status": "failed",
            "error": str(e)
        }


async def test_limited_scraper_execution():
    """Test limited scraper execution (without full scraping)."""
    logger = get_logger(__name__)
    logger.info("Testing limited scraper execution")
    
    # Test Football-Data scraper without API key (should work in limited mode)
    try:
        coordinator = DataCoordinator()
        
        # This should work without API key
        result = await coordinator.run_scraper("football_data")
        
        if result["status"] == "success":
            logger.info("Football-Data scraper test passed (limited mode)")
            return {
                "status": "success",
                "message": "Limited scraper execution test passed",
                "result": result
            }
        else:
            return {
                "status": "failed",
                "error": f"Football-Data scraper failed: {result}"
            }
            
    except Exception as e:
        logger.error(f"Limited scraper execution test failed: {e}")
        return {
            "status": "failed",
            "error": str(e)
        }


async def run_all_tests():
    """Run all Phase 4 tests."""
    logger = get_logger(__name__)
    logger.info("Starting Phase 4 Docker tests")
    
    test_results = {}
    
    # Test 1: Database connection
    logger.info("=" * 50)
    logger.info("TEST 1: Database Connection")
    logger.info("=" * 50)
    test_results["database_connection"] = await test_database_connection()
    
    # Test 2: Scraper imports
    logger.info("=" * 50)
    logger.info("TEST 2: Scraper Imports")
    logger.info("=" * 50)
    test_results["scraper_imports"] = await test_scraper_imports()
    
    # Test 3: Data validation
    logger.info("=" * 50)
    logger.info("TEST 3: Data Validation")
    logger.info("=" * 50)
    test_results["data_validation"] = await test_scraper_data_validation()
    
    # Test 4: Coordinator integration
    logger.info("=" * 50)
    logger.info("TEST 4: Coordinator Integration")
    logger.info("=" * 50)
    test_results["coordinator_integration"] = await test_coordinator_integration()
    
    # Test 5: Limited scraper execution
    logger.info("=" * 50)
    logger.info("TEST 5: Limited Scraper Execution")
    logger.info("=" * 50)
    test_results["limited_execution"] = await test_limited_scraper_execution()
    
    return test_results


def print_test_results(results: Dict[str, Any]):
    """Print test results in a formatted way."""
    print("\n" + "=" * 60)
    print("PHASE 4 DOCKER TEST RESULTS")
    print("=" * 60)
    
    for test_name, result in results.items():
        print(f"\n{test_name.upper().replace('_', ' ')}:")
        print("-" * 40)
        
        if isinstance(result, bool):
            if result:
                print("✅ PASSED")
            else:
                print("❌ FAILED")
        elif isinstance(result, dict):
            if result.get("status") == "success":
                print("✅ PASSED")
                if "message" in result:
                    print(f"   {result['message']}")
                if "available_scrapers" in result:
                    print(f"   Available scrapers: {', '.join(result['available_scrapers'])}")
            else:
                print("❌ FAILED")
                if "error" in result:
                    print(f"   Error: {result['error']}")
                if "issues" in result:
                    print(f"   Issues: {result['issues']}")
        elif isinstance(result, dict) and "status" in result:
            # Handle scraper import results
            for scraper_name, scraper_result in result.items():
                if scraper_result.get("status") == "success":
                    print(f"   ✅ {scraper_name}: PASSED")
                else:
                    print(f"   ❌ {scraper_name}: FAILED - {scraper_result.get('error', 'Unknown error')}")
    
    # Overall summary
    print(f"\n{'=' * 60}")
    
    # Count successes and failures
    total_tests = len(results)
    successful_tests = 0
    
    for result in results.values():
        if isinstance(result, bool) and result:
            successful_tests += 1
        elif isinstance(result, dict) and result.get("status") == "success":
            successful_tests += 1
        elif isinstance(result, dict) and "status" not in result:
            # Handle scraper import results
            all_passed = all(r.get("status") == "success" for r in result.values())
            if all_passed:
                successful_tests += 1
    
    print(f"OVERALL SUMMARY: {successful_tests}/{total_tests} tests passed")
    print(f"{'=' * 60}")
    
    if successful_tests == total_tests:
        print("🎉 All Phase 4 Docker tests passed!")
        return 0
    else:
        print(f"⚠️  {total_tests - successful_tests} test(s) failed. Check the logs for details.")
        return 1


async def main():
    """Main function to run all tests."""
    logger = get_logger(__name__)
    
    try:
        logger.info("Starting Phase 4 Docker tests")
        
        # Run all tests
        results = await run_all_tests()
        
        # Print results
        exit_code = print_test_results(results)
        
        return exit_code
        
    except Exception as e:
        logger.error(f"Docker test execution failed: {e}")
        print(f"❌ Docker test execution failed: {e}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code) 