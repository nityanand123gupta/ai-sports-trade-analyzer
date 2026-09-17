"""Deterministic 4-agent trade analysis pipeline.

This is the guaranteed-to-run core of the project: Data Scout -> Quantitative
Analyst + Cap Specialist (parallel, conceptually) -> GM synthesis. It needs
no API key and no network access (falls back to bundled sample data).

`src/crew.py` wraps these same building blocks in a real CrewAI multi-agent
crew for a more fully "agentic" run when an LLM API key is available.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.tools.nba_data_tool import fetch_league_dataset, find_player, load_cap_rules, team_payroll
from src.tools.cap_rules import check_trade_legality, suggest_balancing_move
from src.tools.quant_analysis import analyze_team_needs, trade_impact_summary


@dataclass
class TradeSide:
    team_abbr: str
    players_sent: list[dict] = field(default_factory=list)
    players_received: list[dict] = field(default_factory=list)


def _resolve_players(teams: dict, names: list[str]) -> list[dict]:
    resolved = []
    for name in names:
        _, player = find_player(teams, name)
        if player is None:
            raise ValueError(f"Player not found in dataset: {name!r}")
        resolved.append(player)
    return resolved


def _grade(net_value_score: float, legal: bool) -> str:
    if not legal:
        return "F (Illegal Trade)"
    if net_value_score >= 15:
        return "A"
    if net_value_score >= 7:
        return "B+"
    if net_value_score >= 2:
        return "B"
    if net_value_score >= -2:
        return "C+"
    if net_value_score >= -7:
        return "C"
    return "D"


def run_trade_analysis(trade: dict[str, Any], use_live_data: bool = True) -> dict[str, Any]:
    """trade = {"team_a": "BOS", "team_b": "LAL",
                "team_a_sends": [...names...], "team_b_sends": [...names...]}
    """
    # --- Step 1: Data Scout ---
    teams = fetch_league_dataset(use_live=use_live_data)
    cap_rules = load_cap_rules()

    team_a, team_b = trade["team_a"], trade["team_b"]
    a_sends = _resolve_players(teams, trade["team_a_sends"])
    b_sends = _resolve_players(teams, trade["team_b_sends"])

    a_payroll_before = team_payroll(teams, team_a)
    b_payroll_before = team_payroll(teams, team_b)

    a_outgoing_salary = sum(p["salary"] for p in a_sends)
    b_outgoing_salary = sum(p["salary"] for p in b_sends)

    # --- Step 2a: Cap Specialist (runs for both sides) ---
    a_legality = check_trade_legality(
        team_abbr=team_a,
        current_payroll=a_payroll_before,
        outgoing_salary=a_outgoing_salary,
        incoming_salary=b_outgoing_salary,
        outgoing_player_count=len(a_sends),
        cap_rules=cap_rules,
    )
    b_legality = check_trade_legality(
        team_abbr=team_b,
        current_payroll=b_payroll_before,
        outgoing_salary=b_outgoing_salary,
        incoming_salary=a_outgoing_salary,
        outgoing_player_count=len(b_sends),
        cap_rules=cap_rules,
    )

    # --- Feedback loop: suggest balancing moves if illegal ---
    a_suggestion = suggest_balancing_move(a_legality)
    b_suggestion = suggest_balancing_move(b_legality)

    # --- Step 2b: Quantitative Analyst ---
    a_needs_before = analyze_team_needs(team_a, teams[team_a]["roster"])
    b_needs_before = analyze_team_needs(team_b, teams[team_b]["roster"])

    a_impact = trade_impact_summary(players_in=b_sends, players_out=a_sends)
    b_impact = trade_impact_summary(players_in=a_sends, players_out=b_sends)

    # --- Step 3: GM synthesis ---
    a_grade = _grade(a_impact["net_value_score"], a_legality.legal)
    b_grade = _grade(b_impact["net_value_score"], b_legality.legal)

    return {
        "trade": trade,
        "cap_rules_season": cap_rules["season"],
        "teams": {
            team_a: {
                "team_name": teams[team_a]["name"],
                "payroll_before": a_payroll_before,
                "cap_status": a_legality.cap_status.value,
                "legality": a_legality,
                "balancing_suggestion": a_suggestion,
                "needs_before": a_needs_before,
                "impact": a_impact,
                "grade": a_grade,
            },
            team_b: {
                "team_name": teams[team_b]["name"],
                "payroll_before": b_payroll_before,
                "cap_status": b_legality.cap_status.value,
                "legality": b_legality,
                "balancing_suggestion": b_suggestion,
                "needs_before": b_needs_before,
                "impact": b_impact,
                "grade": b_grade,
            },
        },
    }


def render_markdown_report(result: dict[str, Any]) -> str:
    trade = result["trade"]
    team_a, team_b = trade["team_a"], trade["team_b"]
    lines: list[str] = []

    lines.append(f"# Trade Analysis Report ({result['cap_rules_season']})")
    lines.append("")
    lines.append(
        f"**Proposed trade:** {team_a} sends {', '.join(trade['team_a_sends'])} "
        f"to {team_b} for {', '.join(trade['team_b_sends'])}."
    )
    lines.append("")

    for team_abbr in (team_a, team_b):
        t = result["teams"][team_abbr]
        legality = t["legality"]
        lines.append(f"## {t['team_name']} ({team_abbr}) — Grade: {t['grade']}")
        lines.append(f"- Cap status: **{t['cap_status']}** (payroll ${t['payroll_before']:,})")
        lines.append(
            f"- Trade legality: {'✅ LEGAL' if legality.legal else '❌ ILLEGAL'} "
            f"(outgoing ${legality.outgoing_salary:,}, incoming ${legality.incoming_salary:,}, "
            f"max allowed incoming ${legality.max_incoming_allowed:,})"
        )
        for v in legality.violations:
            lines.append(f"  - ⚠️ {v}")
        if t["balancing_suggestion"]:
            lines.append(f"  - 💡 {t['balancing_suggestion']}")
        lines.append(
            f"- Quant impact: value acquired {t['impact']['value_acquired']}, "
            f"value surrendered {t['impact']['value_surrendered']}, "
            f"**net {t['impact']['net_value_score']:+}**"
        )
        lines.append(
            f"- Roster before trade: avg age {t['needs_before'].avg_age}, "
            f"positions {t['needs_before'].position_counts}"
        )
        lines.append("")

    return "\n".join(lines)
