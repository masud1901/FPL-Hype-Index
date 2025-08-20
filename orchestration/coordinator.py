"""
Data collection coordinator for orchestrating scraper execution.
"""

import asyncio
from datetime import datetime
from typing import Dict, Any, Optional, List
import importlib

from config.settings import config
from storage.database import db_manager
from storage.repositories import (
    PlayerRepository,
    PlayerStatsRepository,
    TeamRepository,
    FixtureRepository,
    DataQualityRepository,
    ScraperRunRepository,
)
from processors.data_processor import DataProcessor
from utils.logger import get_logger
from scrapers.base.exceptions import (
    ScraperException,
    ScraperConnectionError,
    ScraperTimeoutError,
    ScraperRateLimitError,
    ScraperDataValidationError,
)


class DataCoordinator:
    """Coordinates the execution of data collection scrapers."""

    def __init__(self):
        """Initialize the coordinator."""
        self.logger = get_logger(__name__)
        self.processor = DataProcessor()

        # Initialize repositories
        self.player_repo = PlayerRepository()
        self.stats_repo = PlayerStatsRepository()
        self.team_repo = TeamRepository()
        self.fixture_repo = FixtureRepository()
        self.quality_repo = DataQualityRepository()
        self.run_repo = ScraperRunRepository()

        # Scraper registry - maps scraper names to their module paths
        self.scraper_registry = {
            "fpl_api": "scrapers.fpl_api.fpl_scraper.FPLScraper",
            "understat": "scrapers.understat.understat_scraper.UnderstatScraper",
            "fbref": "scrapers.fbref.fbref_scraper.FBRefScraper",
            "transfermarkt": "scrapers.transfermarkt.transfermarkt_scraper.TransfermarktScraper",
            "whoscored": "scrapers.whoscored.whoscored_scraper.WhoScoredScraper",
            "football_data": "scrapers.football_data.football_data_scraper.FootballDataScraper",
        }

        # Initialize database connection
        self._init_database()

    def _init_database(self):
        """Initialize database connection and create tables."""
        try:
            db_manager.initialize()
            db_manager.create_tables()
            self.logger.debug("Database initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize database: {e}")
            raise

    def get_available_scrapers(self) -> List[str]:
        """Get list of available scrapers.

        Returns:
            List of scraper names
        """
        return list(self.scraper_registry.keys())

    def _get_scraper_class(self, scraper_name: str):
        """Get scraper class by name.

        Args:
            scraper_name: Name of the scraper

        Returns:
            Scraper class

        Raises:
            ValueError: If scraper not found
        """
        if scraper_name not in self.scraper_registry:
            available = self.get_available_scrapers()
            raise ValueError(
                f"Scraper '{scraper_name}' not found. Available scrapers: {available}"
            )

        try:
            module_path, class_name = self.scraper_registry[scraper_name].rsplit(".", 1)
            module = importlib.import_module(module_path)
            scraper_class = getattr(module, class_name)

            return scraper_class

        except (ImportError, AttributeError) as e:
            self.logger.error(
                f"Failed to import scraper class for '{scraper_name}': {e}"
            )
            raise ValueError(f"Scraper '{scraper_name}' could not be loaded: {e}")

    async def run_scraper(
        self, scraper_name: str, config_overrides: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Run a specific scraper by name.

        Args:
            scraper_name: Name of the scraper to run
            config_overrides: Optional configuration overrides

        Returns:
            Dictionary with execution results

        Raises:
            ValueError: If scraper not found
            ScraperException: If scraping fails
        """
        start_time = datetime.utcnow()

        try:
            self.logger.info(f"Starting scraper execution", scraper=scraper_name)

            # Log scraper run start
            with db_manager.get_sync_session() as session:
                run_log = self.run_repo.log_scraper_run(
                    session=session,
                    scraper_name=scraper_name,
                    status="running",
                    start_time=start_time,
                )
                session.commit()

            # Get scraper class and instantiate
            scraper_class = self._get_scraper_class(scraper_name)
            scraper = scraper_class(config.scraper.__dict__)

            # Apply config overrides if provided
            if config_overrides:
                for key, value in config_overrides.items():
                    if hasattr(scraper, key):
                        setattr(scraper, key, value)

            # Run the scraper
            raw_data = await scraper.run()

            # Process the data
            processed_data = await self.processor.process_scraped_data(
                raw_data, scraper_name
            )

            # Save to database
            saved_count = await self._save_scraper_data(processed_data, scraper_name)

            # Log successful completion
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()

            with db_manager.get_sync_session() as session:
                self.run_repo.log_scraper_run(
                    session=session,
                    scraper_name=scraper_name,
                    status="success",
                    start_time=start_time,
                    end_time=end_time,
                    duration_seconds=duration,
                    records_processed=self._count_records(raw_data),
                    records_saved=saved_count,
                )
                session.commit()

            result = {
                "scraper": scraper_name,
                "status": "success",
                "duration_seconds": duration,
                "records_processed": self._count_records(raw_data),
                "records_saved": saved_count,
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
            }

            self.logger.info(
                f"Scraper execution completed successfully",
                scraper=scraper_name,
                duration_seconds=duration,
                records_processed=result["records_processed"],
                records_saved=result["records_saved"],
            )

            return result

        except ScraperException as e:
            # Log scraper-specific errors
            await self._handle_scraper_error(scraper_name, e, start_time)
            raise

        except Exception as e:
            # Log general errors
            await self._handle_general_error(scraper_name, e, start_time)
            raise

    async def run_multiple_scrapers(
        self,
        scraper_names: List[str],
        config_overrides: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Run multiple scrapers concurrently.

        Args:
            scraper_names: List of scraper names to run
            config_overrides: Optional configuration overrides for all scrapers

        Returns:
            Dictionary with results for all scrapers
        """
        try:
            self.logger.info(
                f"Starting multiple scraper execution", scrapers=scraper_names
            )

            # Create tasks for all scrapers
            tasks = [self.run_scraper(name, config_overrides) for name in scraper_names]

            # Run all scrapers concurrently
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Process results
            final_results = {}
            for i, result in enumerate(results):
                scraper_name = scraper_names[i]

                if isinstance(result, Exception):
                    final_results[scraper_name] = {
                        "status": "failed",
                        "error": str(result),
                    }
                    self.logger.error(
                        f"Scraper failed", scraper=scraper_name, error=str(result)
                    )
                else:
                    final_results[scraper_name] = result
                    self.logger.info(
                        f"Scraper completed",
                        scraper=scraper_name,
                        status=result["status"],
                    )

            self.logger.info(
                f"Multiple scraper execution completed",
                total_scrapers=len(scraper_names),
                successful=len(
                    [r for r in final_results.values() if r.get("status") == "success"]
                ),
                failed=len(
                    [r for r in final_results.values() if r.get("status") == "failed"]
                ),
            )

            return final_results

        except Exception as e:
            self.logger.error(f"Failed to run multiple scrapers: {e}")
            raise

    async def _save_scraper_data(self, data: Dict[str, Any], scraper_name: str) -> int:
        """Save scraper data to the database.

        Args:
            data: Processed data to save
            scraper_name: Name of the scraper that produced the data

        Returns:
            Number of records saved
        """
        saved_count = 0

        try:
            with db_manager.get_sync_session() as session:
                # Handle different data types based on scraper
                if scraper_name == "fpl_api":
                    saved_count = await self._save_fpl_data(session, data)
                # elif scraper_name == 'understat':
                #     saved_count = await self._save_understat_data(session, data)
                # Add more scraper-specific save methods as needed

                # Log data quality
                if data:
                    quality_score = 1.0  # Placeholder - could be calculated based on validation results
                    self.quality_repo.log_quality_check(
                        session=session,
                        source=scraper_name,
                        data_type="players",  # Could be determined from data structure
                        quality_score=quality_score,
                        issues=[],
                        record_count=self._count_records(data),
                        valid_count=self._count_records(data),
                        invalid_count=0,
                    )

                session.commit()

                self.logger.debug(
                    f"Data saved successfully",
                    scraper=scraper_name,
                    saved_count=saved_count,
                )

        except Exception as e:
            self.logger.error(
                f"Failed to save data", scraper=scraper_name, error=str(e)
            )
            raise

        return saved_count

    async def _save_fpl_data(self, session, data: Dict[str, Any]) -> int:
        """Save FPL data to the database.

        Args:
            session: Database session
            data: FPL data to save

        Returns:
            Number of records saved
        """
        saved_count = 0

        try:
            # Save players
            if "players" in data:
                for player_data in data["players"]:
                    try:
                        self.player_repo.create_or_update_player(session, player_data)
                        saved_count += 1
                    except Exception as e:
                        self.logger.warning(
                            "Failed to save player",
                            player_id=player_data.get("id"),
                            error=str(e),
                        )

            # Save teams
            if "teams" in data:
                for team_data in data["teams"]:
                    try:
                        self.team_repo.create_or_update_team(session, team_data)
                        saved_count += 1
                    except Exception as e:
                        self.logger.warning(
                            "Failed to save team",
                            team_id=team_data.get("id"),
                            error=str(e),
                        )

            # Save fixtures
            if "fixtures" in data:
                for fixture_data in data["fixtures"]:
                    try:
                        self.fixture_repo.create_or_update_fixture(
                            session, fixture_data
                        )
                        saved_count += 1
                    except Exception as e:
                        self.logger.warning(
                            "Failed to save fixture",
                            fixture_id=fixture_data.get("id"),
                            error=str(e),
                        )

            # Save gameweeks
            if "gameweeks" in data:
                for gameweek_data in data["gameweeks"]:
                    try:
                        # TODO: Implement gameweek repository and save gameweeks
                        pass
                    except Exception as e:
                        self.logger.warning(
                            "Failed to save gameweek",
                            gameweek_id=gameweek_data.get("id"),
                            error=str(e),
                        )

        except Exception as e:
            self.logger.error(f"Failed to save FPL data: {e}")
            raise

        return saved_count

    async def _handle_scraper_error(
        self, scraper_name: str, error: ScraperException, start_time: datetime
    ):
        """Handle scraper-specific errors.

        Args:
            scraper_name: Name of the scraper
            error: The scraper exception
            start_time: When the scraper started
        """
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()

        with db_manager.get_sync_session() as session:
            self.run_repo.log_scraper_run(
                session=session,
                scraper_name=scraper_name,
                status="failed",
                start_time=start_time,
                end_time=end_time,
                duration_seconds=duration,
                error_message=str(error),
            )
            session.commit()

        self.logger.error(
            f"Scraper execution failed",
            scraper=scraper_name,
            duration_seconds=duration,
            error=str(error),
            error_type=type(error).__name__,
        )

    async def _handle_general_error(
        self, scraper_name: str, error: Exception, start_time: datetime
    ):
        """Handle general errors during scraper execution.

        Args:
            scraper_name: Name of the scraper
            error: The general exception
            start_time: When the scraper started
        """
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()

        with db_manager.get_sync_session() as session:
            self.run_repo.log_scraper_run(
                session=session,
                scraper_name=scraper_name,
                status="failed",
                start_time=start_time,
                end_time=end_time,
                duration_seconds=duration,
                error_message=str(error),
            )
            session.commit()

        self.logger.error(
            f"General error during scraper execution",
            scraper=scraper_name,
            duration_seconds=duration,
            error=str(error),
            error_type=type(error).__name__,
        )

    def _count_records(self, data: Dict[str, Any]) -> int:
        """Count the number of records in the data.

        Args:
            data: Data to count records in

        Returns:
            Number of records
        """
        if not data:
            return 0

        count = 0

        # Count players
        if "players" in data and isinstance(data["players"], list):
            count += len(data["players"])

        # Count teams
        if "teams" in data and isinstance(data["teams"], list):
            count += len(data["teams"])

        # Count gameweeks
        if "gameweeks" in data and isinstance(data["gameweeks"], list):
            count += len(data["gameweeks"])

        # If no specific structure, count the top-level items
        if count == 0 and isinstance(data, dict):
            count = len(data)
        elif count == 0 and isinstance(data, list):
            count = len(data)

        return count

    def get_scraper_status(self, scraper_name: str) -> Dict[str, Any]:
        """Get the status of a specific scraper.

        Args:
            scraper_name: Name of the scraper

        Returns:
            Dictionary with scraper status
        """
        try:
            with db_manager.get_sync_session() as session:
                last_run = self.run_repo.get_last_run(session, scraper_name)

                if last_run:
                    return {
                        "scraper": scraper_name,
                        "last_run": (
                            last_run.start_time.isoformat()
                            if last_run.start_time
                            else None
                        ),
                        "last_status": last_run.status,
                        "last_duration": last_run.duration_seconds,
                        "last_records_processed": last_run.records_processed,
                        "last_records_saved": last_run.records_saved,
                        "last_error": last_run.error_message,
                    }
                else:
                    return {
                        "scraper": scraper_name,
                        "last_run": None,
                        "last_status": None,
                        "last_duration": None,
                        "last_records_processed": None,
                        "last_records_saved": None,
                        "last_error": None,
                    }

        except Exception as e:
            self.logger.error(f"Error getting scraper status: {e}")
            return {"scraper": scraper_name, "error": str(e)}

    def cleanup(self):
        """Clean up resources."""
        try:
            db_manager.close()
            self.logger.debug("Coordinator resources cleaned up successfully")
        except Exception as e:
            self.logger.error(f"Failed to cleanup coordinator resources: {e}")


async def main():
    """Main function for testing the coordinator."""
    coordinator = DataCoordinator()

    try:
        # Test running the FPL scraper
        result = await coordinator.run_scraper("fpl_api")
        print(f"FPL scraper result: {result}")

    except Exception as e:
        print(f"Coordinator test failed: {e}")
        raise
    finally:
        coordinator.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
