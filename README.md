# AI-Driven Multi-Agent Sports Front Office

A pro-sports trade analysis system built with **agentic coding**: specialized
autonomous agents (Data Scout, Quantitative Analyst, CBA/Cap Specialist,
General Manager) collaborate to evaluate whether a proposed NBA trade is
statistically sound *and* legal under the league's salary-cap rules.

The project ships as two layers:

1. **Deterministic core** (`src/pipeline.py`) — real player/salary data,
   an aging-curve value model, and a CBA salary-matching/apron rules engine.
   Runs with **zero API keys**, fully unit tested.
2. **Agentic layer** (`src/crew.py`) — a [CrewAI](https://github.com/crewAIInc/crewAI)
   crew of four LLM-powered agent personas that reason over the deterministic
   layer's verified numbers to produce a narrative trade recommendation.
   Opt-in via `--agentic`, requires `ANTHROPIC_API_KEY`.

This split matters: the LLM never has to "do the salary math" (a place LLMs
are unreliable) — it only reasons about strategy, fit, and framing on top of
numbers a human can audit and trust.

## Architecture

```
                    ┌─────────────────┐
   trade proposal → │   Data Scout     │  pulls roster/salary/stat data
                    └────────┬─────────┘  (live nba_api, falls back to
                             │             bundled offline dataset)
              ┌──────────────┴──────────────┐
              ▼                             ▼
   ┌─────────────────────┐      ┌───────────────────────┐
   │ Quantitative Analyst │      │  CBA / Cap Specialist  │
   │ aging-curve value    │      │  salary-matching bands,│
   │ scores, team fit     │      │  apron rules, legality │
   └──────────┬───────────┘      └───────────┬───────────┘
              └──────────────┬───────────────┘
                              ▼
                    ┌──────────────────┐
                    │   General Manager │  synthesizes a graded
                    │   agent            │  trade recommendation
                    └──────────────────┘
```

## Quick start

```bash
pip install -r requirements.txt

# Deterministic mode (no API key required)
python -m src.main examples/sample_trade.json

# Force offline mode (skip live nba_api network calls)
python -m src.main examples/sample_trade.json --offline

# Full agentic mode (CrewAI + Claude narrative synthesis)
cp .env.example .env   # then add your ANTHROPIC_API_KEY
python -m src.main examples/sample_trade.json --agentic
```

### Propose your own trade

Create a JSON file like `examples/sample_trade.json`:

```json
{
  "team_a": "BOS",
  "team_b": "LAL",
  "team_a_sends": ["Jrue Holiday"],
  "team_b_sends": ["D'Angelo Russell", "Gabe Vincent"]
}
```

Player and team names must exist in `src/data/sample_players.json` (the
offline dataset) — see that file for the full roster of playable teams
(`BOS`, `LAL`, `DAL`, `MIA`).

## Running tests

```bash
pip install -r requirements.txt
pytest -v
```

## Project layout

```
src/
  data/
    cap_rules.json         # 2025-26 salary cap / tax / apron thresholds
    sample_players.json    # offline fallback roster + salary + stat dataset
  tools/
    nba_data_tool.py       # live nba_api fetch + offline fallback
    cap_rules.py           # CBA salary-matching & apron legality engine
    quant_analysis.py      # aging-curve player value model
  agents/
    crew_tools.py          # CrewAI tool wrapping the deterministic pipeline
  pipeline.py               # deterministic Scout -> Quant -> Cap -> GM pipeline
  crew.py                   # CrewAI 4-agent crew (agentic narrative layer)
  main.py                   # CLI entrypoint
tests/                      # pytest unit tests for cap rules, quant model, pipeline
examples/sample_trade.json  # example trade proposal
```

## How the CBA rules engine works

`src/tools/cap_rules.py` implements a simplified version of the real 2023
NBA CBA:

- **Under the cap** — a team can take back incoming salary up to its cap
  room plus the outgoing salary.
- **Over the cap, under the first apron** (includes taxpayers) — salary
  must "match" within banded multipliers (200% / 175% / 125% + $250k
  depending on outgoing salary size).
- **First apron** — can take back at most 100% of outgoing salary + $250k,
  and cannot aggregate multiple outgoing players' salaries into one trade.
- **Second apron** — cannot take back *more* salary than sent out at all,
  and also cannot aggregate outgoing salaries.

When a trade violates these rules, the Cap Specialist proposes a concrete
balancing move (shed more salary) rather than just rejecting the trade —
mirroring the "feedback loop" pattern common in agentic workflows.

> These figures/rules are simplified for educational/simulation purposes.
> Verify against the official CBA before using for anything real.

## Extending this project

- Swap `src/tools/quant_analysis.py`'s formulas for a trained scikit-learn/
  XGBoost model (the blueprint this project is based on suggests this).
- Add a **Sentiment Analysis Agent** with a Reddit/X API tool to gauge fan
  reaction to a rumored trade.
- Add a **Negotiation Simulation**: two GM agents (one per team) counter-offer
  each other in a loop (`Process.hierarchical` in CrewAI) until they converge
  or give up.
- Point `nba_data_tool.py` at other sports' APIs (FBref for soccer,
  Sportradar for NFL/MLB) and swap in that sport's CBA/cap rules.
