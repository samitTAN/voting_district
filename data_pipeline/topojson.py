"""Minimal TopoJSON decoding — just enough to turn the arcs/geometries this
project consumes (Polygon / MultiPolygon village boundaries) into plain
coordinate lists, without pulling in a third-party topojson dependency.

Spec: https://github.com/topojson/topojson-specification
"""


def decode_arcs(topology: dict) -> list[list[tuple[float, float]]]:
    """Delta-decode every arc in a topojson Topology into absolute (x, y) points,
    applying the topology's quantization transform if present."""
    transform = topology.get("transform")
    raw_arcs = topology["arcs"]

    if transform is None:
        return [[tuple(point) for point in arc] for arc in raw_arcs]

    scale_x, scale_y = transform["scale"]
    translate_x, translate_y = transform["translate"]

    decoded_arcs = []
    for raw_arc in raw_arcs:
        x = y = 0
        points = []
        for dx, dy in raw_arc:
            x += dx
            y += dy
            points.append((x * scale_x + translate_x, y * scale_y + translate_y))
        decoded_arcs.append(points)
    return decoded_arcs


def resolve_ring(arc_indices: list[int], arcs: list[list[tuple[float, float]]]) -> list[tuple[float, float]]:
    """Concatenate the arcs referenced by a topojson ring into one coordinate
    ring. A negative index ~i (i.e. -i - 1) means "arc i, reversed"."""
    ring: list[tuple[float, float]] = []
    for index in arc_indices:
        if index < 0:
            arc = list(reversed(arcs[~index]))
        else:
            arc = arcs[index]
        if ring and ring[-1] == arc[0]:
            ring.extend(arc[1:])
        else:
            ring.extend(arc)
    return ring


def geometry_coordinates(geometry: dict, arcs: list[list[tuple[float, float]]]):
    """Resolve a topojson Polygon/MultiPolygon geometry's arc indices into
    GeoJSON-shaped coordinate nesting."""
    if geometry["type"] == "Polygon":
        return [resolve_ring(ring, arcs) for ring in geometry["arcs"]]
    if geometry["type"] == "MultiPolygon":
        return [
            [resolve_ring(ring, arcs) for ring in polygon]
            for polygon in geometry["arcs"]
        ]
    raise ValueError(f"unsupported geometry type: {geometry['type']!r}")
