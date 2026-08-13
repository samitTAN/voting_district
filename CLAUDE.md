# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

自己的選區自己畫 ("Draw Your Own Electoral District") is a civic-tech project inspired by a g0v (Taiwan's "零時政府") hackathon proposal. The goal is to build a website that lets citizens participate in drawing/redistricting electoral district boundaries, as a participatory, transparent alternative to redistricting done solely by officials. See README.md for the full background and the original hackathon pitch.

## Current status

This repository is in the earliest planning/setup stage: no application code exists yet, only project scaffolding (README, LICENSE, `.gitignore`). There are no build, lint, or test commands to run yet — when code is added, this file should be updated with the actual commands and architecture notes.

## Development environment

The project uses Python 3.14 via a local `venv` (currently just base `pip`/`setuptools`, no dependencies installed yet):

```bash
python3.14 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

`venv/` is gitignored — each developer creates their own local environment; it is not committed.

## Agent skills

### Issue tracker

Issues are tracked as GitHub Issues in samitTAN/voting_district, via the `gh` CLI. See `docs/agents/issue-tracker.md`.

### Domain docs

Single-context layout — `CONTEXT.md` + `docs/adr/` at the repo root. See `docs/agents/domain.md`.

## License

MIT License (see LICENSE).
