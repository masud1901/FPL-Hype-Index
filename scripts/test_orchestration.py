#!/usr/bin/env python3
"""
Test script for orchestration components.
"""
import asyncio
import sys
import os
from datetime import datetime

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from orchestration.coordinator import DataCoordinator
from orchestration.scheduler import DataCollectionScheduler
from utils.logger import get_logger


async def test_coordinator():
    """Test the DataCoordinator functionality."""
    logger = get_logger(__name__)
    coordinator = None
    
    try:
        logger.info("Testing DataCoordinator...")
        
        # Initialize coordinator
        coordinator = DataCoordinator()
        
        # Test getting available scrapers
        available_scrapers = coordinator.get_available_scrapers()
        logger.info(f"Available scrapers: {available_scrapers}")
        
        # Test running FPL scraper
        logger.info("Running FPL scraper test...")
        result = await coordinator.run_scraper('fpl_api')
        
        logger.info(f"FPL scraper result: {result}")
        
        # Test getting scraper status
        status = coordinator.get_scraper_status('fpl_api')
        logger.info(f"FPL scraper status: {status}")
        
        logger.info("DataCoordinator test completed successfully!")
        
    except Exception as e:
        logger.error(f"DataCoordinator test failed: {e}")
        raise
    finally:
        if coordinator:
            coordinator.cleanup()


async def test_scheduler():
    """Test the DataCollectionScheduler functionality."""
    logger = get_logger(__name__)
    scheduler = None
    
    try:
        logger.info("Testing DataCollectionScheduler...")
        
        # Initialize scheduler
        scheduler = DataCollectionScheduler()
        
        # Test setup schedule
        scheduler.setup_schedule()
        logger.info("Schedule setup completed")
        
        # Test getting status
        status = scheduler.get_status()
        logger.info(f"Scheduler status: {status}")
        
        # Test running a single job manually
        logger.info("Testing manual job execution...")
        await scheduler._run_daily_scrapers()
        
        logger.info("DataCollectionScheduler test completed successfully!")
        
    except Exception as e:
        logger.error(f"DataCollectionScheduler test failed: {e}")
        raise
    finally:
        if scheduler:
            scheduler.stop()


async def test_full_orchestration():
    """Test the full orchestration flow."""
    logger = get_logger(__name__)
    
    try:
        logger.info("Testing full orchestration flow...")
        
        # Test coordinator
        await test_coordinator()
        
        # Test scheduler
        await test_scheduler()
        
        logger.info("Full orchestration test completed successfully!")
        
    except Exception as e:
        logger.error(f"Full orchestration test failed: {e}")
        raise


async def main():
    """Main test function."""
    logger = get_logger(__name__)
    
    try:
        # Check command line arguments
        if len(sys.argv) > 1:
            test_type = sys.argv[1].lower()
            
            if test_type == "coordinator":
                await test_coordinator()
            elif test_type == "scheduler":
                await test_scheduler()
            elif test_type == "full":
                await test_full_orchestration()
            else:
                print(f"Unknown test type: {test_type}")
                print("Available tests: coordinator, scheduler, full")
                sys.exit(1)
        else:
            # Default: run full test
            await test_full_orchestration()
            
    except KeyboardInterrupt:
        logger.info("Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Test failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main()) 