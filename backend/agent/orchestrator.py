import json
import logging
from datetime import datetime, UTC
from sqlalchemy.orm import Session
import anthropic

from backend.config import settings
from backend.models import AgentRun, AgentRunStep, ScrapeSource, ScrapeError, MidiFile
from backend.agent.tools import TOOLS
from backend.lib.ingest import ingest_file, record_scrape_error

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are midi-haul's autonomous collection agent. Your goal is to grow the MIDI file library.

Each run you should:
1. Call list_known_sources to see which sources are stale (not scraped in 7+ days) or have high error counts.
2. Run stale scrapers, starting with the most reliable ones.
3. Check get_scrape_errors for any sources that have been failing.
4. Optionally search for new MIDI sources and run the crawler on 1-2 promising URLs.
5. Use log_message to provide a brief status update at the start and end.

Stop when you have run all stale sources or when you have made enough progress for one session.
Be efficient — do not run the same scraper twice in one session."""

SCRAPER_MAP = None  # populated lazily to avoid circular imports at module load


def _get_scraper_map():
    global SCRAPER_MAP
    if SCRAPER_MAP is None:
        from backend.scrapers import BitMidiScraper, VGMusicScraper, FreeMidiScraper, KunstderfugeScraper
        SCRAPER_MAP = {
            "bitmidi": BitMidiScraper,
            "vgmusic": VGMusicScraper,
            "freemidi": FreeMidiScraper,
            "kunstderfuge": KunstderfugeScraper,
        }
    return SCRAPER_MAP


async def run_agent(run_id: int, db: Session) -> None:
    """Execute one agent run. Updates the AgentRun record throughout."""
    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
    messages = [{"role": "user", "content": "Begin the MIDI collection run."}]
    tool_call_count = 0

    try:
        while tool_call_count < settings.agent_max_steps:
            response = await client.messages.create(
                model=settings.agent_model,
                max_tokens=4096,
                system=SYSTEM_PROMPT,
                tools=TOOLS,
                messages=messages,
            )

            messages.append({"role": "assistant", "content": response.content})

            if response.stop_reason == "end_turn":
                break
            elif response.stop_reason == "tool_use":
                tool_results = []
                for block in response.content:
                    if block.type == "tool_use":
                        tool_call_count += 1
                        result = await _dispatch_tool(block.name, block.input, run_id, db)
                        result_str = json.dumps(result)
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": result_str,
                        })
                        _save_step(run_id, block.name, block.input, result, db)

                messages.append({"role": "user", "content": tool_results})
            else:
                logger.warning("Agent run %d stopped unexpectedly: %s", run_id, response.stop_reason)
                break

        _finish_run(run_id, "completed", db)

    except Exception as e:
        logger.error("Agent run %d failed: %s", run_id, e)
        _finish_run(run_id, "failed", db)
        raise


def _save_step(run_id: int, tool_name: str, tool_input: dict, result: dict, db: Session) -> None:
    step = AgentRunStep(
        run_id=run_id,
        tool_name=tool_name,
        tool_input=json.dumps(tool_input),
        tool_result=json.dumps(result),
        executed_at=datetime.now(UTC),
    )
    db.add(step)
    db.commit()


def _finish_run(run_id: int, status: str, db: Session) -> None:
    run = db.get(AgentRun, run_id)
    if run:
        run.finished_at = datetime.now(UTC)
        run.status = status
        db.commit()


async def _dispatch_tool(name: str, inputs: dict, run_id: int, db: Session) -> dict:
    if name == "list_known_sources":
        return _tool_list_sources(db)
    elif name == "run_scraper":
        return await _tool_run_scraper(inputs, run_id, db)
    elif name == "run_crawler":
        return await _tool_run_crawler(inputs, run_id, db)
    elif name == "search_web_for_midi_sources":
        return await _tool_search_web(inputs)
    elif name == "get_scrape_errors":
        return _tool_get_errors(inputs, db)
    elif name == "log_message":
        return _tool_log(inputs, run_id, db)
    else:
        return {"error": f"Unknown tool: {name}"}


def _tool_list_sources(db: Session) -> dict:
    sources = db.query(ScrapeSource).all()
    now = datetime.now(UTC)
    result = []
    for s in sources:
        days_since = None
        if s.last_scraped:
            days_since = (now - s.last_scraped.replace(tzinfo=UTC)).days
        result.append({
            "name": s.name,
            "display_name": s.display_name,
            "file_count": s.file_count,
            "error_count": s.error_count,
            "enabled": s.enabled,
            "days_since_scraped": days_since,
        })
    return {"sources": result}


async def _tool_run_scraper(inputs: dict, run_id: int, db: Session) -> dict:
    import httpx

    source_name = inputs["source"]
    max_files = inputs.get("max_files", 200)

    scraper_map = _get_scraper_map()
    if source_name not in scraper_map:
        return {"error": f"Unknown scraper: {source_name}"}

    source_record = db.query(ScrapeSource).filter_by(name=source_name).first()
    if source_record and not source_record.enabled:
        return {"error": f"Source '{source_name}' is disabled."}

    found = added = errors = 0

    async with httpx.AsyncClient(headers={"User-Agent": "midi-haul/0.1"}) as client:
        scraper = scraper_map[source_name](client, settings.scrape_rate_limit_delay)
        async for sf in scraper.iter_files():
            found += 1
            if found >= max_files:
                break

            ok, err = await ingest_file(sf, scraper, source_name, db, settings.midi_storage_dir)
            if err:
                errors += 1
                record_scrape_error(source_name, sf.source_url, err, db)
            elif ok:
                added += 1

    _update_source_stats(source_name, added, errors, db)
    _update_run_files_added(run_id, added, db)

    return {"source": source_name, "found": found, "added": added, "errors": errors}


async def _tool_run_crawler(inputs: dict, run_id: int, db: Session) -> dict:
    import httpx
    from backend.scrapers.crawler import GeneralCrawler

    seed_urls = inputs["seed_urls"]
    max_depth = inputs.get("max_depth", 2)
    max_files = inputs.get("max_files", 100)

    found = added = errors = 0

    async with httpx.AsyncClient(headers={"User-Agent": "midi-haul/0.1"}) as client:
        crawler = GeneralCrawler(client, settings.scrape_rate_limit_delay, seed_urls, max_depth)
        async for sf in crawler.iter_files():
            found += 1
            if found >= max_files:
                break

            ok, err = await ingest_file(sf, crawler, "crawler", db, settings.midi_storage_dir)
            if err:
                errors += 1
                record_scrape_error("crawler", sf.source_url, err, db)
            elif ok:
                added += 1

    _update_run_files_added(run_id, added, db)
    return {"found": found, "added": added, "errors": errors, "seeds": seed_urls}


async def _tool_search_web(inputs: dict) -> dict:
    import httpx
    query = inputs["query"]

    if not settings.brave_search_api_key:
        return {
            "note": "Brave Search API not configured. Set BRAVE_SEARCH_API_KEY to enable.",
            "suggestion": f"Try crawling known MIDI sites for: {query}",
        }

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                "https://api.search.brave.com/res/v1/web/search",
                params={"q": query, "count": 10},
                headers={"Accept": "application/json", "X-Subscription-Token": settings.brave_search_api_key},
                timeout=10,
            )
        resp.raise_for_status()
        results = resp.json().get("web", {}).get("results", [])
        return {"urls": [r["url"] for r in results], "query": query}
    except Exception as e:
        return {"error": str(e), "query": query}


def _tool_get_errors(inputs: dict, db: Session) -> dict:
    source = inputs.get("source")
    limit = inputs.get("limit", 20)
    q = db.query(ScrapeError)
    if source:
        q = q.filter_by(source_name=source)
    errors = q.order_by(ScrapeError.occurred_at.desc()).limit(limit).all()
    return {
        "errors": [
            {"source": e.source_name, "url": e.url, "error": e.error_msg, "at": e.occurred_at.isoformat()}
            for e in errors
        ]
    }


def _tool_log(inputs: dict, run_id: int, db: Session) -> dict:
    message = inputs["message"]
    logger.info("Agent run %d: %s", run_id, message)
    step = AgentRunStep(
        run_id=run_id,
        tool_name="log_message",
        tool_input=json.dumps({"message": message}),
        tool_result=json.dumps({"ok": True}),
        executed_at=datetime.now(UTC),
    )
    db.add(step)
    db.commit()
    return {"ok": True}


def _update_source_stats(source_name: str, files_added: int, errors: int, db: Session) -> None:
    source = db.query(ScrapeSource).filter_by(name=source_name).first()
    if source:
        source.file_count += files_added
        source.error_count += errors
        source.last_scraped = datetime.now(UTC)
        db.commit()


def _update_run_files_added(run_id: int, count: int, db: Session) -> None:
    run = db.get(AgentRun, run_id)
    if run:
        run.files_added += count
        db.commit()
