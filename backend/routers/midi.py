import os
from datetime import datetime
from typing import Literal
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, asc

from backend.database import get_db
from backend.models import MidiFile
from backend.schemas import MidiFileSchema, MidiFileList

router = APIRouter(tags=["midi"])


@router.get("", response_model=MidiFileList)
def list_midi_files(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    search: str | None = Query(None),
    source: str | None = Query(None),
    genre: str | None = Query(None),
    sort: str = Query("scraped_at:desc"),
    db: Session = Depends(get_db),
):
    q = db.query(MidiFile)

    if search:
        like = f"%{search}%"
        q = q.filter(
            MidiFile.title.ilike(like)
            | MidiFile.composer.ilike(like)
            | MidiFile.filename.ilike(like)
        )
    if source:
        q = q.filter(MidiFile.source_name == source)
    if genre:
        q = q.filter(MidiFile.genre.ilike(f"%{genre}%"))

    total = q.count()

    sort_col, sort_dir = (sort.split(":") + ["asc"])[:2]
    col_map = {
        "scraped_at": MidiFile.scraped_at,
        "title": MidiFile.title,
        "composer": MidiFile.composer,
        "bpm": MidiFile.bpm,
        "duration_sec": MidiFile.duration_sec,
        "play_count": MidiFile.play_count,
    }
    col = col_map.get(sort_col, MidiFile.scraped_at)
    q = q.order_by(desc(col) if sort_dir == "desc" else asc(col))

    items = q.offset((page - 1) * limit).limit(limit).all()
    return MidiFileList(items=items, total=total, page=page, limit=limit)


@router.get("/stats")
def get_stats(db: Session = Depends(get_db)):
    total = db.query(func.count(MidiFile.id)).scalar()
    total_size = db.query(func.sum(MidiFile.file_size)).scalar() or 0
    by_source = dict(
        db.query(MidiFile.source_name, func.count(MidiFile.id))
        .group_by(MidiFile.source_name)
        .all()
    )
    return {
        "total": total,
        "total_size_mb": round(total_size / 1_048_576, 2),
        "by_source": by_source,
    }


@router.get("/{midi_id}", response_model=MidiFileSchema)
def get_midi_file(midi_id: int, db: Session = Depends(get_db)):
    midi = db.get(MidiFile, midi_id)
    if not midi:
        raise HTTPException(status_code=404, detail="Not found")
    return midi


@router.get("/{midi_id}/stream")
def stream_midi(midi_id: int, db: Session = Depends(get_db)):
    midi = db.get(MidiFile, midi_id)
    if not midi:
        raise HTTPException(status_code=404, detail="Not found")

    full_path = os.path.join(settings_midi_storage_dir(), midi.file_path)
    if not os.path.isfile(full_path):
        raise HTTPException(status_code=404, detail="File not on disk")

    def iter_file():
        with open(full_path, "rb") as f:
            while chunk := f.read(65536):
                yield chunk

    return StreamingResponse(
        iter_file(),
        media_type="audio/midi",
        headers={"Content-Disposition": f'attachment; filename="{midi.filename}"'},
    )


@router.post("/{midi_id}/play")
def increment_play(midi_id: int, db: Session = Depends(get_db)):
    midi = db.get(MidiFile, midi_id)
    if not midi:
        raise HTTPException(status_code=404, detail="Not found")
    midi.play_count += 1
    db.commit()
    return {"ok": True}


def settings_midi_storage_dir() -> str:
    from backend.config import settings
    return settings.midi_storage_dir
