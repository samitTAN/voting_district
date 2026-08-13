"""Read-only query helpers over the reference-data schema (see
data_pipeline/db.py for the schema and writer) for the drawing-page API —
no writes, no dependency on the pipeline itself."""

import json
import sqlite3


def get_counties(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute("SELECT name, seat_count FROM counties ORDER BY name").fetchall()
    return [{"name": row["name"], "seat_count": row["seat_count"]} for row in rows]


def get_seat_count(conn: sqlite3.Connection, county_name: str) -> int | None:
    row = conn.execute("SELECT seat_count FROM counties WHERE name = ?", (county_name,)).fetchone()
    return row["seat_count"] if row else None


def get_villages(conn: sqlite3.Connection, county_name: str) -> list[dict]:
    rows = conn.execute(
        """
        SELECT id, township, name, population, official_district, coordinates, neighbor_ids
        FROM villages WHERE county = ? ORDER BY id
        """,
        (county_name,),
    ).fetchall()
    return [
        {
            "id": row["id"],
            "township": row["township"],
            "name": row["name"],
            "population": row["population"],
            "official_district": row["official_district"],
            "coordinates": json.loads(row["coordinates"]),
            "neighbor_ids": json.loads(row["neighbor_ids"]),
        }
        for row in rows
    ]
