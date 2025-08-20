#!/usr/bin/env python3
"""
Test script for Phase 4 scrapers.

This script tests the new scrapers implemented in Phase 4:
- Transfermarkt scraper
- WhoScored scraper
- Football-Data scraper
"""

import asyncio
import sys
import os
from datetime import datetime
from typing import Dict, Any

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import config
from utils.logger import get_logger
from orchestration.coordinator import DataCoordinator


async def test_transfermarkt_scraper():
    """Test the Transfermarkt scraper."""
    logger = get_logger(__name__)
    logger.info("Testing Transfermarkt scraper")

    try:
        coordinator = DataCoordinator()

        # Test the scraper
        result = await coordinator.run_scraper("transfermarkt")

        logger.info("Transfermarkt scraper test completed", result=result)
        return result

    except Exception as e:
        logger.error("Transfermarkt scraper test failed", error=str(e))
        raise
    finally:
        coordinator.cleanup()


async def test_whoscored_scraper():
    """Test the WhoScored scraper."""
    logger = get_logger(__name__)
    logger.info("Testing WhoScored scraper")

    try:
        coordinator = DataCoordinator()

        # Test the scraper
        result = await coordinator.run_scraper("whoscored")

        logger.info("WhoScored scraper test completed", result=result)
        return result

    except Exception as e:
        logger.error("WhoScored scraper test failed", error=str(e))
        raise
    finally:
        coordinator.cleanup()


async def test_football_data_scraper():
    """Test the Football-Data scraper."""
    logger = get_logger(__name__)
    logger.info("Testing Football-Data scraper")

    try:
        coordinator = DataCoordinator()

        # Test the scraper
        result = await coordinator.run_scraper("football_data")

        logger.info("Football-Data scraper test completed", result=result)
        return result

    except Exception as e:
        logger.error("Football-Data scraper test failed", error=str(e))
        raise
    finally:
        coordinator.cleanup()


async def test_all_phase4_scrapers():
    """Test all Phase 4 scrapers."""
    logger = get_logger(__name__)
    logger.info("Starting Phase 4 scraper tests")

    results = {}

    # Test each scraper
    scrapers = [
        ("transfermarkt", test_transfermarkt_scraper),
        ("whoscored", test_whoscored_scraper),
        ("football_data", test_football_data_scraper),
    ]

    for scraper_name, test_func in scrapers:
        try:
            logger.info(f"Testing {scraper_name} scraper")
            result = await test_func()
            results[scraper_name] = {"status": "success", "result": result}
            logger.info(f"{scraper_name} scraper test passed")

        except Exception as e:
            logger.error(f"{scraper_name} scraper test failed", error=str(e))
            results[scraper_name] = {"status": "failed", "error": str(e)}

    # Print summary
    logger.info("Phase 4 scraper tests completed")
    logger.info("Test results:", results=results)

    # Count successes and failures
    successes = len([r for r in results.values() if r["status"] == "success"])
    failures = len([r for r in results.values() if r["status"] == "failed"])

    logger.info(
        "Test summary",
        total_scrapers=len(scrapers),
        successful=successes,
        failed=failures,
    )

    return results


async def main():
    """Main function to run the tests."""
    logger = get_logger(__name__)

    try:
        logger.info("Starting Phase 4 scraper tests")

        # Test all scrapers
        results = await test_all_phase4_scrapers()

        # Print detailed results
        print("\n" + "=" * 50)
        print("PHASE 4 SCRAPER TEST RESULTS")
        print("=" * 50)

        for scraper_name, result in results.items():
            print(f"\n{scraper_name.upper()} SCRAPER:")
            print("-" * 30)

            if result["status"] == "success":
                print("✅ PASSED")
                if "result" in result:
                    print(
                        f"   Duration: {result['result'].get('duration_seconds', 'N/A')}s"
                    )
                    print(
                        f"   Records processed: {result['result'].get('records_processed', 'N/A')}"
                    )
                    print(
                        f"   Records saved: {result['result'].get('records_saved', 'N/A')}"
                    )
            else:
                print("❌ FAILED")
                print(f"   Error: {result.get('error', 'Unknown error')}")

        # Overall summary
        successes = len([r for r in results.values() if r["status"] == "success"])
        failures = len([r for r in results.values() if r["status"] == "failed"])

        print(f"\n{'='*50}")
        print(f"OVERALL SUMMARY: {successes}/{len(results)} scrapers passed")
        print(f"{'='*50}")

        if failures == 0:
            print("🎉 All Phase 4 scrapers are working correctly!")
            return 0
        else:
            print(f"⚠️  {failures} scraper(s) failed. Check the logs for details.")
            return 1

    except Exception as e:
        logger.error("Test execution failed", error=str(e))
        print(f"❌ Test execution failed: {e}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
