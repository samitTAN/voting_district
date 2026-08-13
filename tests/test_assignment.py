"""Fixture: 6 villages in a row (v1-v2-v3-v4-v5-v6, each adjacent only to its
immediate neighbors), split evenly into two townships (A: v1-v3, B: v4-v6),
population 1000 each — so two seats and a "district 1 = v1-v3, district 2 =
v4-v6" split is balanced, contiguous, and doesn't cross a township."""

from districting.assignment import Village, evaluate_assignment

VILLAGES = [
    Village(id="v1", township="A", population=1000, neighbor_ids=["v2"]),
    Village(id="v2", township="A", population=1000, neighbor_ids=["v1", "v3"]),
    Village(id="v3", township="A", population=1000, neighbor_ids=["v2", "v4"]),
    Village(id="v4", township="B", population=1000, neighbor_ids=["v3", "v5"]),
    Village(id="v5", township="B", population=1000, neighbor_ids=["v4", "v6"]),
    Village(id="v6", township="B", population=1000, neighbor_ids=["v5"]),
]

BALANCED_ASSIGNMENT = {"v1": 1, "v2": 1, "v3": 1, "v4": 2, "v5": 2, "v6": 2}


def test_fully_unassigned_plan_is_incomplete_with_no_warnings():
    result = evaluate_assignment(VILLAGES, {}, seat_count=2)

    assert result.is_complete is False
    # empty districts aren't warning-worthy — there's nothing to flag yet
    assert result.warnings == []
    assert [s.district for s in result.district_stats] == [1, 2]
    assert all(s.population == 0 for s in result.district_stats)
    assert all(s.contiguous for s in result.district_stats)


def test_fully_assigned_balanced_contiguous_plan_has_no_warnings():
    result = evaluate_assignment(VILLAGES, BALANCED_ASSIGNMENT, seat_count=2)

    assert result.is_complete is True
    assert result.warnings == []
    d1 = next(s for s in result.district_stats if s.district == 1)
    d2 = next(s for s in result.district_stats if s.district == 2)
    assert d1.population == 3000
    assert d2.population == 3000
    assert d1.deviation == 0
    assert d2.deviation == 0
    assert d1.contiguous is True
    assert d2.contiguous is True


def test_non_contiguous_district_raises_a_violation_warning():
    # district 1 gets v1 and v3 but not v2 — v1 and v3 aren't neighbors
    assignment = dict(BALANCED_ASSIGNMENT, v1=1, v2=2, v3=1)

    result = evaluate_assignment(VILLAGES, assignment, seat_count=2)

    d1 = next(s for s in result.district_stats if s.district == 1)
    assert d1.contiguous is False
    assert any(w.severity == "violation" for w in result.warnings)


def test_district_exceeding_deviation_threshold_raises_a_caution_warning():
    # district 1 gets all six villages (pop 6000), district 2 gets none —
    # county average per seat is 3000, so district 1 is +100% over
    assignment = {v.id: 1 for v in VILLAGES}

    result = evaluate_assignment(VILLAGES, assignment, seat_count=2)

    d1 = next(s for s in result.district_stats if s.district == 1)
    assert d1.deviation > 0.15
    caution = [w for w in result.warnings if w.severity == "caution"]
    assert any("15%" in w.message or "±15" in w.message for w in caution)
    assert any("中選會" in w.message for w in caution)
    assert not any("法律" in w.message and "非" not in w.message for w in caution)


def test_split_township_raises_a_caution_warning():
    # v1-v3 are township A; splitting them across two districts breaks
    # village/township integrity
    assignment = dict(BALANCED_ASSIGNMENT, v1=1, v2=2, v3=2)

    result = evaluate_assignment(VILLAGES, assignment, seat_count=2)

    cautions = [w for w in result.warnings if w.severity == "caution"]
    assert any("村里不分割" in w.message for w in cautions)


def test_partially_assigned_plan_is_incomplete_with_some_districts_empty():
    # v1-v3 (pop 3000) matches the county average exactly, so this partial
    # plan is warning-free even though it isn't finished
    assignment = {"v1": 1, "v2": 1, "v3": 1}

    result = evaluate_assignment(VILLAGES, assignment, seat_count=2)

    assert result.is_complete is False
    d2 = next(s for s in result.district_stats if s.district == 2)
    assert d2.population == 0
    assert d2.contiguous is True
    assert result.warnings == []
