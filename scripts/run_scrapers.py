#!/usr/bin/env python3
"""
Manual scraper execution script for testing the complete data pipeline.
"""
import asyncio
import sys
import os
from datetime import datetime
from typing import Dict, Any

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import config
from storage.database import db_manager
from storage.repositories import (
    PlayerRepository,
    PlayerStatsRepository,
    DataQualityRepository,
    ScraperRunRepository,
)
from scrapers.fpl_api.fpl_scraper import FPLScraper
from processors.data_processor import DataProcessor
from utils.logger import get_logger, ScraperLogger


class ScraperRunner:
    """Main scraper runner for manual execution."""

    def __init__(self):
        """Initialize the scraper runner."""
        self.logger = get_logger(__name__)
        self.player_repo = PlayerRepository()
        self.stats_repo = PlayerStatsRepository()
        self.quality_repo = DataQualityRepository()
        self.run_repo = ScraperRunRepository()
        self.processor = DataProcessor()

        # Initialize database
        self._init_database()

    def _init_database(self):
        """Initialize database connection and create tables."""
        try:
            db_manager.initialize()
            db_manager.create_tables()
            self.logger.info("Database initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize database: {e}")
            raise

    async def run_fpl_scraper(self) -> Dict[str, Any]:
        """Run the FPL scraper and process the data.

        Returns:
            Dictionary with execution results
        """
        start_time = datetime.utcnow()
        scraper_name = "fpl_api"

        try:
            self.logger.info(f"Starting {scraper_name} scraper execution")

            # Log scraper run start
            with db_manager.get_sync_session() as session:
                run_log = self.run_repo.log_scraper_run(
                    session=session,
                    scraper_name=scraper_name,
                    status="running",
                    start_time=start_time,
                )
                session.commit()

            # Run the scraper
            scraper = FPLScraper()
            raw_data = await scraper.run()

            # Process the data
            processed_data = await self.processor.process_scraped_data(
                raw_data, scraper_name
            )

            # Save to database
            saved_count = await self._save_fpl_data(processed_data)

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
                    records_processed=len(raw_data.get("players", [])),
                    records_saved=saved_count,
                )
                session.commit()

            result = {
                "scraper": scraper_name,
                "status": "success",
                "duration_seconds": duration,
                "records_processed": len(raw_data.get("players", [])),
                "records_saved": saved_count,
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
            }

            self.logger.info(
                f"{scraper_name} scraper completed successfully",
                duration_seconds=duration,
                records_processed=result["records_processed"],
                records_saved=result["records_saved"],
            )

            return result

        except Exception as e:
            # Log failure
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
                    error_message=str(e),
                )
                session.commit()

            self.logger.error(
                f"{scraper_name} scraper failed",
                duration_seconds=duration,
                error=str(e),
            )

            raise

    async def _save_fpl_data(self, data: Dict[str, Any]) -> int:
        """Save FPL data to the database.

        Args:
            data: Processed FPL data

        Returns:
            Number of records saved
        """
        saved_count = 0

        try:
            with db_manager.get_sync_session() as session:
                # Save players
                if "players" in data:
                    for player_data in data["players"]:
                        try:
                            self.player_repo.create_or_update_player(
                                session, player_data
                            )
                            saved_count += 1
                        except Exception as e:
                            self.logger.warning(
                                "Failed to save player",
                                player_id=player_data.get("id"),
                                error=str(e),
                            )

                # Log data quality
                if "players" in data:
                    quality_score = 1.0  # Placeholder - could be calculated based on validation results
                    self.quality_repo.log_quality_check(
                        session=session,
                        source="fpl_api",
                        data_type="players",
                        quality_score=quality_score,
                        issues=[],
                        record_count=len(data["players"]),
                        valid_count=len(data["players"]),
                        invalid_count=0,
                    )

                session.commit()

                self.logger.info("FPL data saved successfully", saved_count=saved_count)

        except Exception as e:
            self.logger.error("Failed to save FPL data", error=str(e))
            raise

        return saved_count

    async def run_all_scrapers(self) -> Dict[str, Any]:
        """Run all available scrapers.

        Returns:
            Dictionary with results for all scrapers
        """
        results = {}

        try:
            # Run FPL scraper
            results["fpl_api"] = await self.run_fpl_scraper()

            # TODO: Add other scrapers as they are implemented
            # results['understat'] = await self.run_understat_scraper()
            # results['fbref'] = await self.run_fbref_scraper()

            self.logger.info("All scrapers completed", results=results)

        except Exception as e:
            self.logger.error(f"Failed to run all scrapers: {e}")
            raise

        return results

    def cleanup(self):
        """Clean up resources."""
        try:
            db_manager.close()
            self.logger.info("Resources cleaned up successfully")
        except Exception as e:
            self.logger.error(f"Failed to cleanup resources: {e}")


async def main():
    """Main execution function."""
    runner = None

    try:
        # Initialize runner
        runner = ScraperRunner()

        # Check command line arguments
        if len(sys.argv) > 1:
            scraper_name = sys.argv[1].lower()

            if scraper_name == "fpl":
                result = await runner.run_fpl_scraper()
                print(f"FPL scraper result: {result}")
            elif scraper_name == "all":
                results = await runner.run_all_scrapers()
                print(f"All scrapers results: {results}")
            else:
                print(f"Unknown scraper: {scraper_name}")
                print("Available scrapers: fpl, all")
                sys.exit(1)
        else:
            # Default: run FPL scraper
            result = await runner.run_fpl_scraper()
            print(f"FPL scraper result: {result}")

    except KeyboardInterrupt:
        print("\nScraper execution interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Scraper execution failed: {e}")
        sys.exit(1)
    finally:
        if runner:
            runner.cleanup()


if __name__ == "__main__":
    # Run the main function
    asyncio.run(main())
