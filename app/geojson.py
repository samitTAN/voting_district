"""The reference-data schema stores each village's boundary as a plain
coordinate-ring list with no explicit Polygon/MultiPolygon type column (see
data_pipeline/topojson.py's geometry_coordinates), so the GeoJSON `type` has
to be recovered from how deeply the list nests: a Polygon's rings are
[ring][point][lon, lat] (3 levels); a MultiPolygon adds one more level for
the list of polygons.
"""


def to_geojson_geometry(coordinates: list) -> dict:
    return {"type": "MultiPolygon" if _depth(coordinates) == 4 else "Polygon", "coordinates": coordinates}


def _depth(value: list) -> int:
    if not isinstance(value, list) or not value:
        return 0
    return 1 + _depth(value[0])
