"""
Data repository layer for database operations.
"""

from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from .database import db_manager
from .models import Player, PlayerStats, DataQualityLog, ScraperRunLog
from utils.logger import StorageLogger


class PlayerRepository:
    """Repository for Player model operations."""

    def __init__(self):
        """Initialize the player repository."""
        self.logger = StorageLogger()

    def create_or_update_player(
        self, session: Session, player_data: Dict[str, Any]
    ) -> Player:
        """Create or update a player record.

        Args:
            session: Database session
            player_data: Player data dictionary

        Returns:
            Player instance
        """
        try:
            fpl_id = player_data.get("id")
            if not fpl_id:
                raise ValueError("Player ID is required")

            # Try to find existing player
            player = session.query(Player).filter(Player.fpl_id == fpl_id).first()

            if player:
                # Update existing player
                self._update_player_fields(player, player_data)
                self.logger.logger.info(
                    "Updated existing player",
                    table="players",
                    fpl_id=fpl_id,
                    name=player.name,
                )
            else:
                # Create new player
                player = self._create_player_from_data(player_data)
                session.add(player)
                self.logger.logger.info(
                    "Created new player",
                    table="players",
                    fpl_id=fpl_id,
                    name=player.name,
                )

            return player

        except Exception as e:
            self.logger.logger.error(
                "Failed to create/update player",
                table="players",
                fpl_id=player_data.get("id"),
                error=str(e),
            )
            raise

    def _create_player_from_data(self, player_data: Dict[str, Any]) -> Player:
        """Create a Player instance from data dictionary.

        Args:
            player_data: Player data dictionary

        Returns:
            Player instance
        """
        return Player(
            fpl_id=player_data.get("id"),
            name=player_data.get(
                "full_name",
                f"{player_data.get('first_name', '')} {player_data.get('second_name', '')}",
            ).strip(),
            team=player_data.get("team_name", ""),
            position=player_data.get("position", ""),
            price=player_data.get("price", 0.0),
            form=player_data.get("form_float", 0.0),
            total_points=player_data.get("total_points", 0),
            selected_by_percent=player_data.get("selected_by_percent_float", 0.0),
            transfers_in=player_data.get("transfers_in", 0),
            transfers_out=player_data.get("transfers_out", 0),
            goals_scored=player_data.get("goals_scored", 0),
            assists=player_data.get("assists", 0),
            clean_sheets=player_data.get("clean_sheets", 0),
            goals_conceded=player_data.get("goals_conceded", 0),
            own_goals=player_data.get("own_goals", 0),
            penalties_saved=player_data.get("penalties_saved", 0),
            penalties_missed=player_data.get("penalties_missed", 0),
            yellow_cards=player_data.get("yellow_cards", 0),
            red_cards=player_data.get("red_cards", 0),
            saves=player_data.get("saves", 0),
            bonus=player_data.get("bonus", 0),
            bps=player_data.get("bps", 0),
            influence=player_data.get("influence_float", 0.0),
            creativity=player_data.get("creativity_float", 0.0),
            threat=player_data.get("threat_float", 0.0),
            ict_index=player_data.get("ict_index_float", 0.0),
        )

    def _update_player_fields(self, player: Player, player_data: Dict[str, Any]):
        """Update player fields from data dictionary.

        Args:
            player: Player instance to update
            player_data: Player data dictionary
        """
        player.name = player_data.get(
            "full_name",
            f"{player_data.get('first_name', '')} {player_data.get('second_name', '')}",
        ).strip()
        player.team = player_data.get("team_name", player.team)
        player.position = player_data.get("position", player.position)
        player.price = player_data.get("price", player.price)
        player.form = player_data.get("form_float", player.form)
        player.total_points = player_data.get("total_points", player.total_points)
        player.selected_by_percent = player_data.get(
            "selected_by_percent_float", player.selected_by_percent
        )
        player.transfers_in = player_data.get("transfers_in", player.transfers_in)
        player.transfers_out = player_data.get("transfers_out", player.transfers_out)
        player.goals_scored = player_data.get("goals_scored", player.goals_scored)
        player.assists = player_data.get("assists", player.assists)
        player.clean_sheets = player_data.get("clean_sheets", player.clean_sheets)
        player.goals_conceded = player_data.get("goals_conceded", player.goals_conceded)
        player.own_goals = player_data.get("own_goals", player.own_goals)
        player.penalties_saved = player_data.get(
            "penalties_saved", player.penalties_saved
        )
        player.penalties_missed = player_data.get(
            "penalties_missed", player.penalties_missed
        )
        player.yellow_cards = player_data.get("yellow_cards", player.yellow_cards)
        player.red_cards = player_data.get("red_cards", player.red_cards)
        player.saves = player_data.get("saves", player.saves)
        player.bonus = player_data.get("bonus", player.bonus)
        player.bps = player_data.get("bps", player.bps)
        player.influence = player_data.get("influence_float", player.influence)
        player.creativity = player_data.get("creativity_float", player.creativity)
        player.threat = player_data.get("threat_float", player.threat)
        player.ict_index = player_data.get("ict_index_float", player.ict_index)
        player.updated_at = datetime.utcnow()

    def get_player_by_fpl_id(self, session: Session, fpl_id: int) -> Optional[Player]:
        """Get player by FPL ID.

        Args:
            session: Database session
            fpl_id: FPL player ID

        Returns:
            Player instance or None
        """
        return session.query(Player).filter(Player.fpl_id == fpl_id).first()

    def get_players_by_team(self, session: Session, team_name: str) -> List[Player]:
        """Get all players for a team.

        Args:
            session: Database session
            team_name: Team name

        Returns:
            List of Player instances
        """
        return session.query(Player).filter(Player.team == team_name).all()

    def get_players_by_position(self, session: Session, position: str) -> List[Player]:
        """Get all players for a position.

        Args:
            session: Database session
            position: Position (GK, DEF, MID, FWD)

        Returns:
            List of Player instances
        """
        return session.query(Player).filter(Player.position == position).all()


class PlayerStatsRepository:
    """Repository for PlayerStats model operations."""

    def __init__(self):
        """Initialize the player stats repository."""
        self.logger = StorageLogger()

    def create_or_update_stats(
        self,
        session: Session,
        player_id: int,
        gameweek: int,
        stats_data: Dict[str, Any],
        source: str,
    ) -> PlayerStats:
        """Create or update player stats for a gameweek.

        Args:
            session: Database session
            player_id: Player ID
            gameweek: Gameweek number
            stats_data: Stats data dictionary
            source: Data source

        Returns:
            PlayerStats instance
        """
        try:
            # Try to find existing stats
            stats = (
                session.query(PlayerStats)
                .filter(
                    and_(
                        PlayerStats.player_id == player_id,
                        PlayerStats.gameweek == gameweek,
                        PlayerStats.source == source,
                    )
                )
                .first()
            )

            if stats:
                # Update existing stats
                self._update_stats_fields(stats, stats_data)
                self.logger.logger.info(
                    "Updated existing player stats",
                    table="player_stats",
                    player_id=player_id,
                    gameweek=gameweek,
                    source=source,
                )
            else:
                # Create new stats
                stats = self._create_stats_from_data(
                    player_id, gameweek, stats_data, source
                )
                session.add(stats)
                self.logger.logger.info(
                    "Created new player stats",
                    table="player_stats",
                    player_id=player_id,
                    gameweek=gameweek,
                    source=source,
                )

            return stats

        except Exception as e:
            self.logger.logger.error(
                "Failed to create/update player stats",
                table="player_stats",
                player_id=player_id,
                gameweek=gameweek,
                source=source,
                error=str(e),
            )
            raise

    def _create_stats_from_data(
        self, player_id: int, gameweek: int, stats_data: Dict[str, Any], source: str
    ) -> PlayerStats:
        """Create a PlayerStats instance from data dictionary.

        Args:
            player_id: Player ID
            gameweek: Gameweek number
            stats_data: Stats data dictionary
            source: Data source

        Returns:
            PlayerStats instance
        """
        return PlayerStats(
            player_id=player_id,
            gameweek=gameweek,
            goals=stats_data.get("goals", 0),
            assists=stats_data.get("assists", 0),
            minutes=stats_data.get("minutes", 0),
            bonus=stats_data.get("bonus", 0),
            bps=stats_data.get("bps", 0),
            xg=stats_data.get("xg", 0.0),
            xa=stats_data.get("xa", 0.0),
            xgi=stats_data.get("xgi", 0.0),
            xgc=stats_data.get("xgc", 0.0),
            xcs=stats_data.get("xcs", 0.0),
            influence=stats_data.get("influence", 0.0),
            creativity=stats_data.get("creativity", 0.0),
            threat=stats_data.get("threat", 0.0),
            ict_index=stats_data.get("ict_index", 0.0),
            source=source,
        )

    def _update_stats_fields(self, stats: PlayerStats, stats_data: Dict[str, Any]):
        """Update stats fields from data dictionary.

        Args:
            stats: PlayerStats instance to update
            stats_data: Stats data dictionary
        """
        stats.goals = stats_data.get("goals", stats.goals)
        stats.assists = stats_data.get("assists", stats.assists)
        stats.minutes = stats_data.get("minutes", stats.minutes)
        stats.bonus = stats_data.get("bonus", stats.bonus)
        stats.bps = stats_data.get("bps", stats.bps)
        stats.xg = stats_data.get("xg", stats.xg)
        stats.xa = stats_data.get("xa", stats.xa)
        stats.xgi = stats_data.get("xgi", stats.xgi)
        stats.xgc = stats_data.get("xgc", stats.xgc)
        stats.xcs = stats_data.get("xcs", stats.xcs)
        stats.influence = stats_data.get("influence", stats.influence)
        stats.creativity = stats_data.get("creativity", stats.creativity)
        stats.threat = stats_data.get("threat", stats.threat)
        stats.ict_index = stats_data.get("ict_index", stats.ict_index)
        stats.updated_at = datetime.utcnow()

    def get_player_stats(
        self,
        session: Session,
        player_id: int,
        gameweek: Optional[int] = None,
        source: Optional[str] = None,
    ) -> List[PlayerStats]:
        """Get player stats with optional filtering.

        Args:
            session: Database session
            player_id: Player ID
            gameweek: Optional gameweek filter
            source: Optional source filter

        Returns:
            List of PlayerStats instances
        """
        query = session.query(PlayerStats).filter(PlayerStats.player_id == player_id)

        if gameweek is not None:
            query = query.filter(PlayerStats.gameweek == gameweek)

        if source is not None:
            query = query.filter(PlayerStats.source == source)

        return query.order_by(PlayerStats.gameweek.desc()).all()

    def get_gameweek_stats(
        self, session: Session, gameweek: int, source: Optional[str] = None
    ) -> List[PlayerStats]:
        """Get all stats for a gameweek.

        Args:
            session: Database session
            gameweek: Gameweek number
            source: Optional source filter

        Returns:
            List of PlayerStats instances
        """
        query = session.query(PlayerStats).filter(PlayerStats.gameweek == gameweek)

        if source is not None:
            query = query.filter(PlayerStats.source == source)

        return query.all()


class DataQualityRepository:
    """Repository for DataQualityLog model operations."""

    def __init__(self):
        """Initialize the data quality repository."""
        self.logger = StorageLogger()

    def log_quality_check(
        self,
        session: Session,
        source: str,
        data_type: str,
        quality_score: float,
        issues: List[str],
        record_count: int = 0,
        valid_count: int = 0,
        invalid_count: int = 0,
    ) -> DataQualityLog:
        """Log a data quality check result.

        Args:
            session: Database session
            source: Data source
            data_type: Type of data
            quality_score: Quality score (0.0 to 1.0)
            issues: List of issues found
            record_count: Total number of records
            valid_count: Number of valid records
            invalid_count: Number of invalid records

        Returns:
            DataQualityLog instance
        """
        try:
            quality_log = DataQualityLog(
                source=source,
                data_type=data_type,
                quality_score=quality_score,
                issues=",".join(issues) if issues else None,
                record_count=record_count,
                valid_count=valid_count,
                invalid_count=invalid_count,
            )

            session.add(quality_log)

            self.logger.logger.info(
                "Logged data quality check",
                table="data_quality_log",
                source=source,
                data_type=data_type,
                quality_score=quality_score,
                total_issues=len(issues),
            )

            return quality_log

        except Exception as e:
            self.logger.logger.error(
                "Failed to log data quality check",
                table="data_quality_log",
                source=source,
                error=str(e),
            )
            raise


class ScraperRunRepository:
    """Repository for ScraperRunLog model operations."""

    def __init__(self):
        """Initialize the scraper run repository."""
        self.logger = StorageLogger()

    def log_scraper_run(
        self,
        session: Session,
        scraper_name: str,
        status: str,
        start_time: datetime,
        end_time: Optional[datetime] = None,
        duration_seconds: Optional[float] = None,
        records_processed: int = 0,
        records_saved: int = 0,
        error_message: Optional[str] = None,
    ) -> ScraperRunLog:
        """Log a scraper run.

        Args:
            session: Database session
            scraper_name: Name of the scraper
            status: Run status (success, failed, partial)
            start_time: Start time
            end_time: End time
            duration_seconds: Duration in seconds
            records_processed: Number of records processed
            records_saved: Number of records saved
            error_message: Error message if failed

        Returns:
            ScraperRunLog instance
        """
        try:
            run_log = ScraperRunLog(
                scraper_name=scraper_name,
                status=status,
                start_time=start_time,
                end_time=end_time,
                duration_seconds=duration_seconds,
                records_processed=records_processed,
                records_saved=records_saved,
                error_message=error_message,
            )

            session.add(run_log)

            self.logger.logger.info(
                "Logged scraper run",
                table="scraper_run_log",
                scraper_name=scraper_name,
                status=status,
                duration_seconds=duration_seconds,
                records_processed=records_processed,
                records_saved=records_saved,
            )

            return run_log

        except Exception as e:
            self.logger.logger.error(
                "Failed to log scraper run",
                table="scraper_run_log",
                scraper_name=scraper_name,
                error=str(e),
            )
            raise
