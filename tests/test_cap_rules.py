from src.tools.cap_rules import (
    CapStatus,
    check_trade_legality,
    suggest_balancing_move,
    team_cap_status,
)

CAP_RULES = {
    "season": "2025-26",
    "salary_cap": 154_647_000,
    "luxury_tax_line": 187_895_000,
    "first_apron": 195_945_000,
    "second_apron": 207_824_000,
}


def test_team_cap_status_under_cap():
    assert team_cap_status(100_000_000, CAP_RULES) == CapStatus.UNDER_CAP


def test_team_cap_status_second_apron():
    assert team_cap_status(210_000_000, CAP_RULES) == CapStatus.SECOND_APRON


def test_under_cap_team_can_absorb_up_to_cap_room():
    # Payroll well under cap: plenty of room to take back extra salary.
    result = check_trade_legality(
        team_abbr="TEST",
        current_payroll=100_000_000,
        outgoing_salary=5_000_000,
        incoming_salary=50_000_000,
        outgoing_player_count=1,
        cap_rules=CAP_RULES,
    )
    assert result.legal
    assert result.cap_status == CapStatus.UNDER_CAP


def test_taxpayer_salary_matching_band_enforced():
    # Payroll over the tax line -> outgoing $10M can take back at most
    # 10M * 1.75 + 250k = 17.75M
    result = check_trade_legality(
        team_abbr="TEST",
        current_payroll=190_000_000,
        outgoing_salary=10_000_000,
        incoming_salary=20_000_000,
        outgoing_player_count=1,
        cap_rules=CAP_RULES,
    )
    assert not result.legal
    assert result.max_incoming_allowed == 17_750_000
    assert result.violations


def test_second_apron_team_cannot_take_back_more_salary():
    result = check_trade_legality(
        team_abbr="TEST",
        current_payroll=210_000_000,
        outgoing_salary=10_000_000,
        incoming_salary=12_000_000,
        outgoing_player_count=1,
        cap_rules=CAP_RULES,
    )
    assert not result.legal
    assert result.cap_status == CapStatus.SECOND_APRON


def test_second_apron_team_cannot_aggregate_salaries():
    result = check_trade_legality(
        team_abbr="TEST",
        current_payroll=210_000_000,
        outgoing_salary=10_000_000,
        incoming_salary=9_000_000,
        outgoing_player_count=2,
        cap_rules=CAP_RULES,
    )
    assert not result.legal
    assert any("aggregate" in v for v in result.violations)


def test_suggest_balancing_move_returns_none_for_legal_trade():
    result = check_trade_legality(
        team_abbr="TEST",
        current_payroll=100_000_000,
        outgoing_salary=10_000_000,
        incoming_salary=10_000_000,
        outgoing_player_count=1,
        cap_rules=CAP_RULES,
    )
    assert suggest_balancing_move(result) is None


def test_suggest_balancing_move_flags_gap_for_illegal_trade():
    result = check_trade_legality(
        team_abbr="TEST",
        current_payroll=210_000_000,
        outgoing_salary=10_000_000,
        incoming_salary=15_000_000,
        outgoing_player_count=1,
        cap_rules=CAP_RULES,
    )
    suggestion = suggest_balancing_move(result)
    assert suggestion is not None
    assert "TEST" in suggestion
