#!/usr/bin/env python3
"""
Test script to verify scheduler startup functionality.
"""
import asyncio
import sys
import os
import signal
from datetime import datetime

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from orchestration.scheduler import DataCollectionScheduler
from utils.logger import get_logger


async def test_scheduler_startup():
    """Test that the scheduler can start up correctly."""
    logger = get_logger(__name__)
    scheduler = None

    try:
        logger.info("Testing scheduler startup...")

        # Initialize scheduler
        scheduler = DataCollectionScheduler()

        # Setup schedule
        scheduler.setup_schedule()
        logger.info("Schedule setup completed")

        # Get initial status
        status = scheduler.get_status()
        logger.info(f"Initial scheduler status: {status}")

        # Test that we can start the scheduler
        logger.info("Starting scheduler...")

        # Create a task that will run for a short time
        async def run_scheduler_briefly():
            try:
                await scheduler.start()
            except asyncio.CancelledError:
                logger.info("Scheduler task cancelled as expected")
                raise

        # Run the scheduler for 5 seconds
        task = asyncio.create_task(run_scheduler_briefly())

        # Wait for 5 seconds
        await asyncio.sleep(5)

        # Cancel the task
        task.cancel()

        try:
            await task
        except asyncio.CancelledError:
            pass

        logger.info("Scheduler startup test completed successfully!")

    except Exception as e:
        logger.error(f"Scheduler startup test failed: {e}")
        raise
    finally:
        if scheduler:
            scheduler.stop()


async def main():
    """Main test function."""
    logger = get_logger(__name__)

    try:
        await test_scheduler_startup()
        print("Scheduler startup test PASSED")

    except Exception as e:
        logger.error(f"Scheduler startup test failed: {e}")
        print("Scheduler startup test FAILED")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
