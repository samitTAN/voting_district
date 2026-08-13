import sqlite3

import pytest
from fastapi.testclient import TestClient

from app.main import app, get_connection
from data_pipeline.build import VillageRecord
from data_pipeline.db import init_db, write_county

# A 3-village strip (A-B-C, each adjacent only to its immediate neighbor) in
# one county, seat_count=1 — enough to exercise villages/geojson/evaluate
# without needing the real seeded reference.db.
VILLAGES = [
    VillageRecord(
        id="A", county="苗栗縣", township="苗栗市", name="中山里", population=1000,
        official_district=1,
        coordinates=[[[120.0, 24.0], [120.1, 24.0], [120.1, 24.1], [120.0, 24.0]]],
        neighbor_ids=["B"],
    ),
    VillageRecord(
        id="B", county="苗栗縣", township="苗栗市", name="中央里", population=1000,
        official_district=1,
        coordinates=[[[120.1, 24.0], [120.2, 24.0], [120.2, 24.1], [120.1, 24.0]]],
        neighbor_ids=["A", "C"],
    ),
    VillageRecord(
        id="C", county="苗栗縣", township="苗栗市", name="中興里", population=1000,
        official_district=1,
        coordinates=[[[120.2, 24.0], [120.3, 24.0], [120.3, 24.1], [120.2, 24.0]]],
        neighbor_ids=["B"],
    ),
]


@pytest.fixture
def client():
    # check_same_thread=False: TestClient runs sync path operations in a
    # worker thread, but this one fixture connection is shared across the
    # whole test's requests — real requests each open their own connection
    # in get_connection, so this constraint doesn't apply there.
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    init_db(conn)
    write_county(conn, "苗栗縣", 1, VILLAGES)

    def override_connection():
        yield conn

    app.dependency_overrides[get_connection] = override_connection
    yield TestClient(app)
    app.dependency_overrides.clear()
    conn.close()


def test_list_counties_returns_seeded_counties(client):
    response = client.get("/api/counties")

    assert response.status_code == 200
    assert response.json() == [{"name": "苗栗縣", "seat_count": 1}]


def test_list_villages_returns_a_geojson_feature_collection(client):
    response = client.get("/api/counties/苗栗縣/villages")

    assert response.status_code == 200
    body = response.json()
    assert body["type"] == "FeatureCollection"
    assert [f["properties"]["id"] for f in body["features"]] == ["A", "B", "C"]
    a = body["features"][0]
    assert a["geometry"] == {"type": "Polygon", "coordinates": VILLAGES[0].coordinates}
    assert a["properties"]["name"] == "中山里"
    assert a["properties"]["population"] == 1000


def test_list_villages_404s_for_an_unknown_county(client):
    response = client.get("/api/counties/不存在縣/villages")

    assert response.status_code == 404


def test_evaluate_returns_district_stats_warnings_and_completeness(client):
    response = client.post(
        "/api/counties/苗栗縣/evaluate",
        json={"assignment": {"A": 1, "B": 1, "C": 1}},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["is_complete"] is True
    assert body["warnings"] == []
    assert body["district_stats"] == [
        {"district": 1, "population": 3000, "deviation": 0.0, "contiguous": True, "within_threshold": True}
    ]


def test_evaluate_flags_a_non_contiguous_district(client):
    response = client.post(
        "/api/counties/苗栗縣/evaluate",
        json={"assignment": {"A": 1, "C": 1}},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["is_complete"] is False
    assert any(w["severity"] == "violation" for w in body["warnings"])


def test_evaluate_404s_for_an_unknown_county(client):
    response = client.post(
        "/api/counties/不存在縣/evaluate",
        json={"assignment": {}},
    )

    assert response.status_code == 404
