# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

自己的選區自己畫 ("Draw Your Own Electoral District") is a civic-tech project inspired by a g0v (Taiwan's "零時政府") hackathon proposal. The goal is to build a website that lets citizens participate in drawing/redistricting electoral district boundaries, as a participatory, transparent alternative to redistricting done solely by officials. See README.md for the full background and the original hackathon pitch.

## Current status

Planning is done — see the wayfinder map [自己的選區自己畫 v0 產品規格書](https://github.com/samitTAN/voting_district/issues/2) and the resulting [Spec：自己的選區自己畫 v0 畫線工具](https://github.com/samitTAN/voting_district/issues/9), which is split into tracer-bullet tickets (issues #10–#15). Implementation is underway; this file is updated as each ticket lands.

So far: the reference-data pipeline (`data_pipeline/`, issue #10) — fetches and joins Taiwan village boundary geometry, population, and official electoral-district data into SQLite. No web app (FastAPI, per the spec) exists yet.

## Development environment

The project uses Python 3.14 via a local `venv`:

```bash
python3.14 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -e ".[dev]"
```

`venv/` is gitignored — each developer creates their own local environment; it is not committed.

## Data pipeline

`data_pipeline/` builds the SQLite reference data (village geometry, population, official district assignment) the app reads, for one county at a time:

```bash
python scripts/build_reference_data.py --county 苗栗縣 --yyymm 11406
```

`--county` takes a real 縣市 name; `--yyymm` is an ROC year+month for the population snapshot (e.g. `11406` = 2025-06). Fetched source data is cached under `data/raw/` (gitignored); re-running replaces that county's rows rather than duplicating them. See `data_pipeline/sources.py` for where each source comes from and known data-quality caveats (e.g. the boundary file predates the 2010/2014 municipality mergers).

```bash
python -m pytest        # unit tests — pure logic (topojson decode, adjacency, joins) only; no network
python -m mypy data_pipeline/ scripts/ --ignore-missing-imports
```

## Agent skills

### Issue tracker

Issues are tracked as GitHub Issues in samitTAN/voting_district, via the `gh` CLI. See `docs/agents/issue-tracker.md`.

### Domain docs

Single-context layout — `CONTEXT.md` + `docs/adr/` at the repo root. See `docs/agents/domain.md`.

## License

MIT License (see LICENSE).
