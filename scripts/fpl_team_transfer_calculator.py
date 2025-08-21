#!/usr/bin/env python3
"""
FPL Team Transfer Calculator

This script fetches a specific FPL team by ID and calculates personalized transfer recommendations.
"""

import sys
import os
import asyncio
import logging
import requests
from typing import Dict, Any, List, Optional

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from storage.database import db_manager
from storage.repositories import PlayerRepository
from storage.models import Player
from prediction.scoring.master_score.player_impact_score import PlayerImpactScore
from prediction.optimization.algorithms.transfer_optimizer import TransferOptimizer
from config.settings import get_settings
from utils.cache import get_cache

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class FPLTeamTransferCalculator:
    """Calculator for FPL team transfers based on team ID."""

    def __init__(self, team_id: int):
        self.team_id = team_id
        self.fpl_api_base = "https://fantasy.premierleague.com/api"
        self.settings = get_settings()
        self.cache = get_cache()

    def fetch_team_data(self) -> Dict[str, Any]:
        """Fetch team data from FPL API."""
        try:
            # Try to get from cache first
            cache_key = f"fpl_team_{self.team_id}"
            cached_data = self.cache.get(cache_key)
            if cached_data:
                logger.info(f"Retrieved team data from cache for team {self.team_id}")
                return cached_data

            # Fetch from FPL API
            url = f"{self.fpl_api_base}/entry/{self.team_id}/event/1/picks/"
            logger.info(f"Fetching team data from FPL API: {url}")

            response = requests.get(url, timeout=10)
            response.raise_for_status()

            team_data = response.json()

            # Cache the data for 1 hour
            self.cache.set(cache_key, team_data, ttl=3600)

            logger.info(f"Successfully fetched team data for team {self.team_id}")
            return team_data

        except Exception as e:
            logger.error(f"Failed to fetch team data: {e}")
            return None

    def get_player_details(self, player_ids: List[int]) -> List[Dict[str, Any]]:
        """Get detailed player information from database."""
        try:
            db_manager.initialize()
            session = db_manager.get_sync_session()

            players = []
            for player_id in player_ids:
                player = (
                    session.query(Player).filter(Player.fpl_id == player_id).first()
                )
                if player:
                    players.append(
                        {
                            "id": player.fpl_id,
                            "name": player.name,
                            "team": player.team,
                            "position": player.position,
                            "price": float(player.price),
                            "form": float(player.form) if player.form else 0.0,
                            "total_points": player.total_points,
                            "selected_by_percent": (
                                float(player.selected_by_percent)
                                if player.selected_by_percent
                                else 0.0
                            ),
                            "transfers_in": player.transfers_in,
                            "transfers_out": player.transfers_out,
                            "goals_scored": player.goals_scored,
                            "assists": player.assists,
                            "clean_sheets": player.clean_sheets,
                            "goals_conceded": player.goals_conceded,
                            "own_goals": player.own_goals,
                            "penalties_saved": player.penalties_saved,
                            "penalties_missed": player.penalties_missed,
                            "yellow_cards": player.yellow_cards,
                            "red_cards": player.red_cards,
                            "saves": player.saves,
                            "bonus": player.bonus,
                            "bps": player.bps,
                            "influence": (
                                float(player.influence) if player.influence else 0.0
                            ),
                            "creativity": (
                                float(player.creativity) if player.creativity else 0.0
                            ),
                            "threat": float(player.threat) if player.threat else 0.0,
                            "ict_index": (
                                float(player.ict_index) if player.ict_index else 0.0
                            ),
                            "minutes_played": player.total_points * 10,  # Estimate
                            "games_played": max(
                                1, player.total_points // 10
                            ),  # Estimate
                            "points_per_game": float(player.total_points)
                            / max(1, player.total_points // 10),
                        }
                    )

            session.close()
            return players

        except Exception as e:
            logger.error(f"Failed to get player details: {e}")
            return []

    def get_available_players(self, exclude_ids: List[int]) -> List[Dict[str, Any]]:
        """Get available players for transfers, excluding current squad."""
        try:
            db_manager.initialize()
            session = db_manager.get_sync_session()

            # Get top players by position, excluding current squad
            available_players = []
            for position in ["GK", "DEF", "MID", "FWD"]:
                players = (
                    session.query(Player)
                    .filter(
                        Player.position == position, ~Player.fpl_id.in_(exclude_ids)
                    )
                    .order_by(Player.total_points.desc())
                    .limit(30)  # Top 30 per position
                    .all()
                )

                for player in players:
                    available_players.append(
                        {
                            "id": player.fpl_id,
                            "name": player.name,
                            "team": player.team,
                            "position": player.position,
                            "price": float(player.price),
                            "form": float(player.form) if player.form else 0.0,
                            "total_points": player.total_points,
                            "selected_by_percent": (
                                float(player.selected_by_percent)
                                if player.selected_by_percent
                                else 0.0
                            ),
                            "transfers_in": player.transfers_in,
                            "transfers_out": player.transfers_out,
                            "goals_scored": player.goals_scored,
                            "assists": player.assists,
                            "clean_sheets": player.clean_sheets,
                            "goals_conceded": player.goals_conceded,
                            "own_goals": player.own_goals,
                            "penalties_saved": player.penalties_saved,
                            "penalties_missed": player.penalties_missed,
                            "yellow_cards": player.yellow_cards,
                            "red_cards": player.red_cards,
                            "saves": player.saves,
                            "bonus": player.bonus,
                            "bps": player.bps,
                            "influence": (
                                float(player.influence) if player.influence else 0.0
                            ),
                            "creativity": (
                                float(player.creativity) if player.creativity else 0.0
                            ),
                            "threat": float(player.threat) if player.threat else 0.0,
                            "ict_index": (
                                float(player.ict_index) if player.ict_index else 0.0
                            ),
                            "minutes_played": player.total_points * 10,  # Estimate
                            "games_played": max(
                                1, player.total_points // 10
                            ),  # Estimate
                            "points_per_game": float(player.total_points)
                            / max(1, player.total_points // 10),
                        }
                    )

            session.close()
            return available_players

        except Exception as e:
            logger.error(f"Failed to get available players: {e}")
            return []

    def calculate_team_analysis(
        self, current_squad: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze current team performance."""
        try:
            scorer = PlayerImpactScore({})

            # Calculate scores for current squad
            squad_scores = []
            total_value = 0.0
            position_counts = {"GK": 0, "DEF": 0, "MID": 0, "FWD": 0}

            for player in current_squad:
                score = scorer.calculate_score(player)
                squad_scores.append(score)
                total_value += player["price"]
                position_counts[player["position"]] += 1

            avg_score = sum(squad_scores) / len(squad_scores) if squad_scores else 0
            total_score = sum(squad_scores)

            return {
                "total_score": total_score,
                "average_score": avg_score,
                "total_value": total_value,
                "position_counts": position_counts,
                "player_scores": list(
                    zip([p["name"] for p in current_squad], squad_scores)
                ),
            }

        except Exception as e:
            logger.error(f"Failed to calculate team analysis: {e}")
            return {}

    def get_transfer_recommendations(
        self,
        current_squad: List[Dict[str, Any]],
        available_players: List[Dict[str, Any]],
        budget: float = 100.0,
        transfers_available: int = 2,
        strategy: str = "balanced",
    ) -> List[Any]:
        """Get transfer recommendations using the prediction engine."""
        try:
            optimizer = TransferOptimizer({})

            recommendations = optimizer.optimize_transfers(
                current_squad=current_squad,
                available_players=available_players,
                budget=budget,
                transfers_available=transfers_available,
                strategy=strategy,
            )

            return recommendations

        except Exception as e:
            logger.error(f"Failed to get transfer recommendations: {e}")
            return []

    def get_top_overall_players(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top overall players regardless of current squad."""
        try:
            db_manager.initialize()
            session = db_manager.get_sync_session()

            # Get top players by total points
            players = (
                session.query(Player)
                .order_by(Player.total_points.desc())
                .limit(limit)
                .all()
            )

            top_players = []
            for player in players:
                top_players.append(
                    {
                        "id": player.fpl_id,
                        "name": player.name,
                        "team": player.team,
                        "position": player.position,
                        "price": float(player.price),
                        "form": float(player.form) if player.form else 0.0,
                        "total_points": player.total_points,
                        "selected_by_percent": (
                            float(player.selected_by_percent)
                            if player.selected_by_percent
                            else 0.0
                        ),
                        "transfers_in": player.transfers_in,
                        "transfers_out": player.transfers_out,
                        "goals_scored": player.goals_scored,
                        "assists": player.assists,
                        "clean_sheets": player.clean_sheets,
                        "goals_conceded": player.goals_conceded,
                        "own_goals": player.own_goals,
                        "penalties_saved": player.penalties_saved,
                        "penalties_missed": player.penalties_missed,
                        "yellow_cards": player.yellow_cards,
                        "red_cards": player.red_cards,
                        "saves": player.saves,
                        "bonus": player.bonus,
                        "bps": player.bps,
                        "influence": (
                            float(player.influence) if player.influence else 0.0
                        ),
                        "creativity": (
                            float(player.creativity) if player.creativity else 0.0
                        ),
                        "threat": float(player.threat) if player.threat else 0.0,
                        "ict_index": (
                            float(player.ict_index) if player.ict_index else 0.0
                        ),
                        "minutes_played": player.total_points * 10,  # Estimate
                        "games_played": max(1, player.total_points // 10),  # Estimate
                        "points_per_game": float(player.total_points)
                        / max(1, player.total_points // 10),
                    }
                )

            session.close()
            return top_players

        except Exception as e:
            logger.error(f"Failed to get top overall players: {e}")
            return []

    def get_manual_transfer_suggestions(
        self,
        current_squad: List[Dict[str, Any]],
        available_players: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Get manual transfer suggestions based on performance gaps."""
        try:
            scorer = PlayerImpactScore({})

            # Score all players
            current_scores = {}
            for player in current_squad:
                score = scorer.calculate_score(player)
                current_scores[player["id"]] = score

            available_scores = {}
            for player in available_players:
                score = scorer.calculate_score(player)
                available_scores[player["id"]] = score

            # Find worst performers in current squad
            worst_players = sorted(
                current_squad, key=lambda x: current_scores[x["id"]]
            )[
                :5
            ]  # Bottom 5

            # Find best available players by position
            best_by_position = {}
            for player in available_players:
                pos = player["position"]
                if pos not in best_by_position:
                    best_by_position[pos] = []
                best_by_position[pos].append(player)

            # Sort by score
            for pos in best_by_position:
                best_by_position[pos].sort(
                    key=lambda x: available_scores[x["id"]], reverse=True
                )

            suggestions = []

            # Suggest replacements for worst players
            for worst_player in worst_players:
                pos = worst_player["position"]
                if pos in best_by_position and best_by_position[pos]:
                    best_replacement = best_by_position[pos][0]

                    current_score = current_scores[worst_player["id"]]
                    replacement_score = available_scores[best_replacement["id"]]
                    improvement = replacement_score - current_score

                    if improvement > 0.5:  # Only suggest if significant improvement
                        suggestions.append(
                            {
                                "type": "upgrade",
                                "player_out": worst_player,
                                "player_in": best_replacement,
                                "current_score": current_score,
                                "replacement_score": replacement_score,
                                "improvement": improvement,
                                "reason": f"Upgrade {worst_player['position']} position",
                            }
                        )

            # Sort by improvement
            suggestions.sort(key=lambda x: x["improvement"], reverse=True)
            return suggestions[:10]  # Top 10 suggestions

        except Exception as e:
            logger.error(f"Failed to get manual transfer suggestions: {e}")
            return []

    def get_pis_breakdown(self, player: Dict[str, Any]) -> Dict[str, Any]:
        """Get detailed breakdown of PIS calculation for a player."""
        try:
            scorer = PlayerImpactScore({})

            # Calculate all sub-scores
            sub_scores = scorer._calculate_sub_scores(player)

            # Calculate base score
            base_score = scorer.calculate_base_score(sub_scores)

            # Calculate interaction bonus
            interaction_bonus = scorer.calculate_interaction_bonus(sub_scores)

            # Calculate risk penalty
            risk_penalty = scorer.calculate_risk_penalty(player)

            # Final score
            final_score = scorer.calculate_score(player)

            # Get confidence
            confidence = scorer.calculate_confidence_multiplier(player, sub_scores)

            return {
                "player_name": player["name"],
                "final_pis": final_score,
                "base_score": base_score,
                "interaction_bonus": interaction_bonus,
                "risk_penalty": risk_penalty,
                "confidence": confidence,
                "sub_scores": sub_scores,
                "sub_score_weights": scorer.sub_score_weights,
                "interaction_thresholds": scorer.interaction_bonuses,
            }

        except Exception as e:
            logger.error(f"Failed to get PIS breakdown: {e}")
            return {}

    def analyze_interaction_bonus_reason(
        self, sub_scores: Dict[str, float], thresholds: Dict[str, float]
    ) -> str:
        """Analyze why interaction bonus is 0 and what would be needed to get bonuses."""
        reasons = []

        # Check each interaction type
        aqs = sub_scores.get("AdvancedQualityScore", 0.0)
        fcs = sub_scores.get("FormConsistencyScore", 0.0)
        fxs = sub_scores.get("FixtureScore", 0.0)
        vs = sub_scores.get("ValueScore", 0.0)
        tms = sub_scores.get("TeamMomentumScore", 0.0)

        # Quality + Form interaction
        quality_form_threshold = thresholds.get("quality_form_threshold", 7.0)
        if aqs < quality_form_threshold or fcs < quality_form_threshold:
            reasons.append(
                f"Quality+Form: AQS({aqs:.2f}) or FCS({fcs:.2f}) < {quality_form_threshold}"
            )

        # Form + Fixture interaction
        form_fixture_threshold = thresholds.get("form_fixture_threshold", 6.5)
        if fcs < form_fixture_threshold or fxs < form_fixture_threshold:
            reasons.append(
                f"Form+Fixture: FCS({fcs:.2f}) or FxS({fxs:.2f}) < {form_fixture_threshold}"
            )

        # Quality + Value interaction
        quality_value_threshold = thresholds.get("quality_value_threshold", 6.0)
        if aqs < quality_value_threshold or vs < quality_value_threshold:
            reasons.append(
                f"Quality+Value: AQS({aqs:.2f}) or VS({vs:.2f}) < {quality_value_threshold}"
            )

        # Team + Form interaction
        team_form_threshold = thresholds.get("team_form_threshold", 6.0)
        if tms < team_form_threshold or fcs < team_form_threshold:
            reasons.append(
                f"Team+Form: TMS({tms:.2f}) or FCS({fcs:.2f}) < {team_form_threshold}"
            )

        if not reasons:
            return "All thresholds met - should have interaction bonus!"

        return " | ".join(reasons[:3])  # Show top 3 reasons

    def analyze_pis_contributors(self, player: Dict[str, Any]) -> str:
        """Analyze which factors contribute most to a player's PIS score."""
        try:
            breakdown = self.get_pis_breakdown(player)
            if not breakdown:
                return "Unable to analyze PIS breakdown"

            sub_scores = breakdown["sub_scores"]
            weights = breakdown["sub_score_weights"]

            # Calculate weighted contributions
            contributions = []
            for score_name, score_value in sub_scores.items():
                weight = weights.get(score_name, 0.1)
                weighted_contribution = score_value * weight
                contributions.append(
                    {
                        "name": score_name,
                        "score": score_value,
                        "weight": weight,
                        "contribution": weighted_contribution,
                    }
                )

            # Sort by contribution
            contributions.sort(key=lambda x: x["contribution"], reverse=True)

            # Find the biggest contributor
            top_contributor = contributions[0]

            # Create analysis text
            analysis = f"Top contributor: {top_contributor['name']} "
            analysis += f"(score: {top_contributor['score']:.2f}, "
            analysis += f"weight: {top_contributor['weight']:.1%}, "
            analysis += f"contribution: {top_contributor['contribution']:.2f})"

            # Add second biggest if significant
            if len(contributions) > 1:
                second = contributions[1]
                if second["contribution"] > 0.5:  # Only mention if significant
                    analysis += f"\nSecond: {second['name']} "
                    analysis += f"(contribution: {second['contribution']:.2f})"

            return analysis

        except Exception as e:
            logger.error(f"Failed to analyze PIS contributors: {e}")
            return "Unable to analyze contributors"

    def show_detailed_pis_analysis(self, current_squad: List[Dict[str, Any]]) -> None:
        """Show detailed PIS analysis for each player."""
        print(f"\n🔍 Detailed PIS Analysis:")
        print("=" * 60)

        scorer = PlayerImpactScore({})

        for i, player in enumerate(current_squad, 1):
            breakdown = self.get_pis_breakdown(player)
            if not breakdown:
                continue

            print(
                f"\n{i:2d}. {player['name']} ({player['position']}) - {player['team']}"
            )
            print(f"    Final PIS: {breakdown['final_pis']:.2f}")
            print(f"    Base Score: {breakdown['base_score']:.2f}")
            print(f"    Interaction Bonus: {breakdown['interaction_bonus']:.2f}")
            print(f"    Risk Penalty: {breakdown['risk_penalty']:.2f}")
            print(f"    Confidence: {breakdown['confidence']:.2f}")

            # Show sub-scores
            print(f"    Sub-scores:")
            for score_name, score_value in breakdown["sub_scores"].items():
                weight = breakdown["sub_score_weights"].get(score_name, 0.1)
                weighted = score_value * weight
                print(
                    f"      {score_name}: {score_value:.2f} (weight: {weight:.1%}, contribution: {weighted:.2f})"
                )

            # Show top contributor analysis
            contributor_analysis = self.analyze_pis_contributors(player)
            print(f"    💡 {contributor_analysis}")

    def analyze_team(self) -> Dict[str, Any]:
        """Complete team analysis and transfer recommendations."""
        print(f"🔍 Analyzing FPL Team {self.team_id}")
        print("=" * 60)

        # Fetch team data
        team_data = self.fetch_team_data()
        if not team_data:
            print("❌ Failed to fetch team data from FPL API")
            return {}

        # Extract player IDs from picks
        picks = team_data.get("picks", [])
        if not picks:
            print("❌ No player picks found in team data")
            return {}

        player_ids = [pick["element"] for pick in picks]
        print(f"📊 Found {len(player_ids)} players in your squad")

        # Get current squad details
        current_squad = self.get_player_details(player_ids)
        if not current_squad:
            print("❌ Failed to get current squad details")
            return {}

        print(f"✅ Retrieved details for {len(current_squad)} players")

        # Analyze current team
        team_analysis = self.calculate_team_analysis(current_squad)
        if not team_analysis:
            print("❌ Failed to analyze current team")
            return {}

        # Display current team analysis
        print(f"\n📈 Current Team Analysis:")
        print(f"  Total PIS Score: {team_analysis['total_score']:.2f}")
        print(f"  Average PIS Score: {team_analysis['average_score']:.2f}")
        print(f"  Total Squad Value: £{team_analysis['total_value']:.1f}m")
        print(f"  Position Distribution: {team_analysis['position_counts']}")

        print(f"\n👥 Your Squad Performance (Ranked):")
        sorted_squad = sorted(
            team_analysis["player_scores"], key=lambda x: x[1], reverse=True
        )
        for i, (name, score) in enumerate(sorted_squad, 1):
            emoji = (
                "⭐"
                if score > 4.0
                else "✅" if score > 3.5 else "⚠️" if score > 3.0 else "❌"
            )
            print(f"  {i:2d}. {emoji} {name}: PIS = {score:.2f}")

        # Show detailed PIS analysis for top and bottom performers
        print(f"\n🔍 Detailed PIS Breakdown Analysis:")
        print("=" * 60)

        # Show top 3 performers with full breakdown
        print(f"\n🏆 Top 3 Performers - Complete PIS Breakdown:")
        top_3 = sorted_squad[:3]
        for name, score in top_3:
            player = next((p for p in current_squad if p["name"] == name), None)
            if player:
                breakdown = self.get_pis_breakdown(player)
                if breakdown:
                    print(f"\n⭐ {name} (Final PIS: {score:.2f})")
                    print(f"   Base Score: {breakdown['base_score']:.2f}")
                    print(f"   Interaction Bonus: {breakdown['interaction_bonus']:.2f}")
                    print(f"   Risk Penalty: {breakdown['risk_penalty']:.2f}")
                    print(f"   Confidence: {breakdown['confidence']:.2f}")

                    # Show all sub-scores
                    print(f"   📊 All Sub-Scores:")
                    for score_name, score_value in breakdown["sub_scores"].items():
                        weight = breakdown["sub_score_weights"].get(score_name, 0.1)
                        weighted = score_value * weight
                        print(
                            f"      {score_name}: {score_value:.2f} (weight: {weight:.1%}, contribution: {weighted:.2f})"
                        )

                    # Show why interaction bonus is 0
                    if breakdown["interaction_bonus"] == 0:
                        reason = self.analyze_interaction_bonus_reason(
                            breakdown["sub_scores"], breakdown["interaction_thresholds"]
                        )
                        print(f"   💡 Why no interaction bonus: {reason}")

                    # Show top contributor
                    sub_scores = breakdown["sub_scores"]
                    weights = breakdown["sub_score_weights"]
                    top_contributor = max(
                        [
                            (name, score * weights.get(name, 0.1))
                            for name, score in sub_scores.items()
                        ],
                        key=lambda x: x[1],
                    )
                    print(
                        f"   🎯 Biggest contributor: {top_contributor[0]} ({top_contributor[1]:.2f})"
                    )

        # Show bottom 3 performers with full breakdown
        print(f"\n⚠️ Bottom 3 Performers - Complete PIS Breakdown:")
        bottom_3 = sorted_squad[-3:]
        for name, score in bottom_3:
            player = next((p for p in current_squad if p["name"] == name), None)
            if player:
                breakdown = self.get_pis_breakdown(player)
                if breakdown:
                    print(f"\n❌ {name} (Final PIS: {score:.2f})")
                    print(f"   Base Score: {breakdown['base_score']:.2f}")
                    print(f"   Interaction Bonus: {breakdown['interaction_bonus']:.2f}")
                    print(f"   Risk Penalty: {breakdown['risk_penalty']:.2f}")
                    print(f"   Confidence: {breakdown['confidence']:.2f}")

                    # Show all sub-scores
                    print(f"   📊 All Sub-Scores:")
                    for score_name, score_value in breakdown["sub_scores"].items():
                        weight = breakdown["sub_score_weights"].get(score_name, 0.1)
                        weighted = score_value * weight
                        print(
                            f"      {score_name}: {score_value:.2f} (weight: {weight:.1%}, contribution: {weighted:.2f})"
                        )

                    # Show why interaction bonus is 0
                    if breakdown["interaction_bonus"] == 0:
                        reason = self.analyze_interaction_bonus_reason(
                            breakdown["sub_scores"], breakdown["interaction_thresholds"]
                        )
                        print(f"   💡 Why no interaction bonus: {reason}")

                    # Show top contributor
                    sub_scores = breakdown["sub_scores"]
                    weights = breakdown["sub_score_weights"]
                    top_contributor = max(
                        [
                            (name, score * weights.get(name, 0.1))
                            for name, score in sub_scores.items()
                        ],
                        key=lambda x: x[1],
                    )
                    print(
                        f"   🎯 Biggest contributor: {top_contributor[0]} ({top_contributor[1]:.2f})"
                    )

        # Get top overall players
        print(f"\n🏆 Top 10 Overall Players (All Positions):")
        top_overall = self.get_top_overall_players(10)
        for i, player in enumerate(top_overall, 1):
            scorer = PlayerImpactScore({})
            score = scorer.calculate_score(player)
            emoji = (
                "🧤"
                if player["position"] == "GK"
                else (
                    "🛡️"
                    if player["position"] == "DEF"
                    else "⚽" if player["position"] == "MID" else "🎯"
                )
            )
            print(
                f"  {i:2d}. {emoji} {player['name']} ({player['team']}) - PIS: {score:.2f}, Points: {player['total_points']}, Price: £{player['price']:.1f}m"
            )

        # Get available players for transfers
        available_players = self.get_available_players(player_ids)
        print(f"\n📊 Found {len(available_players)} available players for transfers")

        # Get transfer recommendations
        recommendations = self.get_transfer_recommendations(
            current_squad=current_squad,
            available_players=available_players,
            budget=100.0,
            transfers_available=2,
            strategy="balanced",
        )

        print(f"\n🎯 Optimized Transfer Recommendations:")
        if recommendations:
            for i, combo in enumerate(recommendations[:5]):  # Top 5 recommendations
                print(f"\n📈 Recommendation #{i+1}:")
                print(f"  Expected Gain: {combo.total_expected_gain:.2f} points")
                print(f"  Confidence: {combo.total_confidence:.2f}")
                print(f"  Risk: {combo.total_risk:.2f}")
                print(f"  Budget Impact: £{combo.budget_impact:.1f}m")
                print(f"  Reasoning: {combo.reasoning}")

                for transfer in combo.transfers:
                    print(
                        f"    🔄 {transfer.player_out['name']} → {transfer.player_in['name']}"
                    )
                    print(
                        f"       Expected Gain: {transfer.expected_points_gain:.2f} points"
                    )
        else:
            print("  No optimized transfer combinations found with current constraints")

        # Get manual transfer suggestions
        print(f"\n💡 Manual Transfer Suggestions (Even if not 'optimal'):")
        manual_suggestions = self.get_manual_transfer_suggestions(
            current_squad, available_players
        )

        if manual_suggestions:
            for i, suggestion in enumerate(manual_suggestions[:5], 1):
                print(f"\n🔄 Suggestion #{i}:")
                print(
                    f"  Out: {suggestion['player_out']['name']} (PIS: {suggestion['current_score']:.2f})"
                )
                print(
                    f"  In:  {suggestion['player_in']['name']} (PIS: {suggestion['replacement_score']:.2f})"
                )
                print(f"  Improvement: +{suggestion['improvement']:.2f} points")
                print(f"  Reason: {suggestion['reason']}")
        else:
            print("  No manual transfer suggestions available")

        # Additional insights
        print(f"\n💭 Strategic Insights:")

        # Budget analysis
        remaining_budget = 100.0 - team_analysis["total_value"]
        print(f"  💰 Remaining Budget: £{remaining_budget:.1f}m")

        # Position analysis
        pos_counts = team_analysis["position_counts"]
        if pos_counts["DEF"] > 5:
            print(
                f"  ⚠️  Heavy on defenders ({pos_counts['DEF']}) - consider midfield/forward options"
            )
        elif pos_counts["MID"] > 6:
            print(
                f"  ⚠️  Heavy on midfielders ({pos_counts['MID']}) - consider defensive/forward options"
            )
        elif pos_counts["FWD"] > 4:
            print(
                f"  ⚠️  Heavy on forwards ({pos_counts['FWD']}) - consider defensive/midfield options"
            )
        else:
            print(f"  ✅ Good position balance")

        # Performance analysis
        avg_score = team_analysis["average_score"]
        if avg_score > 4.0:
            print(f"  🎉 Excellent team performance (avg PIS: {avg_score:.2f})")
        elif avg_score > 3.5:
            print(f"  ✅ Good team performance (avg PIS: {avg_score:.2f})")
        elif avg_score > 3.0:
            print(
                f"  ⚠️  Average team performance (avg PIS: {avg_score:.2f}) - consider upgrades"
            )
        else:
            print(
                f"  ❌ Below average performance (avg PIS: {avg_score:.2f}) - significant improvements needed"
            )

        return {
            "team_id": self.team_id,
            "current_squad": current_squad,
            "team_analysis": team_analysis,
            "recommendations": recommendations,
            "manual_suggestions": manual_suggestions,
            "top_overall": top_overall,
        }


async def main():
    """Main execution function."""
    team_id = 2165234  # Your FPL team ID

    print("🚀 FPL Team Transfer Calculator")
    print("=" * 60)
    print(f"📊 Analyzing Team ID: {team_id}")
    print("=" * 60)

    calculator = FPLTeamTransferCalculator(team_id)
    result = calculator.analyze_team()

    if result:
        print(f"\n✅ Analysis completed for team {team_id}")
        print("🎯 Ready to make informed transfer decisions!")
    else:
        print(f"\n❌ Failed to analyze team {team_id}")
        return 1

    return 0


if __name__ == "__main__":
    exit(asyncio.run(main()))
