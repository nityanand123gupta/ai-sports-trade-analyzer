"""Simplified NBA CBA salary-matching / apron rules engine.

This models the *shape* of the real 2023 Collective Bargaining Agreement
rules (cap, tax, first apron, second apron, salary-matching bands) closely
enough for realistic trade-legality simulation. It is intentionally
simplified for an educational project and should not be relied on for
actual front-office decisions -- always confirm against the official CBA.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class CapStatus(str, Enum):
    UNDER_CAP = "Under the Salary Cap"
    OVER_CAP_UNDER_TAX = "Over the Cap, Under the Luxury Tax"
    TAXPAYER = "Luxury Taxpayer"
    FIRST_APRON = "Over the First Apron"
    SECOND_APRON = "Over the Second Apron"


@dataclass
class TradeLegalityResult:
    legal: bool
    team_abbr: str
    cap_status: CapStatus
    outgoing_salary: int
    incoming_salary: int
    max_incoming_allowed: int
    violations: list[str] = field(default_factory=list)


def team_cap_status(payroll: int, cap_rules: dict) -> CapStatus:
    if payroll < cap_rules["salary_cap"]:
        return CapStatus.UNDER_CAP
    if payroll < cap_rules["luxury_tax_line"]:
        return CapStatus.OVER_CAP_UNDER_TAX
    if payroll < cap_rules["first_apron"]:
        return CapStatus.TAXPAYER
    if payroll < cap_rules["second_apron"]:
        return CapStatus.FIRST_APRON
    return CapStatus.SECOND_APRON


def _salary_matching_cap(outgoing_salary: int, cap_rules: dict) -> int:
    """Max salary a team below the first apron may take back for a given
    outgoing salary, per the 2023 CBA bands."""
    if outgoing_salary <= 7_500_000:
        return int(outgoing_salary * 2.00 + 250_000)
    if outgoing_salary <= 29_000_000:
        return int(outgoing_salary * 1.75 + 250_000)
    return int(outgoing_salary * 1.25 + 250_000)


def check_trade_legality(
    team_abbr: str,
    current_payroll: int,
    outgoing_salary: int,
    incoming_salary: int,
    outgoing_player_count: int,
    cap_rules: dict,
) -> TradeLegalityResult:
    """Validate one side of a trade against simplified CBA salary-matching
    and hard-cap-apron rules.

    outgoing_player_count > 1 means the team is *aggregating* multiple
    players' salaries into the trade, which is restricted for apron teams.
    """
    violations: list[str] = []
    status = team_cap_status(current_payroll, cap_rules)

    if status == CapStatus.UNDER_CAP:
        cap_room = cap_rules["salary_cap"] - current_payroll
        max_incoming = max(cap_room, 0) + outgoing_salary
        if incoming_salary > max_incoming:
            violations.append(
                f"Incoming salary ${incoming_salary:,} exceeds available cap room "
                f"(${cap_room:,}) plus outgoing salary (${outgoing_salary:,})."
            )
    elif status in (CapStatus.OVER_CAP_UNDER_TAX, CapStatus.TAXPAYER):
        max_incoming = _salary_matching_cap(outgoing_salary, cap_rules)
        if incoming_salary > max_incoming:
            violations.append(
                f"Incoming salary ${incoming_salary:,} exceeds the CBA salary-matching "
                f"limit of ${max_incoming:,} for ${outgoing_salary:,} outgoing."
            )
    elif status == CapStatus.FIRST_APRON:
        max_incoming = outgoing_salary + 250_000
        if incoming_salary > max_incoming:
            violations.append(
                f"First-apron team cannot take back more than 100% of outgoing salary "
                f"+ $250,000. Incoming ${incoming_salary:,} > allowed ${max_incoming:,}."
            )
        if outgoing_player_count > 1:
            violations.append(
                "First-apron teams cannot aggregate multiple outgoing players' "
                "salaries in a single trade."
            )
    else:  # SECOND_APRON
        max_incoming = outgoing_salary  # cannot even add the $250k buffer
        if incoming_salary > max_incoming:
            violations.append(
                f"Second-apron team cannot take back MORE salary than it sends out. "
                f"Incoming ${incoming_salary:,} > outgoing ${outgoing_salary:,}."
            )
        if outgoing_player_count > 1:
            violations.append(
                "Second-apron teams cannot aggregate multiple outgoing players' "
                "salaries in a single trade."
            )
    return TradeLegalityResult(
        legal=len(violations) == 0,
        team_abbr=team_abbr,
        cap_status=status,
        outgoing_salary=outgoing_salary,
        incoming_salary=incoming_salary,
        max_incoming_allowed=max_incoming,
        violations=violations,
    )


def suggest_balancing_move(result: TradeLegalityResult) -> str | None:
    """When a trade is illegal purely on salary-matching grounds, suggest a
    generic fix (used by the Cap Specialist -> GM feedback loop)."""
    if result.legal:
        return None
    gap = result.incoming_salary - result.max_incoming_allowed
    if gap <= 0:
        return None
    return (
        f"{result.team_abbr} needs to shed roughly ${gap:,} more in outgoing "
        f"salary (e.g. attach a smaller salaried player or ask the other side "
        f"to include less salary) to bring this trade within CBA limits."
    )
