"""Thin network I/O — fetches the three upstream sources the pipeline joins,
caching each to data/raw/ so re-runs (and tests) don't re-hit the network
every time. No transformation logic lives here; see build.py and
topojson.py for that.

Sources:
- Village boundary topology: g0v/twgeojson (community conversion of NLSC's
  official 村里界圖, itself distributed as SHP on data.gov.tw).
- Official village -> legislative-district correspondence: kiang/db.cec.gov.tw,
  built from CEC's own raw election data.
- Village population: 內政部戶政司 via the ris.gov.tw open-data API.
"""

import json
from pathlib import Path

import requests

RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"

VILLAGE_TOPOLOGY_URL = "https://raw.githubusercontent.com/g0v/twgeojson/master/json/twVillage1982.topo.json"
OFFICIAL_DISTRICTS_URL = "https://raw.githubusercontent.com/kiang/db.cec.gov.tw/master/data/ly/2024/zones.json"
POPULATION_API = "https://www.ris.gov.tw/rs-opendata/api/v1/datastore/ODRP014/{yyymm}"


def _read_cache(cache_file: Path, *, force_refresh: bool):
    if cache_file.exists() and not force_refresh:
        return json.loads(cache_file.read_text())
    return None


def _write_cache(cache_file: Path, data) -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    cache_file.write_text(json.dumps(data, ensure_ascii=False))


def _cached_get_json(url: str, cache_file: Path, *, force_refresh: bool = False) -> dict:
    cached = _read_cache(cache_file, force_refresh=force_refresh)
    if cached is not None:
        return cached
    response = requests.get(url, timeout=60)
    response.raise_for_status()
    data = response.json()
    _write_cache(cache_file, data)
    return data


def fetch_village_topology(*, force_refresh: bool = False) -> dict:
    return _cached_get_json(
        VILLAGE_TOPOLOGY_URL, RAW_DIR / "twVillage1982.topo.json", force_refresh=force_refresh
    )


def fetch_official_districts(*, force_refresh: bool = False) -> dict:
    return _cached_get_json(
        OFFICIAL_DISTRICTS_URL, RAW_DIR / "official_districts_2024.json", force_refresh=force_refresh
    )


def fetch_population(yyymm: str, *, force_refresh: bool = False) -> list[dict]:
    """The ris.gov.tw API paginates nationwide village population figures;
    this walks every page and caches the concatenated result."""
    cache_file = RAW_DIR / f"population_{yyymm}.json"
    cached = _read_cache(cache_file, force_refresh=force_refresh)
    if cached is not None:
        return cached

    rows: list[dict] = []
    url = POPULATION_API.format(yyymm=yyymm)
    page = 1
    while True:
        response = requests.get(url, params={"page": page}, timeout=60)
        response.raise_for_status()
        payload = response.json()
        rows.extend(payload["responseData"])
        if page >= int(payload["totalPage"]):
            break
        page += 1

    _write_cache(cache_file, rows)
    return rows
