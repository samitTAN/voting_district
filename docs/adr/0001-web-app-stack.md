# 0001: Web app stack — FastAPI + vanilla JS + Leaflet

## Status

Accepted (2026-08-13)

## Context

Issue #9 (the v0 spec) explicitly defers this choice: "Frontend framework, backend/storage technology, hosting... are not decided by this spec — they belong to implementation planning." No prior issue, comment, or ADR in this repo actually picks a stack. CLAUDE.md carried a parenthetical "(FastAPI, per the spec)" that doesn't trace to anything in issue #9's body or any issue/comment in the tracker — treated as stale/aspirational, not a real decision.

Issue #12 (畫線頁) is the first ticket that needs an actual web app: a backend serving the `data_pipeline`-built SQLite reference data, and a frontend rendering real village geometry on a clickable map.

## Decision

- **Backend**: FastAPI. Thin JSON API over the existing SQLite reference data (`data/reference.db`), reusing `districting.assignment.evaluate_assignment` directly rather than reimplementing validation logic elsewhere.
- **Frontend**: vanilla JS, no build step. Matches both existing throwaway prototypes (issue #6/#7, plain HTML/JS) and keeps v0 free of framework/build-tooling decisions it doesn't need yet.
- **Map rendering**: Leaflet, loaded via CDN script tag (no bundler). Village polygons render from the reference data's stored coordinates (GeoJSON-shaped Polygon/MultiPolygon rings); adjacency and validation stay server-side.

## Consequences

- The validation seam (`evaluateAssignment`) stays server-side and single-sourced: the frontend POSTs the in-progress assignment to the backend on every village click rather than duplicating population/contiguity logic in JS. Acceptable latency at county-scale village counts (low hundreds). This includes the ±15% threshold itself — the `/evaluate` response carries a `within_threshold` flag per district so the frontend never redefines `DEVIATION_THRESHOLD` to decide chip color; `districting.assignment` stays the only place that constant is defined.
- No component framework decision is made here — if #13-15 (save/share, gallery) outgrow vanilla JS, that's a new decision, not an extension of this one.
- The reference-data table (`data_pipeline/db.py`'s `villages` schema) has no explicit Polygon/MultiPolygon type column; the API layer disambiguates by coordinate-array nesting depth (3 levels = Polygon, 4 = MultiPolygon), matching how `data_pipeline/topojson.py` produces both shapes.
