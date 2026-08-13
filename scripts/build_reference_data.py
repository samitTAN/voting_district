#!/usr/bin/env python3
"""Build the SQLite reference data (village geometry, population, official
district assignment) that the app reads for one county.

    python scripts/build_reference_data.py --county 苗栗縣 --yyymm 11406

Re-run any time to refresh a county (e.g. with a newer --yyymm population
snapshot); it replaces that county's rows rather than duplicating them.
"""

import argparse
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from data_pipeline import sources
from data_pipeline.topojson import decode_arcs, geometry_coordinates
from data_pipeline.build import townships_for_county, index_population, build_villages, MissingJoinError
from data_pipeline.db import init_db, write_county

DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "data" / "reference.db"


def run(county: str, yyymm: str, db_path: Path, *, force_refresh: bool = False) -> None:
    print(f"Fetching village boundary topology ...")
    topology = sources.fetch_village_topology(force_refresh=force_refresh)
    arcs = decode_arcs(topology)
    all_village_geometries = topology["objects"]["layer1"]["geometries"]
    county_geometries = [
        feature for feature in all_village_geometries
        if feature["properties"]["COUNTYNAME"] == county
    ]
    if not county_geometries:
        # NOTE: the boundary file's COUNTYNAME values predate the 2010/2014
        # municipality mergers — it has no 新北市/桃園市 and no post-merger
        # 台中市/台南市/高雄市, only their pre-merger 縣/市 halves. A county
        # name that doesn't match is most likely one of those five, not a typo.
        raise SystemExit(
            f"No villages found for county {county!r} in the boundary topology. "
            f"Note: this data source uses pre-2010/2014-merger county names — "
            f"新北市, 桃園市, and merged 台中/台南/高雄市 are not available from it."
        )

    print(f"Fetching official district correspondence ...")
    official_districts = sources.fetch_official_districts(force_refresh=force_refresh)
    district_map = townships_for_county(official_districts, county)
    seat_count = len(set(district_map.values()))

    print(f"Fetching population snapshot {yyymm} (paginated, nationwide) ...")
    population_rows = sources.fetch_population(yyymm, force_refresh=force_refresh)
    population_map = index_population(population_rows, county)

    prepared = []
    for feature in county_geometries:
        props = feature["properties"]
        has_geometry = bool(feature.get("arcs"))
        prepared.append(
            {
                "id": props["VILLAGEID"],
                "township": props["TOWNNAME"],
                "name": props["VILLAGENAM"],
                "coordinates": geometry_coordinates(feature, arcs) if has_geometry else None,
                "raw_arcs": feature.get("arcs"),
            }
        )

    try:
        records, skipped = build_villages(county, prepared, district_map, population_map)
    except MissingJoinError as exc:
        raise SystemExit(f"Data join failed: {exc}")

    if skipped:
        print(f"Skipped {len(skipped)} village(s) with no source geometry:")
        for s in skipped:
            print(f"  - {s['id']}: {s['reason']}")

    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    init_db(conn)
    write_county(conn, county, seat_count, records)
    conn.close()

    print(f"Wrote {len(records)} villages for {county} ({seat_count} districts) to {db_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--county", required=True, help="e.g. 苗栗縣")
    parser.add_argument("--yyymm", required=True, help="ROC year+month for the population snapshot, e.g. 11406")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB_PATH, help="output SQLite path")
    parser.add_argument("--force-refresh", action="store_true", help="bypass the local data/raw/ cache")
    args = parser.parse_args()

    run(args.county, args.yyymm, args.db, force_refresh=args.force_refresh)


if __name__ == "__main__":
    main()
