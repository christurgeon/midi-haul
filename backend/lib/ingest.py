from datetime import datetime, UTC
from sqlalchemy.orm import Session

from backend.lib.dedup import sha256_of
from backend.lib.storage import file_path_for, ensure_parent
from backend.lib.metadata import extract_metadata
from backend.models import MidiFile, ScrapeError
from backend.scrapers.base import BaseScraper, ScrapedFile


async def ingest_file(
    sf: ScrapedFile,
    downloader: BaseScraper,
    source_name: str,
    db: Session,
    midi_storage_dir: str,
) -> tuple[bool, str | None]:
    """Download and persist one MIDI file. Returns (added, error_msg|None)."""
    if db.query(MidiFile).filter_by(source_url=sf.source_url).first():
        return False, None

    try:
        data = await downloader.download(sf)
    except Exception as e:
        return False, str(e)

    file_hash = sha256_of(data)
    if db.query(MidiFile).filter_by(file_hash=file_hash).first():
        return False, None

    meta = extract_metadata(data)
    path = file_path_for(source_name, file_hash, midi_storage_dir)
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
        file_path=str(path.relative_to(midi_storage_dir)),
        file_size=len(data),
    ))
    db.commit()
    return True, None


def record_scrape_error(source_name: str, url: str | None, error_msg: str, db: Session) -> None:
    db.add(ScrapeError(source_name=source_name, url=url, error_msg=error_msg, occurred_at=datetime.now(UTC)))
    db.commit()
