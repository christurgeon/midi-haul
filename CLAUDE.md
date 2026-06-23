# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

midi-haul collects MIDI files from the web. Site-specific scrapers and a general crawler feed a shared ingest pipeline; an autonomous Claude agent decides what to scrape on a schedule. A FastAPI backend serves a React UI for browsing, searching, and playing the collection.

## Commands

Backend uses `uv` — never activate the venv, prefix everything with `uv run`. Run all backend commands from the repo root (relative paths like `data/` and `frontend/dist` resolve against CWD).

```bash
uv sync                                   # install deps from uv.lock into .venv
uv run playwright install chromium        # required once for Playwright-based scrapers
uv run python -c "from backend.database import init_db; init_db()"   # create tables + seed sources
uv run uvicorn backend.main:app --reload  # dev server on :8000 (also auto-inits DB + starts scheduler via lifespan)

uv run pytest                             # all tests
uv run pytest tests/test_agent.py::test_tools_count   # single test

cd frontend && npm install && npm run dev # Vite dev server on :5173, proxies /api -> :8000
cd frontend && npm run build              # tsc -b && vite build -> frontend/dist
cd frontend && npm run lint               # eslint
```

Requires `ANTHROPIC_API_KEY` in `.env` (copy from `.env.example`) for the agent. `BRAVE_SEARCH_API_KEY` is optional — without it the agent's web-search tool returns a "not configured" note instead of URLs.

## Architecture

**Two entry points, one pipeline.** Scraping is triggered either manually (`POST /api/scrape/run` → `routers/scrape.py::_run_scraper_job`, tracked in an in-memory `_jobs` dict) or autonomously by the Claude agent (`agent/orchestrator.py`). Both paths run the same loop: instantiate a scraper, iterate `iter_files()`, and call `lib/ingest.py::ingest_file` per file. The scheduler (`tasks/scheduler.py`, APScheduler, default cron `0 2 * * *`) kicks off agent runs.

**The agent loop** (`orchestrator.py::run_agent`) is a standard Anthropic tool-use loop: call `messages.create` with `TOOLS`, dispatch any `tool_use` blocks through `_dispatch_tool`, append results, repeat until `end_turn` or `agent_max_steps` tool calls. Tool schemas live in `agent/tools.py`; their implementations are the `_tool_*` functions in `orchestrator.py`. Every tool call is persisted as an `AgentRunStep`, which the UI tails live over SSE (`GET /api/agent/runs/{id}/stream`).

**Scrapers** subclass `BaseScraper` (`scrapers/base.py`) and implement the async generator `iter_files()` yielding `ScrapedFile` dataclasses. `download()` is inherited. The general `crawler.py` does BFS over seed URLs, same-domain link following, collecting `.mid`/`.midi` links.

**Ingest** (`lib/ingest.py`) dedups twice — first by `source_url`, then by sha256 `file_hash` after download — extracts metadata with `mido` (`lib/metadata.py`), stores the file content-addressed and sharded at `{storage_dir}/{source}/{hash[:2]}/{hash}.mid` (`lib/storage.py`), and writes a `MidiFile` row with a path relative to the storage dir.

**Data layer.** SQLAlchemy 2.0 (`Mapped`/`mapped_column`) models in `models.py`, SQLite by default. `database.py::init_db` does `create_all` + `seed_sources` only — **there is no migration tool (no Alembic)**, so any model change requires deleting `data/midi_haul.db` and re-initializing. Pydantic response schemas are separate (`schemas.py`, `from_attributes=True`).

**Frontend.** React 19 + Vite + Tailwind v4 + TanStack Query. All server calls go through the typed `api` object in `frontend/src/api/client.ts`. In-browser playback uses the `html-midi-player` web component (typed in `html-midi-player.d.ts`).

## Adding a scraper

The scraper registry is **duplicated in three places** — all must be updated, plus the file:

1. New `scrapers/<name>.py` subclassing `BaseScraper`.
2. Export it in `scrapers/__init__.py`.
3. Add to `orchestrator.py::_get_scraper_map`.
4. Add to the inline `scraper_map` in `routers/scrape.py::_run_scraper_job`.
5. Add a `ScrapeSource(...)` row in `database.py::seed_sources` so it shows up in the UI and the agent's `list_known_sources`.

## Testing notes

`pytest` runs in `asyncio_mode = auto` (no `@pytest.mark.asyncio` needed, though tests use it). The `db` fixture (`tests/conftest.py`) gives an in-memory SQLite session. HTTP is mocked with `respx`; the agent's Anthropic client is patched directly (see `test_agent.py`). There are no frontend tests.
