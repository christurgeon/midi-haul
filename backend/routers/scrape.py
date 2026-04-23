import uuid
from datetime import datetime, UTC
from typing import Any
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import ScrapeSource, ScrapeError
from backend.schemas import ScrapeSourceSchema, ScrapeErrorSchema

router = APIRouter(tags=["scrape"])

# In-memory job status store (good enough for single-process)
_jobs: dict[str, dict[str, Any]] = {}


@router.get("/sources", response_model=list[ScrapeSourceSchema])
def list_sources(db: Session = Depends(get_db)):
    return db.query(ScrapeSource).all()


@router.post("/run")
async def run_scraper(
    source: str,
    background_tasks: BackgroundTasks,
    max_files: int = 200,
    db: Session = Depends(get_db),
):
    job_id = str(uuid.uuid4())
    _jobs[job_id] = {"status": "running", "files_found": 0, "files_added": 0, "errors": 0}
    background_tasks.add_task(_run_scraper_job, job_id, source, max_files)
    return {"job_id": job_id}


@router.get("/status/{job_id}")
def get_job_status(job_id: str):
    job = _jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.get("/errors", response_model=list[ScrapeErrorSchema])
def list_errors(
    source: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    q = db.query(ScrapeError)
    if source:
        q = q.filter_by(source_name=source)
    return q.order_by(ScrapeError.occurred_at.desc()).limit(limit).all()


async def _run_scraper_job(job_id: str, source_name: str, max_files: int) -> None:
    import httpx
    from backend.scrapers import BitMidiScraper, VGMusicScraper, FreeMidiScraper, KunstderfugeScraper
    from backend.lib.ingest import ingest_file, record_scrape_error
    from backend.config import settings

    scraper_map = {
        "bitmidi": BitMidiScraper,
        "vgmusic": VGMusicScraper,
        "freemidi": FreeMidiScraper,
        "kunstderfuge": KunstderfugeScraper,
    }

    if source_name not in scraper_map:
        _jobs[job_id] = {"status": "failed", "error": f"Unknown source: {source_name}"}
        return

    from backend.database import SessionLocal
    db = SessionLocal()
    found = added = errors = 0

    try:
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

                _jobs[job_id].update({"files_found": found, "files_added": added, "errors": errors})

        _jobs[job_id] = {"status": "completed", "files_found": found, "files_added": added, "errors": errors}

    except Exception as e:
        _jobs[job_id] = {"status": "failed", "error": str(e), "files_found": found, "files_added": added, "errors": errors}
    finally:
        db.close()
