# midi-haul

An AI-powered MIDI file collector. Uses site-specific scrapers and a Claude-powered agent to discover and download MIDI files from across the internet. A FastAPI + React UI lets you browse, search, and play your collection.

## Features

- **Scrapers**: BitMidi, VGMusic, FreeMIDI, Kunstderfuge + general web crawler
- **Agent**: Claude (claude-sonnet-4-5) autonomously decides what to scrape, retries failures, and discovers new sources
- **UI**: Searchable/sortable table, in-browser MIDI player, metadata panel, scrape controls, live agent log

## Setup

```bash
# Backend
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
playwright install chromium
cp .env.example .env  # add your ANTHROPIC_API_KEY
python -c "from backend.database import init_db; init_db()"
uvicorn backend.main:app --reload

# Frontend (separate terminal)
cd frontend && npm install && npm run dev
```

Open http://localhost:5173

## Stack

- **Backend**: Python 3.11+, FastAPI, SQLAlchemy, httpx, mido, Playwright, APScheduler
- **AI**: Anthropic Claude API with tool use
- **Frontend**: React 18, Vite, TypeScript, Tailwind CSS, html-midi-player
