"""CLI entrypoint for the AI-Driven Multi-Agent Sports Front Office.

Usage:
    python -m src.main examples/sample_trade.json
    python -m src.main examples/sample_trade.json --agentic   # requires crewai + API key
    python -m src.main examples/sample_trade.json --offline   # skip live nba_api calls
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from src.pipeline import run_trade_analysis, render_markdown_report


def _load_trade(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def main() -> None:
    # Windows terminals often default to a legacy codepage that can't render
    # the emoji/markdown glyphs in the report; force UTF-8 stdout when possible.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="AI Multi-Agent Sports Trade Analyzer")
    parser.add_argument("trade_file", help="Path to a trade proposal JSON file")
    parser.add_argument(
        "--agentic",
        action="store_true",
        help="Run the full CrewAI multi-agent crew (requires crewai + ANTHROPIC_API_KEY)",
    )
    parser.add_argument(
        "--offline",
        action="store_true",
        help="Skip live nba_api lookups and use only the bundled sample dataset",
    )
    parser.add_argument("-o", "--output", help="Optional path to write the markdown report to")
    args = parser.parse_args()

    trade = _load_trade(args.trade_file)

    print("Running deterministic Scout -> Quant -> Cap -> GM pipeline...\n")
    result = run_trade_analysis(trade, use_live_data=not args.offline)
    report = render_markdown_report(result)
    print(report)

    if args.agentic:
        if not os.environ.get("ANTHROPIC_API_KEY"):
            print(
                "\n[!] --agentic requested but ANTHROPIC_API_KEY is not set. "
                "Skipping the CrewAI narrative layer; showing the deterministic report above.",
                file=sys.stderr,
            )
        else:
            try:
                from src.crew import run_agentic_analysis
            except ImportError:
                print(
                    "\n[!] crewai is not installed (pip install -r requirements.txt). "
                    "Skipping the agentic layer.",
                    file=sys.stderr,
                )
            else:
                print("\n\n--- Agentic Crew Narrative (CrewAI + Claude) ---\n")
                narrative = run_agentic_analysis(trade)
                print(narrative)
                report += "\n\n---\n\n## Agentic Crew Narrative\n\n" + narrative

    if args.output:
        Path(args.output).write_text(report, encoding="utf-8")
        print(f"\nReport written to {args.output}")


if __name__ == "__main__":
    main()
