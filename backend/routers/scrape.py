import asyncio
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
def run_scraper(
    source: str,
    max_files: int = 200,
    background_tasks: BackgroundTasks = BackgroundTasks(),
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
    from backend.lib.dedup import sha256_of
    from backend.lib.storage import file_path_for, ensure_parent
    from backend.lib.metadata import extract_metadata
    from backend.models import MidiFile, ScrapeError
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

                existing = db.query(MidiFile).filter_by(source_url=sf.source_url).first()
                if existing:
                    continue

                try:
                    data = await scraper.download(sf)
                except Exception as e:
                    errors += 1
                    db.add(ScrapeError(source_name=source_name, url=sf.source_url, error_msg=str(e), occurred_at=datetime.now(UTC)))
                    db.commit()
                    continue

                file_hash = sha256_of(data)
                if db.query(MidiFile).filter_by(file_hash=file_hash).first():
                    continue

                meta = extract_metadata(data)
                path = file_path_for(source_name, file_hash, settings.midi_storage_dir)
                ensure_parent(path)
                path.write_bytes(data)

                db.add(MidiFile(
                    file_hash=file_hash,
                    filename=sf.raw_filename,
                    source_url=sf.source_url,
                    page_url=sf.page_url,
                    source_name=source_name,
                    title=meta.title or sf.extra.get("title"),
                    composer=meta.composer or sf.extra.get("composer"),
                    genre=sf.extra.get("genre"),
                    bpm=meta.bpm,
                    duration_sec=meta.duration_sec,
                    track_count=meta.track_count,
                    time_signature=meta.time_signature,
                    scraped_at=datetime.now(UTC),
                    file_path=str(path.relative_to(settings.midi_storage_dir)),
                    file_size=len(data),
                ))
                db.commit()
                added += 1
                _jobs[job_id].update({"files_found": found, "files_added": added, "errors": errors})

        _jobs[job_id] = {"status": "completed", "files_found": found, "files_added": added, "errors": errors}

    except Exception as e:
        _jobs[job_id] = {"status": "failed", "error": str(e), "files_found": found, "files_added": added, "errors": errors}
    finally:
        db.close()
