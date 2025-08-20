"""
Task scheduler for automated data collection.
"""

import asyncio
import schedule
import time
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
import signal
import sys

from config.settings import config
from utils.logger import get_logger
from .coordinator import DataCoordinator


class DataCollectionScheduler:
    """Manages scheduled data collection tasks."""

    def __init__(self):
        """Initialize the scheduler."""
        self.logger = get_logger(__name__)
        self.coordinator = DataCoordinator()
        self.running = False
        self.scheduler_thread = None

        # Register signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        self.logger.info(f"Received signal {signum}, shutting down scheduler")
        self.stop()
        sys.exit(0)

    def setup_schedule(self):
        """Set up the scheduling configuration."""
        try:
            # Clear any existing schedules
            schedule.clear()

            # Daily tasks - run at 06:00 UTC
            schedule.every().day.at("06:00").do(self._run_daily_scrapers)

            # Weekly tasks - run every Monday at 02:00 UTC
            schedule.every().monday.at("02:00").do(self._run_weekly_scrapers)

            # Bi-weekly tasks - run every other Wednesday at 03:00 UTC
            schedule.every(2).weeks.do(self._run_biweekly_scrapers)

            # Additional daily task for live data - run at 18:00 UTC (after matches)
            schedule.every().day.at("18:00").do(self._run_live_data_scrapers)

            self.logger.info(
                "Scheduler configured successfully",
                daily_time="06:00 UTC",
                weekly_time="Monday 02:00 UTC",
                biweekly_time="Every other Wednesday 03:00 UTC",
                live_data_time="18:00 UTC",
            )

        except Exception as e:
            self.logger.error(f"Failed to setup schedule: {e}")
            raise

    async def _run_daily_scrapers(self):
        """Run high-frequency scrapers that need daily updates."""
        try:
            self.logger.info("Starting daily scraper execution")

            # FPL API - daily updates for live data
            tasks = [self.coordinator.run_scraper("fpl_api")]

            # Run tasks concurrently
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Log results
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    self.logger.error(
                        "Daily scraper failed", scraper="fpl_api", error=str(result)
                    )
                else:
                    self.logger.info(
                        "Daily scraper completed", scraper="fpl_api", result=result
                    )

            self.logger.info("Daily scraper execution completed")

        except Exception as e:
            self.logger.error(f"Daily scraper execution failed: {e}")

    async def _run_weekly_scrapers(self):
        """Run comprehensive data collection weekly."""
        try:
            self.logger.info("Starting weekly scraper execution")

            # Weekly scrapers for comprehensive data
            tasks = [
                self.coordinator.run_scraper("fpl_api"),  # Full data refresh
                self.coordinator.run_scraper("understat"),  # Advanced stats (xG, xA)
                self.coordinator.run_scraper("fbref"),  # Comprehensive stats
            ]

            # Run tasks concurrently
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Log results
            scrapers = [
                "fpl_api",
                "understat",
                "fbref",
            ]  # Add more as they're implemented
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    self.logger.error(
                        "Weekly scraper failed", scraper=scrapers[i], error=str(result)
                    )
                else:
                    self.logger.info(
                        "Weekly scraper completed", scraper=scrapers[i], result=result
                    )

            self.logger.info("Weekly scraper execution completed")

        except Exception as e:
            self.logger.error(f"Weekly scraper execution failed: {e}")

    async def _run_biweekly_scrapers(self):
        """Run less frequent scrapers bi-weekly."""
        try:
            self.logger.info("Starting bi-weekly scraper execution")

            # Bi-weekly scrapers for market data and less frequent updates
            tasks = [
                self.coordinator.run_scraper(
                    "transfermarkt"
                ),  # Market data and transfers
                self.coordinator.run_scraper("whoscored"),  # Performance ratings
                self.coordinator.run_scraper(
                    "football_data"
                ),  # Historical data and fixtures
            ]

            if not tasks:
                self.logger.info("No bi-weekly scrapers configured yet")
                return

            # Run tasks concurrently
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Log results
            scrapers = ["transfermarkt", "whoscored", "football_data"]
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    self.logger.error(
                        "Bi-weekly scraper failed",
                        scraper=scrapers[i],
                        error=str(result),
                    )
                else:
                    self.logger.info(
                        "Bi-weekly scraper completed",
                        scraper=scrapers[i],
                        result=result,
                    )

            self.logger.info("Bi-weekly scraper execution completed")

        except Exception as e:
            self.logger.error(f"Bi-weekly scraper execution failed: {e}")

    async def _run_live_data_scrapers(self):
        """Run scrapers for live match data after games."""
        try:
            self.logger.info("Starting live data scraper execution")

            # Live data scrapers - run after matches
            tasks = [
                self.coordinator.run_scraper("fpl_api")  # Get live scores and stats
            ]

            # Run tasks concurrently
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Log results
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    self.logger.error(
                        "Live data scraper failed", scraper="fpl_api", error=str(result)
                    )
                else:
                    self.logger.info(
                        "Live data scraper completed", scraper="fpl_api", result=result
                    )

            self.logger.info("Live data scraper execution completed")

        except Exception as e:
            self.logger.error(f"Live data scraper execution failed: {e}")

    async def _run_scheduled_jobs(self):
        """Run all pending scheduled jobs."""
        try:
            # Get all pending jobs
            pending_jobs = schedule.get_jobs()

            if pending_jobs:
                self.logger.debug(
                    f"Found {len(pending_jobs)} pending jobs",
                    jobs=[job.job_func.__name__ for job in pending_jobs],
                )

            # Run pending jobs
            schedule.run_pending()

        except Exception as e:
            self.logger.error(f"Error running scheduled jobs: {e}")

    async def start(self):
        """Start the scheduler."""
        try:
            self.logger.info("Starting data collection scheduler")

            # Setup the schedule
            self.setup_schedule()

            # Mark as running
            self.running = True

            # Log initial schedule
            self.logger.info(
                "Scheduler started successfully",
                next_run=schedule.next_run(),
                jobs_count=len(schedule.get_jobs()),
            )

            # Main scheduler loop
            while self.running:
                try:
                    # Run pending jobs
                    await self._run_scheduled_jobs()

                    # Sleep for 1 minute before checking again
                    await asyncio.sleep(60)

                except Exception as e:
                    self.logger.error(f"Error in scheduler loop: {e}")
                    await asyncio.sleep(60)  # Continue running

        except Exception as e:
            self.logger.error(f"Failed to start scheduler: {e}")
            raise

    def stop(self):
        """Stop the scheduler."""
        self.logger.info("Stopping data collection scheduler")
        self.running = False

    def get_status(self) -> Dict[str, Any]:
        """Get scheduler status information.

        Returns:
            Dictionary with scheduler status
        """
        try:
            jobs = schedule.get_jobs()
            next_run = schedule.next_run()

            return {
                "running": self.running,
                "jobs_count": len(jobs),
                "next_run": next_run.isoformat() if next_run else None,
                "jobs": [
                    {
                        "function": job.job_func.__name__,
                        "next_run": job.next_run.isoformat() if job.next_run else None,
                        "interval": (
                            str(job.interval) if hasattr(job, "interval") else None
                        ),
                    }
                    for job in jobs
                ],
            }

        except Exception as e:
            self.logger.error(f"Error getting scheduler status: {e}")
            return {"running": self.running, "error": str(e)}


async def main():
    """Main function to run the scheduler."""
    scheduler = DataCollectionScheduler()

    try:
        await scheduler.start()
    except KeyboardInterrupt:
        scheduler.logger.info("Scheduler interrupted by user")
    except Exception as e:
        scheduler.logger.error(f"Scheduler failed: {e}")
        raise
    finally:
        scheduler.stop()


if __name__ == "__main__":
    asyncio.run(main())
