"""Pure join logic: turn raw fetched sources (village geometry, official
district zones, population) into the village records the app's SQLite
reference data is built from. No network access here — see sources.py for
that; this module only transforms data already in memory, which is what
makes it cheap to unit test.
"""

from dataclasses import dataclass, field

from data_pipeline.adjacency import neighbors_from_shared_arcs

# Known administrative-status changes since the 1982-vintage boundary file's
# township names were assigned (鎮/鄉 upgraded to a county-administered 市).
# Extend this table as more mismatches turn up in other counties.
_TOWN_NAME_RENAMES = {
    "頭份鎮": "頭份市",
}

# The ris.gov.tw population dataset and the boundary-file village names
# disagree on a handful of traditional-character variants (same word, two
# accepted glyphs) — normalize the population side to the boundary file's
# spelling so the two datasets join by name.
_VILLAGE_NAME_CHAR_VARIANTS = str.maketrans({"双": "雙", "舘": "館", "脚": "腳"})


class MissingJoinError(Exception):
    """Raised when a village can't be matched to an official district or a
    population figure — surfaced loudly rather than silently writing a
    village with a null district/population into the reference data."""


def normalize_town_name(name: str) -> str:
    return _TOWN_NAME_RENAMES.get(name, name)


def townships_for_county(zones_geojson: dict, county_name: str) -> dict[str, int]:
    """Map each of the county's townships (name, normalized) to its official
    legislative district number (1-based, scoped to the county — the last two
    digits of the zone's national id)."""
    result: dict[str, int] = {}
    for feature in zones_geojson["features"]:
        props = feature["properties"]
        if not props["name"].startswith(county_name):
            continue
        district_number = int(str(props["id"])[-2:])
        for area in props["areas"].split(","):
            area = area.strip()
            if not area.startswith(county_name):
                continue
            town_name = normalize_town_name(area[len(county_name):])
            result[town_name] = district_number
    return result


def index_population(rows: list[dict], county_name: str) -> dict[tuple[str, str], int]:
    """Map (township, village) -> population, for one county's rows out of
    the (nationwide) ris.gov.tw population dataset."""
    result: dict[tuple[str, str], int] = {}
    for row in rows:
        site_id = row["site_id"]
        if not site_id.startswith(county_name):
            continue
        town_name = normalize_town_name(site_id[len(county_name):])
        village_name = row["village"].translate(_VILLAGE_NAME_CHAR_VARIANTS)
        result[(town_name, village_name)] = int(row["people_total"])
    return result


@dataclass
class VillageRecord:
    id: str
    county: str
    township: str
    name: str
    population: int
    official_district: int
    coordinates: list = field(repr=False)
    neighbor_ids: list[str]


def build_villages(
    county_name: str,
    prepared_villages: list[dict],
    district_map: dict[str, int],
    population_map: dict[tuple[str, str], int],
) -> tuple[list[VillageRecord], list[dict]]:
    """prepared_villages: dicts with id/township/name/coordinates/raw_arcs
    (coordinates and raw_arcs are None when the source geometry was missing).

    Returns (records, skipped) — skipped entries carry {"id", "reason"} so
    callers can report data-quality gaps instead of them vanishing silently.
    """
    skipped: list[dict] = []
    keepers: list[dict] = []
    for village in prepared_villages:
        if village["coordinates"] is None:
            skipped.append({"id": village["id"], "reason": "missing geometry"})
            continue
        keepers.append(village)

    neighbor_map = neighbors_from_shared_arcs({v["id"]: v["raw_arcs"] for v in keepers})

    records = []
    for village in keepers:
        township = normalize_town_name(village["township"])
        if township not in district_map:
            raise MissingJoinError(
                f"{village['id']} ({township}{village['name']}): no official district found"
            )
        population_key = (township, village["name"])
        if population_key not in population_map:
            raise MissingJoinError(
                f"{village['id']} ({township}{village['name']}): no population figure found"
            )
        records.append(
            VillageRecord(
                id=village["id"],
                county=county_name,
                township=township,
                name=village["name"],
                population=population_map[population_key],
                official_district=district_map[township],
                coordinates=village["coordinates"],
                neighbor_ids=sorted(neighbor_map[village["id"]]),
            )
        )

    return records, skipped
