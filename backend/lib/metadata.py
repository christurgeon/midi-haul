import io
from dataclasses import dataclass
import mido

@dataclass
class MidiMeta:
    title: str | None
    composer: str | None
    bpm: float | None
    duration_sec: float
    track_count: int
    time_signature: str | None


def extract_metadata(data: bytes) -> MidiMeta:
    mid = mido.MidiFile(file=io.BytesIO(data))

    title = composer = bpm = time_sig = None
    tempo = 500_000  # default 120 BPM

    for track in mid.tracks:
        for msg in track:
            if msg.type == "track_name" and not title:
                v = msg.name.strip()
                title = v if v else None
            elif msg.type == "text" and not title:
                v = msg.text.strip()
                title = v if v else None
            elif msg.type == "set_tempo" and bpm is None:
                tempo = msg.tempo
                bpm = round(60_000_000 / tempo, 1)
            elif msg.type == "time_signature" and time_sig is None:
                time_sig = f"{msg.numerator}/{msg.denominator}"
            elif msg.type == "copyright" and composer is None:
                v = msg.text.strip()
                composer = v if v else None

    return MidiMeta(
        title=title,
        composer=composer,
        bpm=bpm,
        duration_sec=round(mid.length, 2),
        track_count=len(mid.tracks),
        time_signature=time_sig,
    )
