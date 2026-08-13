"""The drawing-page API: serves the reference-data pipeline's SQLite output
as JSON/GeoJSON, and runs the districting.assignment validation seam
server-side so the frontend never duplicates that logic in JS."""

import dataclasses
import os
import sqlite3
from pathlib import Path
from typing import Iterator

from fastapi import Depends, FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app.db import get_counties, get_seat_count, get_villages
from app.geojson import to_geojson_geometry
from districting.assignment import DEVIATION_THRESHOLD, Village, evaluate_assignment

DB_PATH = Path(os.environ.get("VOTING_DISTRICT_DB", "data/reference.db"))


def get_connection() -> Iterator[sqlite3.Connection]:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


class EvaluateRequest(BaseModel):
    assignment: dict[str, int | None]


app = FastAPI(title="自己的選區自己畫")


def _require_seat_count(conn: sqlite3.Connection, county: str) -> int:
    seat_count = get_seat_count(conn, county)
    if seat_count is None:
        raise HTTPException(status_code=404, detail=f"county not found: {county}")
    return seat_count


@app.get("/api/counties")
def list_counties(conn: sqlite3.Connection = Depends(get_connection)) -> list[dict]:
    return get_counties(conn)


@app.get("/api/counties/{county}/villages")
def list_villages(county: str, conn: sqlite3.Connection = Depends(get_connection)) -> dict:
    _require_seat_count(conn, county)
    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": to_geojson_geometry(row["coordinates"]),
                "properties": {
                    "id": row["id"],
                    "name": row["name"],
                    "township": row["township"],
                    "population": row["population"],
                    "official_district": row["official_district"],
                    "neighbor_ids": row["neighbor_ids"],
                },
            }
            for row in get_villages(conn, county)
        ],
    }


@app.post("/api/counties/{county}/evaluate")
def evaluate(
    county: str, request: EvaluateRequest, conn: sqlite3.Connection = Depends(get_connection)
) -> dict:
    seat_count = _require_seat_count(conn, county)

    villages = [
        Village(
            id=row["id"],
            township=row["township"],
            population=row["population"],
            neighbor_ids=row["neighbor_ids"],
        )
        for row in get_villages(conn, county)
    ]
    result = evaluate_assignment(villages, request.assignment, seat_count)
    return {
        # within_threshold travels with each stat so the frontend never
        # redefines ±15% itself — DEVIATION_THRESHOLD stays single-sourced
        # in districting.assignment.
        "district_stats": [
            dataclasses.asdict(s) | {"within_threshold": abs(s.deviation) <= DEVIATION_THRESHOLD}
            for s in result.district_stats
        ],
        "warnings": [dataclasses.asdict(w) for w in result.warnings],
        "is_complete": result.is_complete,
    }


app.mount("/", StaticFiles(directory=Path(__file__).parent / "static", html=True), name="static")
