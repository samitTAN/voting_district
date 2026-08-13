"""Pure evaluation of a village-to-district assignment: population balance,
geographic contiguity, and completeness. This is the v0 spec's single test
seam for the districting domain logic — no UI, HTTP, or database dependency,
so a future frontend/backend can both call it directly.

Ported from the throwaway prototype at
prototype/village-assignment-interaction (issue #6).
"""

from dataclasses import dataclass
from typing import Literal

Severity = Literal["violation", "caution"]

# CEC's 2005 redistricting-committee principle (《第7屆立法委員直轄市縣市選舉區
# 劃分原則》) for population balance across a county's districts. Historical
# guidance, not codified law, and not formally re-adopted for the current
# redistricting cycle — warning text must keep framing it that way.
DEVIATION_THRESHOLD = 0.15


@dataclass
class Village:
    id: str
    township: str
    population: int
    neighbor_ids: list[str]


@dataclass
class DistrictStats:
    district: int
    population: int
    deviation: float
    contiguous: bool


@dataclass
class AssignmentWarning:
    severity: Severity
    message: str


@dataclass
class AssignmentResult:
    district_stats: list[DistrictStats]
    warnings: list[AssignmentWarning]
    is_complete: bool


def evaluate_assignment(
    villages: list[Village],
    assignment: dict[str, int | None],
    seat_count: int,
) -> AssignmentResult:
    """assignment maps village id -> district number (1..seat_count), or
    None/absent for not-yet-assigned. district_stats always has one entry
    per district 1..seat_count, even if empty."""
    # The county's target-per-district population — total population is
    # fixed regardless of how much of the plan is assigned yet, so this is
    # stable across an in-progress plan rather than drifting as villages
    # get assigned.
    average_population = sum(v.population for v in villages) / seat_count

    district_stats: list[DistrictStats] = []
    warnings: list[AssignmentWarning] = []
    for district in range(1, seat_count + 1):
        members = [v for v in villages if assignment.get(v.id) == district]
        population = sum(v.population for v in members)
        deviation = (
            (population - average_population) / average_population if average_population else 0.0
        )
        contiguous = _is_contiguous(members)
        district_stats.append(
            DistrictStats(
                district=district, population=population, deviation=deviation, contiguous=contiguous
            )
        )

        if not members:
            continue
        if not contiguous:
            warnings.append(
                AssignmentWarning("violation", f"第{district}選區目前指派的村里不相鄰，地理不連續。")
            )
        if abs(deviation) > DEVIATION_THRESHOLD:
            warnings.append(
                AssignmentWarning(
                    "caution",
                    f"第{district}選區人口{_format_percent(deviation)}，超出中選會 2005 年選區劃分原則的 "
                    "±15% 標準（非法律硬性規定）。",
                )
            )

    warnings.extend(_township_split_warnings(villages, assignment))

    is_complete = all(assignment.get(v.id) is not None for v in villages)

    return AssignmentResult(district_stats=district_stats, warnings=warnings, is_complete=is_complete)


def _is_contiguous(members: list[Village]) -> bool:
    if len(members) <= 1:
        return True
    member_ids = {v.id for v in members}
    by_id = {v.id: v for v in members}
    seen = {members[0].id}
    stack = [members[0]]
    while stack:
        current = stack.pop()
        for neighbor_id in current.neighbor_ids:
            if neighbor_id in member_ids and neighbor_id not in seen:
                seen.add(neighbor_id)
                stack.append(by_id[neighbor_id])
    return seen == member_ids


def _township_split_warnings(
    villages: list[Village], assignment: dict[str, int | None]
) -> list[AssignmentWarning]:
    districts_by_township: dict[str, list[int]] = {}
    for v in villages:
        district = assignment.get(v.id)
        if district is None:
            continue
        seen = districts_by_township.setdefault(v.township, [])
        if district not in seen:
            seen.append(district)

    return [
        AssignmentWarning(
            "caution", f"{township}的村里被分到 {len(districts)} 個不同選區，違反「村里不分割」慣例。"
        )
        for township, districts in districts_by_township.items()
        if len(districts) > 1
    ]


def _format_percent(deviation: float) -> str:
    percent = deviation * 100
    sign = "+" if percent >= 0 else ""
    return f"{sign}{percent:.1f}%"
