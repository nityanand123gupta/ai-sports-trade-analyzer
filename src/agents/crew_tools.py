"""CrewAI tool wrappers around the deterministic analysis functions.

Keeping all real logic in src/tools/* and src/pipeline.py means the CrewAI
agents are reasoning *on top of* trustworthy, testable computations instead
of hallucinating salary math -- the LLM's job is narrative synthesis and
judgment calls (team fit, risk framing), not arithmetic.
"""
from __future__ import annotations

import json

from crewai.tools import tool

from src.pipeline import run_trade_analysis, render_markdown_report


@tool("Run Full Trade Analysis")
def run_full_trade_analysis_tool(trade_json: str) -> str:
    """Runs the full deterministic Scout -> Quant -> Cap -> GM pipeline for a
    proposed trade and returns a structured summary plus a markdown report.

    Args:
        trade_json: JSON string with keys team_a, team_b, team_a_sends
            (list of player names), team_b_sends (list of player names).
    """
    trade = json.loads(trade_json)
    result = run_trade_analysis(trade)
    report = render_markdown_report(result)

    summary = {
        team: {
            "grade": data["grade"],
            "cap_status": data["cap_status"],
            "legal": data["legality"].legal,
            "violations": data["legality"].violations,
            "net_value_score": data["impact"]["net_value_score"],
        }
        for team, data in result["teams"].items()
    }
    return json.dumps({"summary": summary, "markdown_report": report}, indent=2)
