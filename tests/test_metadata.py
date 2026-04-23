import pytest
from pathlib import Path
from backend.lib.metadata import extract_metadata

TECHNO_MIDI = Path("/Users/christopherturgeon/Documents/Code/music-explore/techno_song.mid")


@pytest.mark.skipif(not TECHNO_MIDI.exists(), reason="techno_song.mid not found")
def test_extract_bpm():
    data = TECHNO_MIDI.read_bytes()
    meta = extract_metadata(data)
    assert meta.bpm == 123.0


@pytest.mark.skipif(not TECHNO_MIDI.exists(), reason="techno_song.mid not found")
def test_extract_duration():
    data = TECHNO_MIDI.read_bytes()
    meta = extract_metadata(data)
    assert meta.duration_sec > 0


@pytest.mark.skipif(not TECHNO_MIDI.exists(), reason="techno_song.mid not found")
def test_extract_track_count():
    data = TECHNO_MIDI.read_bytes()
    meta = extract_metadata(data)
    assert meta.track_count == 6


def test_extract_empty_bytes_raises():
    with pytest.raises(Exception):
        extract_metadata(b"")


def test_extract_invalid_bytes_raises():
    with pytest.raises(Exception):
        extract_metadata(b"not a midi file at all")
