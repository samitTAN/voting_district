import pytest

from data_pipeline.build import (
    normalize_town_name,
    townships_for_county,
    index_population,
    build_villages,
    MissingJoinError,
)


def test_normalize_town_name_applies_known_administrative_renames():
    # 頭份鎮 was upgraded to 頭份市 (county-administered city) in 2015; the
    # 1982-vintage boundary file still calls it 頭份鎮.
    assert normalize_town_name("頭份鎮") == "頭份市"


def test_normalize_town_name_passes_through_unknown_names():
    assert normalize_town_name("苗栗市") == "苗栗市"


def test_townships_for_county_maps_normalized_names_to_district_numbers():
    zones_geojson = {
        "features": [
            {"properties": {"id": 1000501, "name": "苗栗縣第01選區", "areas": "苗栗縣苑裡鎮,苗栗縣通霄鎮"}},
            {"properties": {"id": 1000502, "name": "苗栗縣第02選區", "areas": "苗栗縣苗栗市,苗栗縣頭份市"}},
            {"properties": {"id": 1000901, "name": "雲林縣第01選區", "areas": "雲林縣虎尾鎮"}},
        ]
    }

    result = townships_for_county(zones_geojson, "苗栗縣")

    assert result == {
        "苑裡鎮": 1,
        "通霄鎮": 1,
        "苗栗市": 2,
        "頭份市": 2,
    }
    # 1000501 -> district 1, 1000502 -> district 2: last two digits of the
    # official id are the within-county district number.


def test_index_population_normalizes_known_character_variants_in_village_names():
    # ris.gov.tw spells these villages with informal character variants
    # (双/舘/脚) that the boundary file spells traditionally (雙/館/腳).
    rows = [
        {"site_id": "苗栗縣三義鄉", "village": "双湖村", "people_total": "2046"},
        {"site_id": "苗栗縣竹南鎮", "village": "公舘里", "people_total": "1000"},
        {"site_id": "苗栗縣苑裡鎮", "village": "山脚里", "people_total": "900"},
    ]

    result = index_population(rows, "苗栗縣")

    assert result == {
        ("三義鄉", "雙湖村"): 2046,
        ("竹南鎮", "公館里"): 1000,
        ("苑裡鎮", "山腳里"): 900,
    }


def test_index_population_keys_by_township_and_village_within_county():
    rows = [
        {"site_id": "苗栗縣苗栗市", "village": "中山里", "people_total": "5000"},
        {"site_id": "苗栗縣頭份市", "village": "中央里", "people_total": "3000"},
        {"site_id": "新北市板橋區", "village": "留侯里", "people_total": "1640"},
    ]

    result = index_population(rows, "苗栗縣")

    assert result == {
        ("苗栗市", "中山里"): 5000,
        ("頭份市", "中央里"): 3000,
    }


def test_build_villages_assembles_records_with_district_population_and_neighbors():
    prepared = [
        {"id": "A", "township": "苗栗市", "name": "中山里", "coordinates": [[(0, 0), (1, 0), (1, 1), (0, 0)]], "raw_arcs": [[0, 1]]},
        {"id": "B", "township": "頭份鎮", "name": "中央里", "coordinates": [[(1, 0), (2, 0), (2, 1), (1, 0)]], "raw_arcs": [[-2, 2]]},
    ]
    district_map = {"苗栗市": 2, "頭份市": 2}
    population_map = {("苗栗市", "中山里"): 5000, ("頭份市", "中央里"): 3000}

    records, skipped = build_villages("苗栗縣", prepared, district_map, population_map)

    assert skipped == []
    assert len(records) == 2
    a = next(r for r in records if r.id == "A")
    b = next(r for r in records if r.id == "B")
    assert a.township == "苗栗市"
    assert a.population == 5000
    assert a.official_district == 2
    assert a.neighbor_ids == ["B"]
    assert b.township == "頭份市"  # normalized from 頭份鎮
    assert b.population == 3000
    assert b.neighbor_ids == ["A"]


def test_build_villages_skips_entries_with_no_geometry_and_reports_them():
    prepared = [
        {"id": "A", "township": "苗栗市", "name": "中山里", "coordinates": [[(0, 0), (1, 0), (1, 1), (0, 0)]], "raw_arcs": [[0, 1]]},
        {"id": "Z", "township": "苗栗市", "name": "無地圖里", "coordinates": None, "raw_arcs": None},
    ]
    district_map = {"苗栗市": 2}
    population_map = {("苗栗市", "中山里"): 5000, ("苗栗市", "無地圖里"): 10}

    records, skipped = build_villages("苗栗縣", prepared, district_map, population_map)

    assert [r.id for r in records] == ["A"]
    assert skipped == [{"id": "Z", "reason": "missing geometry"}]


def test_build_villages_raises_on_unmatched_district_or_population():
    prepared = [
        {"id": "A", "township": "不存在鄉", "name": "中山里", "coordinates": [[(0, 0), (1, 0), (1, 1), (0, 0)]], "raw_arcs": [[0, 1]]},
    ]

    with pytest.raises(MissingJoinError):
        build_villages("苗栗縣", prepared, district_map={}, population_map={})
