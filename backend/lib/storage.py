from pathlib import Path

def file_path_for(source_name: str, file_hash: str, storage_dir: str = "./data/midi_files") -> Path:
    """Returns the absolute path where a MIDI file should be stored.
    Uses two-char prefix sharding: {storage_dir}/{source}/{hash[:2]}/{hash}.mid
    """
    base = Path(storage_dir)
    return base / source_name / file_hash[:2] / f"{file_hash}.mid"


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
