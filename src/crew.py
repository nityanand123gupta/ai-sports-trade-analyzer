"""CrewAI multi-agent orchestration for the AI Front Office.

Four specialized agents collaborate sequentially, each grounded in the same
deterministic tool output (src/agents/crew_tools.py -> src/pipeline.py) so
the LLM never has to invent salary math -- it reasons about narrative,
team fit, and negotiation strategy on top of verified numbers.

Requires `crewai` installed and an LLM API key (ANTHROPIC_API_KEY by
default). If either is missing, use src/pipeline.py directly instead --
see src/main.py for the automatic fallback.
"""
from __future__ import annotations

import json
import os

from crewai import Agent, Crew, Process, Task

from src.agents.crew_tools import run_full_trade_analysis_tool

DEFAULT_MODEL = os.environ.get("TRADE_ANALYZER_MODEL", "anthropic/claude-sonnet-4-5-20250929")


def build_crew(trade: dict) -> Crew:
    trade_json = json.dumps(trade)
    llm = DEFAULT_MODEL

    data_scout = Agent(
        role="Data Scout",
        goal="Retrieve and summarize accurate roster, salary, and performance data for every team involved in a proposed trade.",
        backstory=(
            "A meticulous former advance scout turned data analyst. You trust the tools over "
            "assumptions and always cite the exact numbers you pulled."
        ),
        llm=llm,
        verbose=True,
    )

    quant_analyst = Agent(
        role="Lead Quantitative Analyst",
        goal="Project the on-court impact of the trade for each team using advanced metrics and aging curves.",
        backstory=(
            "A data-driven analyst who looks strictly at advanced metrics, aging curves, and "
            "team fit rather than reputation or name value."
        ),
        llm=llm,
        verbose=True,
    )

    cap_specialist = Agent(
        role="CBA and Salary Cap Specialist",
        goal="Audit the trade for strict compliance with salary-matching and apron rules, and propose fixes for illegal trades.",
        backstory=(
            "You know the Collective Bargaining Agreement inside and out. You block trades "
            "that break cap rules and always propose a concrete fix instead of just saying no."
        ),
        llm=llm,
        verbose=True,
    )

    gm_agent = Agent(
        role="General Manager",
        goal="Synthesize the scouting, analytics, and cap-compliance findings into a final graded trade recommendation for both teams.",
        backstory=(
            "A veteran GM who weighs win-now value, financial risk, and long-term roster "
            "construction. You give a clear letter grade for each side and explain your reasoning."
        ),
        llm=llm,
        verbose=True,
    )

    scout_task = Task(
        description=(
            f"Using the Run Full Trade Analysis tool with trade_json={trade_json!r}, "
            "retrieve the underlying data and summarize each team's current cap status "
            "and the players changing hands. Report only facts, no opinions."
        ),
        expected_output="A short factual data summary for both teams involved in the trade.",
        agent=data_scout,
        tools=[run_full_trade_analysis_tool],
    )

    quant_task = Task(
        description=(
            "Using the same tool output, analyze the net value score for each team and explain "
            "what it means for on-court performance, citing the value acquired vs. surrendered."
        ),
        expected_output="A quantitative impact analysis paragraph per team.",
        agent=quant_analyst,
        tools=[run_full_trade_analysis_tool],
        context=[scout_task],
    )

    cap_task = Task(
        description=(
            "Using the same tool output, state clearly whether the trade is CBA-legal for each "
            "team. If illegal, explain the violation in plain English and state the suggested "
            "balancing move from the tool output."
        ),
        expected_output="A cap-compliance verdict (LEGAL/ILLEGAL) with reasoning for each team.",
        agent=cap_specialist,
        tools=[run_full_trade_analysis_tool],
        context=[scout_task],
    )

    gm_task = Task(
        description=(
            "Combine the scouting summary, quantitative analysis, and cap-compliance verdict into "
            "one final report. Give each team a letter grade (matching the tool's computed grade), "
            "explain the trade-off in 2-3 sentences per team, and give a one-line overall verdict "
            "on whether this trade is likely to happen."
        ),
        expected_output="A final markdown trade recommendation report with letter grades for both teams.",
        agent=gm_agent,
        context=[scout_task, quant_task, cap_task],
    )

    return Crew(
        agents=[data_scout, quant_analyst, cap_specialist, gm_agent],
        tasks=[scout_task, quant_task, cap_task, gm_task],
        process=Process.sequential,
        verbose=True,
    )


def run_agentic_analysis(trade: dict) -> str:
    crew = build_crew(trade)
    result = crew.kickoff()
    return str(result)
