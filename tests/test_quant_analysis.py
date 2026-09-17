from src.tools.quant_analysis import (
    age_multiplier,
    analyze_team_needs,
    contract_efficiency,
    player_value_score,
    project_post_trade_value,
    trade_impact_summary,
)

YOUNG_STAR = {"name": "Young Star", "position": "SG", "age": 26, "salary": 20_000_000, "per": 24.0, "win_shares": 8.0}
AGING_VET = {"name": "Aging Vet", "position": "C", "age": 37, "salary": 10_000_000, "per": 12.0, "win_shares": 2.0}


def test_age_multiplier_peaks_around_27():
    assert age_multiplier(27) == 1.0
    assert age_multiplier(19) < age_multiplier(27)
    assert age_multiplier(37) < age_multiplier(27)


def test_player_value_score_higher_for_better_stats():
    assert player_value_score(YOUNG_STAR) > player_value_score(AGING_VET)


def test_contract_efficiency_scales_inversely_with_salary():
    cheap = {**YOUNG_STAR, "salary": 5_000_000}
    expensive = {**YOUNG_STAR, "salary": 40_000_000}
    assert contract_efficiency(cheap) > contract_efficiency(expensive)


def test_project_post_trade_value_declines_for_aging_player():
    projected = project_post_trade_value(AGING_VET, years_out=3)
    assert projected <= player_value_score(AGING_VET)


def test_analyze_team_needs_counts_positions():
    roster = [YOUNG_STAR, AGING_VET]
    profile = analyze_team_needs("TEST", roster)
    assert profile.position_counts == {"SG": 1, "C": 1}
    assert profile.avg_age == (26 + 37) / 2


def test_trade_impact_summary_net_value():
    summary = trade_impact_summary(players_in=[YOUNG_STAR], players_out=[AGING_VET])
    assert summary["value_acquired"] == player_value_score(YOUNG_STAR)
    assert summary["value_surrendered"] == player_value_score(AGING_VET)
    assert summary["net_value_score"] == round(
        player_value_score(YOUNG_STAR) - player_value_score(AGING_VET), 1
    )
