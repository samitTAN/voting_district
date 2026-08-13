"""Geographic adjacency between villages, derived from topojson's shared-arc
encoding rather than geometric intersection — two villages are neighbors iff
their boundary rings reference the same arc (regardless of direction)."""

from collections import defaultdict
from typing import Iterable


def _flatten_arc_indices(nested) -> Iterable[int]:
    """Arc-index structures nest one level deeper for MultiPolygon than
    Polygon; recurse until we hit the actual (possibly negative) integers."""
    for item in nested:
        if isinstance(item, int):
            yield item
        else:
            yield from _flatten_arc_indices(item)


def neighbors_from_shared_arcs(villages: dict[str, list]) -> dict[str, set[str]]:
    """villages: village id -> its geometry's raw (nested) arc-index structure,
    as found verbatim in a topojson geometry's `arcs` field.

    Returns village id -> set of neighbor village ids (sharing at least one arc).
    """
    arc_owners: dict[int, set[str]] = defaultdict(set)
    for village_id, arc_structure in villages.items():
        for index in _flatten_arc_indices(arc_structure):
            absolute_index = index if index >= 0 else ~index
            arc_owners[absolute_index].add(village_id)

    neighbors: dict[str, set[str]] = {village_id: set() for village_id in villages}
    for owners in arc_owners.values():
        if len(owners) < 2:
            continue
        for village_id in owners:
            neighbors[village_id].update(owners - {village_id})

    return neighbors
