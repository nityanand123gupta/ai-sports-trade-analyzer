"""Deterministic statistical modeling used by the Quantitative Analyst agent.

No ML training pipeline is required for a project of this scope -- instead
we use transparent, explainable formulas (aging curve multiplier, surplus
value vs. contract, positional need matching) that an agent can reason
about and cite in its report. Swap in scikit-learn/XGBoost models here if
you want to extend the project with real predictive modeling.
"""
from __future__ import annotations

from dataclasses import dataclass

# Rough NBA aging curve: multiplier applied to current production to project
# value over the remaining life of a contract. Peak production ~ age 27.
_AGE_CURVE = {
    19: 0.80, 20: 0.85, 21: 0.90, 22: 0.94, 23: 0.97, 24: 0.99,
    25: 1.00, 26: 1.00, 27: 1.00, 28: 0.99, 29: 0.97, 30: 0.94,
    31: 0.90, 32: 0.85, 33: 0.79, 34: 0.72, 35: 0.64, 36: 0.55,
    37: 0.46, 38: 0.37,
}


def age_multiplier(age: int) -> float:
    return _AGE_CURVE.get(age, 0.35 if age > 38 else 0.75)


def player_value_score(player: dict) -> float:
    """0-100 composite score blending production (PER, win shares) with an
    aging-curve-adjusted outlook. Higher is better."""
    per = player.get("per", 10.0)
    win_shares = player.get("win_shares", 1.0)
    age_mult = age_multiplier(player.get("age", 27))

    raw = (per * 2.2) + (win_shares * 3.0)
    projected = raw * age_mult
    return round(min(projected, 100.0), 1)


def contract_efficiency(player: dict) -> float:
    """Value score produced per million dollars of salary. Higher = better
    value contract; helps flag salary-dump or bargain pieces."""
    score = player_value_score(player)
    salary_millions = max(player.get("salary", 1) / 1_000_000, 0.1)
    return round(score / salary_millions, 3)


def project_post_trade_value(player: dict, years_out: int = 1) -> float:
    """Project a player's value score N years into the future by walking
    the aging curve forward from their current age."""
    future_age = player.get("age", 27) + years_out
    base = player_value_score(player)
    current_mult = age_multiplier(player.get("age", 27))
    future_mult = age_multiplier(future_age)
    if current_mult == 0:
        return base
    return round(base * (future_mult / current_mult), 1)


@dataclass
class TeamNeedsProfile:
    team_abbr: str
    position_counts: dict[str, int]
    avg_age: float
    total_value_score: float


def analyze_team_needs(team_abbr: str, roster: list[dict]) -> TeamNeedsProfile:
    position_counts: dict[str, int] = {}
    for p in roster:
        position_counts[p["position"]] = position_counts.get(p["position"], 0) + 1
    avg_age = round(sum(p["age"] for p in roster) / len(roster), 1) if roster else 0.0
    total_value = round(sum(player_value_score(p) for p in roster), 1)
    return TeamNeedsProfile(
        team_abbr=team_abbr,
        position_counts=position_counts,
        avg_age=avg_age,
        total_value_score=total_value,
    )


def trade_impact_summary(players_in: list[dict], players_out: list[dict]) -> dict:
    value_in = round(sum(player_value_score(p) for p in players_in), 1)
    value_out = round(sum(player_value_score(p) for p in players_out), 1)
    return {
        "value_acquired": value_in,
        "value_surrendered": value_out,
        "net_value_score": round(value_in - value_out, 1),
        "players_in": [
            {"name": p["name"], "value_score": player_value_score(p)} for p in players_in
        ],
        "players_out": [
            {"name": p["name"], "value_score": player_value_score(p)} for p in players_out
        ],
    }
