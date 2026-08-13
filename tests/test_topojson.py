"""Tests for the topojson arc-decoding helpers, using tiny hand-built topologies
rather than the real (2MB) twVillage1982 file, so these run instantly and
pin down the decoding logic in isolation.
"""

from data_pipeline.topojson import decode_arcs, resolve_ring, geometry_coordinates


def test_decode_arcs_applies_transform_and_delta_decoding():
    # A single arc with two points: start at translate, then one delta step.
    # Real topojson quantizes coordinates and delta-encodes them; the first
    # point of each arc is absolute (post-scale), subsequent points are deltas.
    topology = {
        "transform": {"scale": [1, 1], "translate": [100, 200]},
        "arcs": [
            [[0, 0], [1, 2], [3, -1]],
        ],
    }

    arcs = decode_arcs(topology)

    assert arcs == [
        [
            (100, 200),  # translate + (0,0)
            (101, 202),  # + delta (1,2)
            (104, 201),  # + delta (3,-1)
        ]
    ]


def test_resolve_ring_concatenates_forward_arcs_without_duplicating_join_points():
    arcs = [
        [(0, 0), (1, 0)],
        [(1, 0), (1, 1)],
    ]

    ring = resolve_ring([0, 1], arcs)

    # arc 1's first point (1,0) duplicates arc 0's last point — topojson
    # rings drop that duplicate when concatenating.
    assert ring == [(0, 0), (1, 0), (1, 1)]


def test_resolve_ring_reverses_negative_indices():
    arcs = [
        [(0, 0), (1, 0)],
        [(1, 1), (1, 0)],
    ]

    # ~1 == -2 refers to arc 1, reversed: [(1, 0), (1, 1)]
    ring = resolve_ring([0, -2], arcs)

    assert ring == [(0, 0), (1, 0), (1, 1)]


def test_geometry_coordinates_for_polygon():
    arcs = [
        [(0, 0), (1, 0)],
        [(1, 0), (1, 1)],
        [(1, 1), (0, 1)],
        [(0, 1), (0, 0)],
    ]
    geometry = {"type": "Polygon", "arcs": [[0, 1, 2, 3]]}

    coords = geometry_coordinates(geometry, arcs)

    assert coords == [[(0, 0), (1, 0), (1, 1), (0, 1), (0, 0)]]


def test_geometry_coordinates_for_multipolygon():
    arcs = [
        [(0, 0), (1, 0), (1, 1), (0, 0)],
        [(5, 5), (6, 5), (6, 6), (5, 5)],
    ]
    geometry = {"type": "MultiPolygon", "arcs": [[[0]], [[1]]]}

    coords = geometry_coordinates(geometry, arcs)

    assert coords == [
        [[(0, 0), (1, 0), (1, 1), (0, 0)]],
        [[(5, 5), (6, 5), (6, 6), (5, 5)]],
    ]
