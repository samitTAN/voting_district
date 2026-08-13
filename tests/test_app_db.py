import sqlite3

import pytest

from app.db import get_counties, get_seat_count, get_villages
from data_pipeline.build import VillageRecord
from data_pipeline.db import init_db, write_county


@pytest.fixture
def conn():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    init_db(connection)
    write_county(
        connection,
        "苗栗縣",
        2,
        [
            VillageRecord(
                id="A",
                county="苗栗縣",
                township="苗栗市",
                name="中山里",
                population=5000,
                official_district=1,
                coordinates=[[[120.0, 24.0], [120.1, 24.0], [120.1, 24.1], [120.0, 24.0]]],
                neighbor_ids=["B"],
            ),
            VillageRecord(
                id="B",
                county="苗栗縣",
                township="苗栗市",
                name="中央里",
                population=3000,
                official_district=1,
                coordinates=[[[120.1, 24.0], [120.2, 24.0], [120.2, 24.1], [120.1, 24.0]]],
                neighbor_ids=["A"],
            ),
        ],
    )
    write_county(connection, "雲林縣", 3, [])
    return connection


def test_get_counties_lists_every_seeded_county_with_its_seat_count(conn):
    assert get_counties(conn) == [
        {"name": "苗栗縣", "seat_count": 2},
        {"name": "雲林縣", "seat_count": 3},
    ]


def test_get_seat_count_returns_the_countys_seat_count(conn):
    assert get_seat_count(conn, "苗栗縣") == 2


def test_get_seat_count_returns_none_for_an_unknown_county(conn):
    assert get_seat_count(conn, "不存在縣") is None


def test_get_villages_returns_only_the_requested_countys_villages_decoded(conn):
    villages = get_villages(conn, "苗栗縣")

    assert [v["id"] for v in villages] == ["A", "B"]
    a = villages[0]
    assert a["township"] == "苗栗市"
    assert a["name"] == "中山里"
    assert a["population"] == 5000
    assert a["official_district"] == 1
    assert a["coordinates"] == [[[120.0, 24.0], [120.1, 24.0], [120.1, 24.1], [120.0, 24.0]]]
    assert a["neighbor_ids"] == ["B"]


def test_get_villages_returns_empty_list_for_a_county_with_no_villages(conn):
    assert get_villages(conn, "雲林縣") == []
