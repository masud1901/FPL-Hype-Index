"""
System health checker for monitoring scraper performance and operational status.
"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import json
import logging
from pathlib import Path

from utils.logger import get_logger
from storage.database import db_manager
from storage.models import DataQualityLog
from sqlalchemy import func, desc


@dataclass
class ScraperHealth:
    """Health status for a single scraper"""

    name: str
    last_run: Optional[datetime]
    last_success: Optional[datetime]
    success_rate: float
    total_runs: int
    successful_runs: int
    failed_runs: int
    average_duration: float
    status: str  # 'healthy', 'warning', 'critical'
    error_message: Optional[str] = None


@dataclass
class SystemHealth:
    """Overall system health status"""

    timestamp: datetime
    overall_status: str  # 'healthy', 'warning', 'critical'
    scraper_health: Dict[str, ScraperHealth]
    database_status: str
    total_scrapers: int
    healthy_scrapers: int
    warning_scrapers: int
    critical_scrapers: int
    uptime_hours: float
    last_data_collection: Optional[datetime]


class HealthChecker:
    """Monitor and report system health status"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.logger = get_logger("health_checker")

        # Health thresholds
        self.success_rate_threshold = self.config.get("success_rate_threshold", 0.8)
        self.max_hours_since_last_run = self.config.get("max_hours_since_last_run", 24)
        self.max_hours_since_last_success = self.config.get(
            "max_hours_since_last_success", 48
        )

        # Health check history
        self.health_history: List[SystemHealth] = []
        self.max_history_size = self.config.get("max_health_history", 100)

        # Start time for uptime calculation
        self.start_time = datetime.now()

    async def check_system_health(self) -> SystemHealth:
        """Perform comprehensive system health check"""
        self.logger.info("Starting system health check")

        try:
            # Check scraper health
            scraper_health = await self._check_scraper_health()

            # Check database health
            database_status = await self._check_database_health()

            # Calculate overall status
            overall_status = self._calculate_overall_status(
                scraper_health, database_status
            )

            # Count scraper statuses
            healthy_count = sum(
                1 for h in scraper_health.values() if h.status == "healthy"
            )
            warning_count = sum(
                1 for h in scraper_health.values() if h.status == "warning"
            )
            critical_count = sum(
                1 for h in scraper_health.values() if h.status == "critical"
            )

            # Calculate uptime
            uptime_hours = (datetime.now() - self.start_time).total_seconds() / 3600

            # Get last data collection time
            last_data_collection = await self._get_last_data_collection()

            health = SystemHealth(
                timestamp=datetime.now(),
                overall_status=overall_status,
                scraper_health=scraper_health,
                database_status=database_status,
                total_scrapers=len(scraper_health),
                healthy_scrapers=healthy_count,
                warning_scrapers=warning_count,
                critical_scrapers=critical_count,
                uptime_hours=uptime_hours,
                last_data_collection=last_data_collection,
            )

            # Store in history
            self.health_history.append(health)
            if len(self.health_history) > self.max_history_size:
                self.health_history.pop(0)

            self.logger.info(
                "System health check completed",
                overall_status=overall_status,
                healthy_scrapers=healthy_count,
                warning_scrapers=warning_count,
                critical_scrapers=critical_count,
            )

            return health

        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            # Return critical health status
            return SystemHealth(
                timestamp=datetime.now(),
                overall_status="critical",
                scraper_health={},
                database_status="unknown",
                total_scrapers=0,
                healthy_scrapers=0,
                warning_scrapers=0,
                critical_scrapers=0,
                uptime_hours=0.0,
                last_data_collection=None,
            )

    async def _check_scraper_health(self) -> Dict[str, ScraperHealth]:
        """Check health status for all scrapers"""
        scraper_health = {}

        # Get scraper performance data from database
        async for session in db_manager.get_async_session():
            # Get recent data quality logs for each scraper
            recent_logs = await session.execute(
                func.select(DataQualityLog)
                .where(DataQualityLog.timestamp >= datetime.now() - timedelta(days=7))
                .order_by(desc(DataQualityLog.timestamp))
            )
            logs = recent_logs.scalars().all()

            # Group logs by scraper
            scraper_logs = {}
            for log in logs:
                if log.scraper_name not in scraper_logs:
                    scraper_logs[log.scraper_name] = []
                scraper_logs[log.scraper_name].append(log)

            # Calculate health for each scraper
            for scraper_name, logs_list in scraper_logs.items():
                health = self._calculate_scraper_health(scraper_name, logs_list)
                scraper_health[scraper_name] = health

        return scraper_health

    def _calculate_scraper_health(
        self, scraper_name: str, logs: List[DataQualityLog]
    ) -> ScraperHealth:
        """Calculate health status for a single scraper"""
        if not logs:
            return ScraperHealth(
                name=scraper_name,
                last_run=None,
                last_success=None,
                success_rate=0.0,
                total_runs=0,
                successful_runs=0,
                failed_runs=0,
                average_duration=0.0,
                status="critical",
                error_message="No recent activity",
            )

        # Sort logs by timestamp (most recent first)
        logs.sort(key=lambda x: x.timestamp, reverse=True)

        # Calculate metrics
        last_run = logs[0].timestamp
        successful_runs = sum(1 for log in logs if log.status == "success")
        failed_runs = sum(1 for log in logs if log.status == "error")
        total_runs = len(logs)
        success_rate = successful_runs / total_runs if total_runs > 0 else 0.0

        # Find last successful run
        last_success = None
        for log in logs:
            if log.status == "success":
                last_success = log.timestamp
                break

        # Calculate average duration
        durations = [log.duration for log in logs if log.duration is not None]
        average_duration = sum(durations) / len(durations) if durations else 0.0

        # Determine status
        status = "healthy"
        error_message = None

        if success_rate < self.success_rate_threshold:
            status = "critical"
            error_message = f"Low success rate: {success_rate:.1%}"
        elif last_run < datetime.now() - timedelta(hours=self.max_hours_since_last_run):
            status = "warning"
            error_message = f"No recent runs (last: {last_run})"
        elif last_success and last_success < datetime.now() - timedelta(
            hours=self.max_hours_since_last_success
        ):
            status = "critical"
            error_message = f"No recent successful runs (last: {last_success})"

        return ScraperHealth(
            name=scraper_name,
            last_run=last_run,
            last_success=last_success,
            success_rate=success_rate,
            total_runs=total_runs,
            successful_runs=successful_runs,
            failed_runs=failed_runs,
            average_duration=average_duration,
            status=status,
            error_message=error_message,
        )

    async def _check_database_health(self) -> str:
        """Check database connectivity and health"""
        try:
            async for session in db_manager.get_async_session():
                # Simple query to test connectivity
                await session.execute("SELECT 1")
                return "healthy"
        except Exception as e:
            self.logger.error(f"Database health check failed: {e}")
            return "critical"

    async def _get_last_data_collection(self) -> Optional[datetime]:
        """Get timestamp of last successful data collection"""
        try:
            async for session in db_manager.get_async_session():
                result = await session.execute(
                    func.select(func.max(DataQualityLog.timestamp)).where(
                        DataQualityLog.status == "success"
                    )
                )
                return result.scalar()
        except Exception as e:
            self.logger.error(f"Failed to get last data collection time: {e}")
            return None

    def _calculate_overall_status(
        self, scraper_health: Dict[str, ScraperHealth], database_status: str
    ) -> str:
        """Calculate overall system status"""
        if database_status == "critical":
            return "critical"

        if not scraper_health:
            return "warning"

        critical_count = sum(
            1 for h in scraper_health.values() if h.status == "critical"
        )
        warning_count = sum(1 for h in scraper_health.values() if h.status == "warning")

        if critical_count > 0:
            return "critical"
        elif warning_count > 0:
            return "warning"
        else:
            return "healthy"

    def get_health_summary(self) -> Dict[str, Any]:
        """Get a summary of current health status"""
        if not self.health_history:
            return {"status": "unknown", "message": "No health data available"}

        latest_health = self.health_history[-1]

        return {
            "status": latest_health.overall_status,
            "timestamp": latest_health.timestamp.isoformat(),
            "scrapers": {
                "total": latest_health.total_scrapers,
                "healthy": latest_health.healthy_scrapers,
                "warning": latest_health.warning_scrapers,
                "critical": latest_health.critical_scrapers,
            },
            "database": latest_health.database_status,
            "uptime_hours": round(latest_health.uptime_hours, 2),
            "last_data_collection": (
                latest_health.last_data_collection.isoformat()
                if latest_health.last_data_collection
                else None
            ),
        }

    def get_health_history(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get health history for the specified time period"""
        cutoff_time = datetime.now() - timedelta(hours=hours)

        history = []
        for health in self.health_history:
            if health.timestamp >= cutoff_time:
                history.append(asdict(health))

        return history

    async def export_health_report(self, filepath: str) -> None:
        """Export health report to JSON file"""
        health = await self.check_system_health()

        report = {
            "timestamp": health.timestamp.isoformat(),
            "overall_status": health.overall_status,
            "summary": self.get_health_summary(),
            "scraper_details": {
                name: asdict(scraper_health)
                for name, scraper_health in health.scraper_health.items()
            },
            "history": self.get_health_history(24),
        }

        # Ensure directory exists
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)

        with open(filepath, "w") as f:
            json.dump(report, f, indent=2, default=str)

        self.logger.info(f"Health report exported to {filepath}")

    async def start_health_monitoring(self, interval_minutes: int = 15) -> None:
        """Start continuous health monitoring"""
        self.logger.info(
            f"Starting health monitoring with {interval_minutes} minute intervals"
        )

        while True:
            try:
                await self.check_system_health()
                await asyncio.sleep(interval_minutes * 60)
            except Exception as e:
                self.logger.error(f"Health monitoring error: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retrying


# Global health checker instance
health_checker = HealthChecker()


async def get_system_health() -> SystemHealth:
    """Get current system health status"""
    return await health_checker.check_system_health()


async def get_health_summary() -> Dict[str, Any]:
    """Get health summary"""
    return health_checker.get_health_summary()
