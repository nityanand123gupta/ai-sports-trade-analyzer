"""Data access layer used by the Data Scout agent.

Tries to pull live stats via the `nba_api` package. Falls back to the bundled
offline sample dataset (src/data/sample_players.json) whenever the network
call fails (no internet, stats.nba.com rate limit, sandboxed environment,
etc.) so the rest of the pipeline always has data to work with.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
SAMPLE_PLAYERS_PATH = DATA_DIR / "sample_players.json"
CAP_RULES_PATH = DATA_DIR / "cap_rules.json"


def load_cap_rules() -> dict[str, Any]:
    with open(CAP_RULES_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _load_offline_dataset() -> dict[str, Any]:
    with open(SAMPLE_PLAYERS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)["teams"]


def fetch_league_dataset(use_live: bool = True) -> dict[str, Any]:
    """Return {team_abbr: {"name": ..., "roster": [player, ...]}}.

    When use_live=True, attempts to enrich the offline dataset with live
    per-game stats from nba_api. If that fails for any reason, silently
    returns the offline dataset unmodified.
    """
    teams = _load_offline_dataset()
    if not use_live:
        return teams

    try:
        from nba_api.stats.static import players as static_players
        from nba_api.stats.endpoints import playercareerstats

        for team_abbr, team in teams.items():
            for player in team["roster"]:
                matches = static_players.find_players_by_full_name(player["name"])
                if not matches:
                    continue
                player_id = matches[0]["id"]
                career = playercareerstats.PlayerCareerStats(player_id=player_id, timeout=5)
                df = career.get_data_frames()[0]
                if df.empty:
                    continue
                latest = df.iloc[-1]
                player["live_stats"] = {
                    "season": latest.get("SEASON_ID"),
                    "pts": float(latest.get("PTS", 0)),
                    "reb": float(latest.get("REB", 0)),
                    "ast": float(latest.get("AST", 0)),
                    "gp": int(latest.get("GP", 0)),
                }
    except Exception:
        # Offline / rate-limited / package missing — fall back silently.
        pass

    return teams


def find_player(teams: dict[str, Any], name: str) -> tuple[str, dict[str, Any]] | tuple[None, None]:
    for team_abbr, team in teams.items():
        for player in team["roster"]:
            if player["name"].lower() == name.lower():
                return team_abbr, player
    return None, None


def team_payroll(teams: dict[str, Any], team_abbr: str) -> int:
    team = teams[team_abbr]
    return sum(p["salary"] for p in team["roster"])
