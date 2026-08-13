from app.geojson import to_geojson_geometry


def test_three_levels_of_nesting_is_a_polygon():
    coordinates = [[[120.7, 24.4], [120.8, 24.4], [120.8, 24.5], [120.7, 24.4]]]

    result = to_geojson_geometry(coordinates)

    assert result == {"type": "Polygon", "coordinates": coordinates}


def test_four_levels_of_nesting_is_a_multipolygon():
    coordinates = [
        [[[120.7, 24.4], [120.8, 24.4], [120.8, 24.5], [120.7, 24.4]]],
        [[[121.0, 25.0], [121.1, 25.0], [121.1, 25.1], [121.0, 25.0]]],
    ]

    result = to_geojson_geometry(coordinates)

    assert result == {"type": "MultiPolygon", "coordinates": coordinates}
