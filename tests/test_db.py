import json
import sqlite3

from data_pipeline.build import VillageRecord
from data_pipeline.db import init_db, write_county


def _connect():
    conn = sqlite3.connect(":memory:")
    init_db(conn)
    return conn


def _record(id_, township, name, population, district, neighbor_ids, county="苗栗縣"):
    return VillageRecord(
        id=id_,
        county=county,
        township=township,
        name=name,
        population=population,
        official_district=district,
        coordinates=[[(0, 0), (1, 0), (1, 1), (0, 0)]],
        neighbor_ids=neighbor_ids,
    )


def test_write_county_persists_villages_and_seat_count():
    conn = _connect()
    records = [
        _record("A", "苗栗市", "中山里", 5000, 2, ["B"]),
        _record("B", "頭份市", "中央里", 3000, 2, ["A"]),
    ]

    write_county(conn, "苗栗縣", seat_count=2, records=records)

    county_row = conn.execute("SELECT name, seat_count FROM counties WHERE name = ?", ("苗栗縣",)).fetchone()
    assert county_row == ("苗栗縣", 2)

    rows = conn.execute(
        "SELECT id, township, name, population, official_district, coordinates, neighbor_ids "
        "FROM villages WHERE county = ? ORDER BY id",
        ("苗栗縣",),
    ).fetchall()
    assert len(rows) == 2
    assert rows[0][0:5] == ("A", "苗栗市", "中山里", 5000, 2)
    assert json.loads(rows[0][6]) == ["B"]


def test_rerunning_write_county_replaces_rather_than_duplicates():
    conn = _connect()
    write_county(conn, "苗栗縣", seat_count=2, records=[_record("A", "苗栗市", "中山里", 5000, 2, [])])
    write_county(conn, "苗栗縣", seat_count=2, records=[_record("A", "苗栗市", "中山里", 5100, 2, [])])

    rows = conn.execute("SELECT population FROM villages WHERE county = ?", ("苗栗縣",)).fetchall()
    assert rows == [(5100,)]


def test_writing_a_second_county_does_not_touch_the_first():
    conn = _connect()
    write_county(conn, "苗栗縣", seat_count=2, records=[_record("A", "苗栗市", "中山里", 5000, 2, [])])
    write_county(conn, "雲林縣", seat_count=2, records=[_record("Y", "斗六市", "延平里", 8000, 1, [], county="雲林縣")])

    counties = conn.execute("SELECT name FROM counties ORDER BY name").fetchall()
    assert counties == [("苗栗縣",), ("雲林縣",)]
    miaoli_villages = conn.execute("SELECT id FROM villages WHERE county = ?", ("苗栗縣",)).fetchall()
    assert miaoli_villages == [("A",)]
