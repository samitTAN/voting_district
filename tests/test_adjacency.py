"""Villages that share a topojson arc are geographic neighbors — this is how
topojson encodes shared borders, so adjacency falls out of index bookkeeping
alone, with no need for geometric intersection tests."""

from data_pipeline.adjacency import neighbors_from_shared_arcs


def test_two_villages_sharing_an_arc_are_neighbors():
    # B references arc 1 reversed (~1 == -2); that's still arc 1, so A and B share it.
    villages = {
        "A": [[0, 1]],
        "B": [[-2, 2]],
    }

    result = neighbors_from_shared_arcs(villages)

    assert result == {"A": {"B"}, "B": {"A"}}


def test_villages_with_no_shared_arc_are_not_neighbors():
    villages = {
        "A": [[0, 1]],
        "C": [[3, 4]],
    }

    result = neighbors_from_shared_arcs(villages)

    assert result == {"A": set(), "C": set()}


def test_three_villages_in_a_row_only_touch_immediate_neighbors():
    # A-B share arc 1, B-C share arc 2; A and C never touch.
    villages = {
        "A": [[0, 1]],
        "B": [[-2, 2]],
        "C": [[-3, 4]],
    }

    result = neighbors_from_shared_arcs(villages)

    assert result == {"A": {"B"}, "B": {"A", "C"}, "C": {"B"}}


def test_multipolygon_rings_are_flattened_before_matching():
    # nested ring lists (multipolygon-shaped) should still be scanned for arcs
    villages = {
        "A": [[[0, 1]], [[5]]],
        "B": [[[-2, 6]]],
    }

    result = neighbors_from_shared_arcs(villages)

    assert result == {"A": {"B"}, "B": {"A"}}
