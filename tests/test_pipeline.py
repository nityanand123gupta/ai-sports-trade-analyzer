import pytest

from src.pipeline import render_markdown_report, run_trade_analysis

SAMPLE_TRADE = {
    "team_a": "BOS",
    "team_b": "LAL",
    "team_a_sends": ["Jrue Holiday"],
    "team_b_sends": ["D'Angelo Russell", "Gabe Vincent"],
}


def test_run_trade_analysis_offline_end_to_end():
    result = run_trade_analysis(SAMPLE_TRADE, use_live_data=False)
    assert set(result["teams"].keys()) == {"BOS", "LAL"}
    for team_data in result["teams"].values():
        assert team_data["grade"]
        assert team_data["legality"] is not None


def test_render_markdown_report_contains_team_names():
    result = run_trade_analysis(SAMPLE_TRADE, use_live_data=False)
    report = render_markdown_report(result)
    assert "Boston Celtics" in report
    assert "Los Angeles Lakers" in report
    assert "Grade:" in report


def test_unknown_player_raises_value_error():
    bad_trade = {**SAMPLE_TRADE, "team_a_sends": ["Nonexistent Player"]}
    with pytest.raises(ValueError):
        run_trade_analysis(bad_trade, use_live_data=False)
