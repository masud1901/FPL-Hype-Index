"""
Prediction API Routes

This module provides API endpoints for the FPL prediction engine, including
transfer recommendations, player scoring, and backtesting functionality.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import JSONResponse
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field
import logging

from prediction.optimization.algorithms.transfer_optimizer import (
    TransferOptimizer,
    TransferRecommendation,
)
from prediction.scoring.master_score.player_impact_score import PlayerImpactScore
from prediction.validation.backtesting.backtest_engine import BacktestEngine
from prediction.validation.backtesting.performance_metrics import PerformanceMetrics
from config.settings import get_settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/prediction", tags=["prediction"])


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================


class PlayerData(BaseModel):
    """Player data model for API requests"""

    id: str
    name: str
    position: str
    team: str
    price: float
    form: float = 0.0
    total_points: int = 0
    minutes_played: int = 0
    goals: int = 0
    assists: int = 0
    clean_sheets: int = 0
    saves: int = 0
    goals_conceded: int = 0
    bonus_points: int = 0
    injury_history: List[str] = []
    age: int = 25
    rotation_risk: bool = False


class SquadData(BaseModel):
    """Squad data model for API requests"""

    players: List[PlayerData]
    budget: float = 0.0
    transfers_available: int = 1


class TransferRequest(BaseModel):
    """Transfer optimization request model"""

    current_squad: SquadData
    available_players: List[PlayerData]
    strategy: str = Field(
        default="balanced", description="Strategy: balanced, aggressive, conservative"
    )
    max_transfers: int = Field(
        default=2, ge=1, le=3, description="Maximum transfers to consider"
    )


class TransferResponse(BaseModel):
    """Transfer recommendation response model"""

    player_out: PlayerData
    player_in: PlayerData
    expected_points_gain: float
    confidence_score: float
    risk_score: float
    reasoning: str


class TransferCombinationResponse(BaseModel):
    """Transfer combination response model"""

    transfers: List[TransferResponse]
    total_expected_gain: float
    total_confidence: float
    total_risk: float
    budget_impact: float
    reasoning: str


class PlayerScoreRequest(BaseModel):
    """Player scoring request model"""

    player: PlayerData


class PlayerScoreResponse(BaseModel):
    """Player scoring response model"""

    player_id: str
    player_name: str
    final_pis: float
    confidence: float
    sub_scores: Dict[str, float]
    reasoning: str


class BacktestRequest(BaseModel):
    """Backtest request model"""

    start_gameweek: int = Field(ge=1, le=38)
    end_gameweek: int = Field(ge=1, le=38)
    initial_squad: SquadData
    strategy_config: Dict[str, Any] = Field(default_factory=dict)


class BacktestResponse(BaseModel):
    """Backtest response model"""

    start_gameweek: int
    end_gameweek: int
    total_points: float
    average_points_per_gameweek: float
    total_transfers: int
    total_transfer_hits: int
    final_squad_value: float
    performance_metrics: Dict[str, float]
    gameweek_results: List[Dict[str, Any]]


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def get_optimizer() -> TransferOptimizer:
    """Get transfer optimizer instance"""
    settings = get_settings()
    return TransferOptimizer(settings.dict())


def get_scorer() -> PlayerImpactScore:
    """Get player impact scorer instance"""
    settings = get_settings()
    return PlayerImpactScore(settings.dict())


def get_backtest_engine() -> BacktestEngine:
    """Get backtest engine instance"""
    settings = get_settings()
    return BacktestEngine(settings.dict())


def convert_player_to_dict(player: PlayerData) -> Dict[str, Any]:
    """Convert PlayerData model to dictionary"""
    return player.dict()


def convert_dict_to_player(player_dict: Dict[str, Any]) -> PlayerData:
    """Convert dictionary to PlayerData model"""
    return PlayerData(**player_dict)


# ============================================================================
# PREDICTION ENDPOINTS
# ============================================================================


@router.post("/scores/player", response_model=PlayerScoreResponse)
async def calculate_player_score(
    request: PlayerScoreRequest, scorer: PlayerImpactScore = Depends(get_scorer)
):
    """
    Calculate Player Impact Score for a single player.

    This endpoint calculates the comprehensive Player Impact Score (PIS) for a given player,
    including all sub-scores and confidence metrics.
    """
    try:
        # Convert player data to dictionary
        player_data = convert_player_to_dict(request.player)

        # Calculate score
        score_result = scorer.calculate_pis(player_data)

        # Create response
        response = PlayerScoreResponse(
            player_id=player_data["id"],
            player_name=player_data["name"],
            final_pis=score_result["final_pis"],
            confidence=score_result["confidence"],
            sub_scores=score_result["sub_scores"],
            reasoning=f"PIS calculated based on {len(score_result['sub_scores'])} sub-scores",
        )

        return response

    except Exception as e:
        logger.error(f"Error calculating player score: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to calculate player score: {str(e)}"
        )


@router.post("/scores/batch", response_model=List[PlayerScoreResponse])
async def calculate_player_scores_batch(
    players: List[PlayerData], scorer: PlayerImpactScore = Depends(get_scorer)
):
    """
    Calculate Player Impact Scores for multiple players.

    This endpoint calculates PIS for a batch of players, useful for ranking
    and comparison purposes.
    """
    try:
        responses = []

        for player in players:
            try:
                # Convert player data to dictionary
                player_data = convert_player_to_dict(player)

                # Calculate score
                score_result = scorer.calculate_pis(player_data)

                # Create response
                response = PlayerScoreResponse(
                    player_id=player_data["id"],
                    player_name=player_data["name"],
                    final_pis=score_result["final_pis"],
                    confidence=score_result["confidence"],
                    sub_scores=score_result["sub_scores"],
                    reasoning=f"PIS calculated based on {len(score_result['sub_scores'])} sub-scores",
                )

                responses.append(response)

            except Exception as e:
                logger.warning(f"Failed to score player {player.name}: {e}")
                # Add error response
                responses.append(
                    PlayerScoreResponse(
                        player_id=player.id,
                        player_name=player.name,
                        final_pis=0.0,
                        confidence=0.0,
                        sub_scores={},
                        reasoning=f"Error: {str(e)}",
                    )
                )

        return responses

    except Exception as e:
        logger.error(f"Error calculating batch player scores: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to calculate batch scores: {str(e)}"
        )


@router.post(
    "/transfers/recommendations", response_model=List[TransferCombinationResponse]
)
async def get_transfer_recommendations(
    request: TransferRequest, optimizer: TransferOptimizer = Depends(get_optimizer)
):
    """
    Get transfer recommendations for the current squad.

    This endpoint analyzes the current squad and available players to provide
    optimal transfer recommendations based on the specified strategy.

    The endpoint returns multiple transfer combinations ranked by expected gain,
    allowing managers to choose the best option for their strategy.
    """
    try:
        # Convert request data to dictionaries
        current_squad = [
            convert_player_to_dict(p) for p in request.current_squad.players
        ]
        available_players = [
            convert_player_to_dict(p) for p in request.available_players
        ]

        # Get transfer recommendations
        recommendations = optimizer.optimize_transfers(
            current_squad=current_squad,
            available_players=available_players,
            budget=request.current_squad.budget,
            transfers_available=request.max_transfers,
            strategy=request.strategy,
        )

        # Convert to response format
        response_combinations = []
        for combination in recommendations:
            # Convert transfers
            transfer_responses = []
            for transfer in combination.transfers:
                transfer_response = TransferResponse(
                    player_out=convert_dict_to_player(transfer.player_out),
                    player_in=convert_dict_to_player(transfer.player_in),
                    expected_points_gain=transfer.expected_points_gain,
                    confidence_score=transfer.confidence_score,
                    risk_score=transfer.risk_score,
                    reasoning=transfer.reasoning,
                )
                transfer_responses.append(transfer_response)

            # Create combination response
            combination_response = TransferCombinationResponse(
                transfers=transfer_responses,
                total_expected_gain=combination.total_expected_gain,
                total_confidence=combination.total_confidence,
                total_risk=combination.total_risk,
                budget_impact=combination.budget_impact,
                reasoning=combination.reasoning,
            )
            response_combinations.append(combination_response)

        return response_combinations

    except Exception as e:
        logger.error(f"Error getting transfer recommendations: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get transfer recommendations: {str(e)}"
        )


@router.post("/transfers/single", response_model=List[TransferResponse])
async def get_single_transfer_recommendations(
    request: TransferRequest, optimizer: TransferOptimizer = Depends(get_optimizer)
):
    """
    Get single transfer recommendations.

    This endpoint provides individual transfer recommendations (one player out,
    one player in) rather than combinations.
    """
    try:
        # Convert request data to dictionaries
        current_squad = [
            convert_player_to_dict(p) for p in request.current_squad.players
        ]
        available_players = [
            convert_player_to_dict(p) for p in request.available_players
        ]

        # Get single transfer recommendations
        recommendations = optimizer.get_single_transfer_recommendations(
            current_squad=current_squad,
            available_players=available_players,
            budget=request.current_squad.budget,
        )

        # Convert to response format
        response_transfers = []
        for rec in recommendations:
            transfer_response = TransferResponse(
                player_out=convert_dict_to_player(rec.player_out),
                player_in=convert_dict_to_player(rec.player_in),
                expected_points_gain=rec.expected_points_gain,
                confidence_score=rec.confidence_score,
                risk_score=rec.risk_score,
                reasoning=rec.reasoning,
            )
            response_transfers.append(transfer_response)

        return response_transfers

    except Exception as e:
        logger.error(f"Error getting single transfer recommendations: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get single transfer recommendations: {str(e)}",
        )


@router.post("/backtest", response_model=BacktestResponse)
async def run_backtest(
    request: BacktestRequest, engine: BacktestEngine = Depends(get_backtest_engine)
):
    """
    Run a backtest simulation.

    This endpoint runs a complete backtest simulation over the specified gameweek
    range to validate the prediction engine's performance.
    """
    try:
        # Convert request data to dictionaries
        initial_squad = [
            convert_player_to_dict(p) for p in request.initial_squad.players
        ]

        # Run backtest
        result = engine.run_backtest(
            start_gameweek=request.start_gameweek,
            end_gameweek=request.end_gameweek,
            initial_squad=initial_squad,
            strategy_config=request.strategy_config,
        )

        # Convert gameweek results to dictionaries
        gameweek_results = []
        for gw_result in result.gameweek_results:
            gw_dict = {
                "gameweek": gw_result.gameweek,
                "total_points": gw_result.total_points,
                "squad_points": gw_result.squad_points,
                "bench_points": gw_result.bench_points,
                "captain_points": gw_result.captain_points,
                "transfers_made": gw_result.transfers_made,
                "transfer_hits": gw_result.transfer_hits,
                "squad_value": gw_result.squad_value,
                "captain_choice": gw_result.captain_choice,
                "vice_captain_choice": gw_result.vice_captain_choice,
            }
            gameweek_results.append(gw_dict)

        # Create response
        response = BacktestResponse(
            start_gameweek=result.start_gameweek,
            end_gameweek=result.end_gameweek,
            total_points=result.total_points,
            average_points_per_gameweek=result.average_points_per_gameweek,
            total_transfers=result.total_transfers,
            total_transfer_hits=result.total_transfer_hits,
            final_squad_value=result.final_squad_value,
            performance_metrics=result.performance_metrics,
            gameweek_results=gameweek_results,
        )

        return response

    except Exception as e:
        logger.error(f"Error running backtest: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to run backtest: {str(e)}")


@router.get("/strategies")
async def get_available_strategies():
    """
    Get available optimization strategies.

    This endpoint returns information about the available transfer optimization
    strategies and their parameters.
    """
    strategies = {
        "balanced": {
            "name": "Balanced Strategy",
            "description": "Balances performance and risk for consistent results",
            "max_transfers_per_week": 1,
            "min_confidence_threshold": 0.6,
            "max_risk_threshold": 0.4,
            "suitable_for": "Most managers, consistent performance",
        },
        "aggressive": {
            "name": "Aggressive Strategy",
            "description": "Focuses on high-ceiling players with higher risk tolerance",
            "max_transfers_per_week": 2,
            "min_confidence_threshold": 0.5,
            "max_risk_threshold": 0.6,
            "suitable_for": "Risk-taking managers, chasing high scores",
        },
        "conservative": {
            "name": "Conservative Strategy",
            "description": "Prioritizes consistency and low-risk transfers",
            "max_transfers_per_week": 1,
            "min_confidence_threshold": 0.8,
            "max_risk_threshold": 0.2,
            "suitable_for": "Cautious managers, avoiding transfer hits",
        },
    }

    return strategies


@router.get("/health")
async def prediction_health_check():
    """
    Health check for prediction engine components.

    This endpoint checks the health of the prediction engine components
    including the scorer, optimizer, and backtest engine.
    """
    try:
        health_status = {"status": "healthy", "components": {}}

        # Check scorer
        try:
            scorer = get_scorer()
            health_status["components"]["scorer"] = "healthy"
        except Exception as e:
            health_status["components"]["scorer"] = f"unhealthy: {str(e)}"
            health_status["status"] = "degraded"

        # Check optimizer
        try:
            optimizer = get_optimizer()
            health_status["components"]["optimizer"] = "healthy"
        except Exception as e:
            health_status["components"]["optimizer"] = f"unhealthy: {str(e)}"
            health_status["status"] = "degraded"

        # Check backtest engine
        try:
            engine = get_backtest_engine()
            health_status["components"]["backtest_engine"] = "healthy"
        except Exception as e:
            health_status["components"]["backtest_engine"] = f"unhealthy: {str(e)}"
            health_status["status"] = "degraded"

        return health_status

    except Exception as e:
        logger.error(f"Prediction health check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")


@router.get("/metrics/performance")
async def get_performance_metrics(
    predicted_scores: List[float] = Query(..., description="List of predicted scores"),
    actual_points: List[float] = Query(..., description="List of actual points"),
):
    """
    Calculate performance metrics for prediction validation.

    This endpoint calculates comprehensive performance metrics to evaluate
    the prediction engine's accuracy and reliability.
    """
    try:
        if len(predicted_scores) != len(actual_points):
            raise HTTPException(
                status_code=400,
                detail="Predicted scores and actual points must have the same length",
            )

        # Calculate metrics
        metrics_calculator = PerformanceMetrics()
        metrics = metrics_calculator.calculate_all_metrics(
            predicted_scores, actual_points
        )

        return {
            "metrics": metrics,
            "summary": {
                "total_predictions": len(predicted_scores),
                "correlation": metrics.get("spearman_correlation", 0.0),
                "precision": metrics.get("top_10_precision", 0.0),
                "calibration": metrics.get("calibration_score", 0.0),
            },
        }

    except Exception as e:
        logger.error(f"Error calculating performance metrics: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to calculate metrics: {str(e)}"
        )
