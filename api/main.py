"""
FastAPI application for FPL Chase API.
The powerful backend engine for FPL Hype Index - empowering your gut feelings with data-driven insights.
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from config.settings import get_settings
from utils.logger import get_logger
from orchestration.health_checker import get_system_health, get_health_summary
from orchestration.coordinator import DataCoordinator
from storage.database import db_manager
from storage.repositories import PlayerRepository, TeamRepository, FixtureRepository
from api.routes import prediction

# Initialize logger
logger = get_logger("api")

# Create FastAPI app
app = FastAPI(
    title="FPL Chase API",
    description="The powerful backend engine for FPL Hype Index. Empowering your gut feelings with data-driven insights through advanced Player Impact Score (PIS) calculations, transfer optimization, and comprehensive FPL analytics.",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global coordinator instance
coordinator = DataCoordinator()


@app.on_event("startup")
async def startup_event():
    """Initialize application on startup."""
    logger.info("Starting FPL Chase API - The Backend Engine for FPL Hype Index")

    # Initialize database
    try:
        db_manager.initialize()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on application shutdown."""
    logger.info("Shutting down FPL Chase API")
    db_manager.close()


# ============================================================================
# HEALTH & STATUS ENDPOINTS
# ============================================================================


@app.get("/health")
async def health_check():
    """Basic health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "2.0.0",
        "service": "FPL Chase API",
        "brand": "FPL Hype Index",
        "motto": "Empower Your Gut Feelings",
    }


@app.get("/health/detailed")
async def detailed_health_check():
    """Detailed system health check."""
    try:
        health_summary = await get_health_summary()
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "system_health": health_summary,
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")


@app.get("/status/database")
async def database_status():
    """Check database connectivity and status."""
    try:
        # Test database connection
        async for session in db_manager.get_async_session():
            result = await session.execute("SELECT 1 as test")
            test_result = result.scalar()

            if test_result == 1:
                return {
                    "status": "connected",
                    "timestamp": datetime.now().isoformat(),
                    "database": "healthy",
                }
            else:
                raise HTTPException(status_code=500, detail="Database test failed")

    except Exception as e:
        logger.error(f"Database status check failed: {e}")
        return {
            "status": "disconnected",
            "timestamp": datetime.now().isoformat(),
            "error": str(e),
        }


# ============================================================================
# DATA FETCHING ENDPOINTS
# ============================================================================


@app.get("/data/players")
async def get_players(
    limit: int = 100,
    offset: int = 0,
    team: Optional[str] = None,
    position: Optional[str] = None,
    min_points: Optional[int] = None,
    max_points: Optional[int] = None,
):
    """Get player data with optional filtering."""
    try:
        async for session in db_manager.get_async_session():
            repo = PlayerRepository(session)
            players = await repo.get_players(
                limit=limit,
                offset=offset,
                team=team,
                position=position,
                min_points=min_points,
                max_points=max_points,
            )

            return {
                "status": "success",
                "count": len(players),
                "limit": limit,
                "offset": offset,
                "players": players,
            }

    except Exception as e:
        logger.error(f"Failed to fetch players: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch players: {str(e)}"
        )


@app.get("/data/players/{player_id}")
async def get_player(player_id: int):
    """Get specific player by ID."""
    try:
        async for session in db_manager.get_async_session():
            repo = PlayerRepository(session)
            player = await repo.get_player_by_id(player_id)

            if not player:
                raise HTTPException(status_code=404, detail="Player not found")

            return {"status": "success", "player": player}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch player {player_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch player: {str(e)}")


@app.get("/data/teams")
async def get_teams():
    """Get all Premier League teams data."""
    try:
        async for session in db_manager.get_async_session():
            # Get all teams from teams table
            from sqlalchemy import text

            result = await session.execute(
                text("SELECT * FROM teams ORDER BY position, name")
            )
            teams = [dict(row._mapping) for row in result.fetchall()]

            # If no teams in database, return the 20 Premier League teams
            if not teams:
                premier_league_teams = [
                    {"name": "Arsenal", "short_name": "ARS", "position": 0},
                    {"name": "Aston Villa", "short_name": "AVL", "position": 0},
                    {"name": "Bournemouth", "short_name": "BOU", "position": 0},
                    {"name": "Brentford", "short_name": "BRE", "position": 0},
                    {"name": "Brighton", "short_name": "BHA", "position": 0},
                    {"name": "Burnley", "short_name": "BUR", "position": 0},
                    {"name": "Chelsea", "short_name": "CHE", "position": 0},
                    {"name": "Crystal Palace", "short_name": "CRY", "position": 0},
                    {"name": "Everton", "short_name": "EVE", "position": 0},
                    {"name": "Fulham", "short_name": "FUL", "position": 0},
                    {"name": "Liverpool", "short_name": "LIV", "position": 0},
                    {"name": "Luton", "short_name": "LUT", "position": 0},
                    {"name": "Manchester City", "short_name": "MCI", "position": 0},
                    {"name": "Manchester United", "short_name": "MUN", "position": 0},
                    {"name": "Newcastle", "short_name": "NEW", "position": 0},
                    {"name": "Nottingham Forest", "short_name": "NFO", "position": 0},
                    {"name": "Sheffield United", "short_name": "SHU", "position": 0},
                    {"name": "Tottenham", "short_name": "TOT", "position": 0},
                    {"name": "West Ham", "short_name": "WHU", "position": 0},
                    {"name": "Wolves", "short_name": "WOL", "position": 0},
                ]
                return {"status": "success", "count": 20, "teams": premier_league_teams}

            return {"status": "success", "count": len(teams), "teams": teams}

    except Exception as e:
        logger.error(f"Failed to fetch teams: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch teams: {str(e)}")


@app.get("/data/fixtures")
async def get_fixtures(gameweek: Optional[int] = None, limit: Optional[int] = 10):
    """Get fixtures data."""
    try:
        from sqlalchemy import text

        async for session in db_manager.get_async_session():
            if gameweek:
                # Get fixtures for specific gameweek
                result = await session.execute(
                    text(
                        """
                        SELECT f.*, 
                               ht.name as home_team_name, ht.short_name as home_team_short,
                               at.name as away_team_name, at.short_name as away_team_short
                        FROM fixtures f
                        JOIN teams ht ON f.team_h_id = ht.id
                        JOIN teams at ON f.team_a_id = at.id
                        WHERE f.event = :gameweek
                        ORDER BY f.kickoff_time
                    """
                    ),
                    {"gameweek": gameweek},
                )
            else:
                # Get next upcoming fixtures
                result = await session.execute(
                    text(
                        """
                        SELECT f.*, 
                               ht.name as home_team_name, ht.short_name as home_team_short,
                               at.name as away_team_name, at.short_name as away_team_short
                        FROM fixtures f
                        JOIN teams ht ON f.team_h_id = ht.id
                        JOIN teams at ON f.team_a_id = at.id
                        WHERE f.finished = false
                        ORDER BY f.kickoff_time
                        LIMIT :limit
                    """
                    ),
                    {"limit": limit},
                )

            fixtures = [dict(row._mapping) for row in result.fetchall()]

            return {"status": "success", "count": len(fixtures), "fixtures": fixtures}

    except Exception as e:
        logger.error(f"Failed to fetch fixtures: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch fixtures: {str(e)}"
        )


@app.get("/data/teams/{team_name}")
async def get_team(team_name: str):
    """Get specific team by name."""
    try:
        async for session in db_manager.get_async_session():
            # Get team data from teams table
            from sqlalchemy import text

            result = await session.execute(
                text(
                    "SELECT * FROM teams WHERE name = :team_name OR short_name = :team_name"
                ),
                {"team_name": team_name},
            )
            team_row = result.fetchone()

            if not team_row:
                raise HTTPException(status_code=404, detail="Team not found")

            team_data = dict(team_row._mapping)

            # Get team players
            result = await session.execute(
                text(
                    "SELECT * FROM players WHERE team = :team_name ORDER BY position, name"
                ),
                {"team_name": team_data["name"]},
            )
            players = [dict(row._mapping) for row in result.fetchall()]

            response_data = {
                "id": team_data["id"],
                "fpl_id": team_data["fpl_id"],
                "name": team_data["name"],
                "short_name": team_data["short_name"],
                "code": team_data["code"],
                "strength": team_data["strength"],
                "position": team_data["position"],
                "points": team_data["points"],
                "played": team_data["played"],
                "win": team_data["win"],
                "loss": team_data["loss"],
                "draw": team_data["draw"],
                "goals_for": team_data["goals_for"],
                "goals_against": team_data["goals_against"],
                "goal_difference": team_data["goal_difference"],
                "form": team_data["form"],
                "player_count": len(players),
                "players": players,
            }

            return {"status": "success", "team": response_data}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch team {team_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch team: {str(e)}")


# ============================================================================
# DATA COLLECTION CONTROL ENDPOINTS
# ============================================================================


@app.post("/trigger/scraper/{scraper_name}")
async def trigger_scraper(scraper_name: str, background_tasks: BackgroundTasks):
    """Manually trigger a specific scraper."""
    try:
        # Add scraper execution to background tasks
        background_tasks.add_task(coordinator.run_scraper, scraper_name)

        return {
            "status": "triggered",
            "scraper": scraper_name,
            "timestamp": datetime.now().isoformat(),
            "message": f"Scraper {scraper_name} has been queued for execution",
        }

    except Exception as e:
        logger.error(f"Failed to trigger scraper {scraper_name}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to trigger scraper: {str(e)}"
        )


@app.post("/trigger/all-scrapers")
async def trigger_all_scrapers(background_tasks: BackgroundTasks):
    """Manually trigger all scrapers."""
    try:
        # Get list of available scrapers
        available_scrapers = coordinator.get_available_scrapers()

        # Add all scrapers to background tasks
        for scraper_name in available_scrapers:
            background_tasks.add_task(coordinator.run_scraper, scraper_name)

        return {
            "status": "triggered",
            "scrapers": available_scrapers,
            "count": len(available_scrapers),
            "timestamp": datetime.now().isoformat(),
            "message": f"All {len(available_scrapers)} scrapers have been queued for execution",
        }

    except Exception as e:
        logger.error(f"Failed to trigger all scrapers: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to trigger scrapers: {str(e)}"
        )


@app.get("/scrapers/status")
async def get_scrapers_status():
    """Get status of all scrapers."""
    try:
        available_scrapers = coordinator.get_available_scrapers()

        scraper_status = []
        for scraper_name in available_scrapers:
            # Get last run info from database
            async for session in db_manager.get_async_session():
                from storage.models import DataQualityLog
                from sqlalchemy import func, desc

                result = await session.execute(
                    func.select(DataQualityLog)
                    .where(DataQualityLog.scraper_name == scraper_name)
                    .order_by(desc(DataQualityLog.timestamp))
                    .limit(1)
                )
                last_run = result.scalar()

                status = {
                    "name": scraper_name,
                    "available": True,
                    "last_run": last_run.timestamp.isoformat() if last_run else None,
                    "last_status": last_run.status if last_run else "unknown",
                    "last_duration": last_run.duration if last_run else None,
                }
                scraper_status.append(status)
                break

        return {
            "status": "success",
            "scrapers": scraper_status,
            "count": len(scraper_status),
        }

    except Exception as e:
        logger.error(f"Failed to get scrapers status: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get scrapers status: {str(e)}"
        )


# ============================================================================
# STATISTICS ENDPOINTS
# ============================================================================


@app.get("/stats/overview")
async def get_stats_overview():
    """Get overview statistics of collected data."""
    try:
        from sqlalchemy import text, func
        from storage.models import DataQualityLog

        async for session in db_manager.get_async_session():
            # Get player count
            player_result = await session.execute(text("SELECT COUNT(*) FROM players"))
            player_count = player_result.scalar()

            # Get team count
            team_result = await session.execute(text("SELECT COUNT(*) FROM teams"))
            team_count = team_result.scalar()

            # Get fixture count
            fixture_result = await session.execute(
                text("SELECT COUNT(*) FROM fixtures")
            )
            fixture_count = fixture_result.scalar()

            # Get recent data quality logs (simplified)
            recent_runs = 0  # Placeholder - can be enhanced later

            return {
                "status": "success",
                "timestamp": datetime.now().isoformat(),
                "statistics": {
                    "total_players": player_count,
                    "total_teams": team_count,
                    "total_fixtures": fixture_count,
                    "runs_last_7_days": recent_runs,
                },
            }

    except Exception as e:
        logger.error(f"Failed to get statistics: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get statistics: {str(e)}"
        )


# ============================================================================
# INCLUDE PREDICTION ROUTES
# ============================================================================

# Include prediction engine routes
app.include_router(prediction.router, prefix="/api/v1")


# ============================================================================
# ERROR HANDLERS
# ============================================================================


@app.exception_handler(404)
async def not_found_handler(request, exc):
    """Handle 404 errors."""
    return JSONResponse(
        status_code=404,
        content={
            "error": "Not found",
            "message": "The requested resource was not found",
            "timestamp": datetime.now().isoformat(),
        },
    )


@app.exception_handler(500)
async def internal_error_handler(request, exc):
    """Handle 500 errors."""
    logger.error(f"Internal server error: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": "An unexpected error occurred",
            "timestamp": datetime.now().isoformat(),
        },
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "api.main:app", host="0.0.0.0", port=8000, reload=True, log_level="info"
    )
