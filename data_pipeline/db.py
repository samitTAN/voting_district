"""SQLite schema and writer for the reference data the rest of the app reads.
Loading is idempotent per county — re-running the pipeline for a county
replaces that county's rows rather than appending duplicates.
"""

import json
import sqlite3

from data_pipeline.build import VillageRecord

SCHEMA = """
CREATE TABLE IF NOT EXISTS counties (
    name TEXT PRIMARY KEY,
    seat_count INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS villages (
    id TEXT PRIMARY KEY,
    county TEXT NOT NULL REFERENCES counties(name),
    township TEXT NOT NULL,
    name TEXT NOT NULL,
    population INTEGER NOT NULL,
    official_district INTEGER NOT NULL,
    coordinates TEXT NOT NULL,
    neighbor_ids TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_villages_county ON villages(county);
"""


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA)


def write_county(
    conn: sqlite3.Connection,
    county_name: str,
    seat_count: int,
    records: list[VillageRecord],
) -> None:
    conn.execute("DELETE FROM villages WHERE county = ?", (county_name,))
    conn.execute(
        "INSERT INTO counties (name, seat_count) VALUES (?, ?) "
        "ON CONFLICT(name) DO UPDATE SET seat_count = excluded.seat_count",
        (county_name, seat_count),
    )
    conn.executemany(
        """
        INSERT INTO villages (id, county, township, name, population, official_district, coordinates, neighbor_ids)
        VALUES (:id, :county, :township, :name, :population, :official_district, :coordinates, :neighbor_ids)
        """,
        [
            {
                "id": r.id,
                "county": r.county,
                "township": r.township,
                "name": r.name,
                "population": r.population,
                "official_district": r.official_district,
                "coordinates": json.dumps(r.coordinates),
                "neighbor_ids": json.dumps(r.neighbor_ids),
            }
            for r in records
        ],
    )
    conn.commit()
