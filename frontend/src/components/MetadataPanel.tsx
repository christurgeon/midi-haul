import { X, ExternalLink } from "lucide-react";
import type { MidiFile } from "../api/client";

interface Props {
  file: MidiFile | null;
  onClose: () => void;
  onPlay: (file: MidiFile) => void;
}

function Row({ label, value }: { label: string; value: React.ReactNode }) {
  if (!value) return null;
  return (
    <div className="flex gap-2 text-sm py-1 border-b last:border-0">
      <span className="w-28 text-gray-400 shrink-0">{label}</span>
      <span className="text-gray-800 break-all">{value}</span>
    </div>
  );
}

export function MetadataPanel({ file, onClose, onPlay }: Props) {
  if (!file) return null;

  const genres = file.genre ? file.genre.split(",").map((g) => g.trim()) : [];

  return (
    <div className="w-72 border-l bg-white overflow-y-auto flex-shrink-0">
      <div className="flex items-center justify-between p-3 border-b">
        <h2 className="font-semibold text-sm">File Info</h2>
        <button onClick={onClose}><X className="h-4 w-4 text-gray-400" /></button>
      </div>
      <div className="p-3 flex flex-col gap-1">
        <Row label="Title" value={file.title} />
        <Row label="Composer" value={file.composer} />
        <Row label="BPM" value={file.bpm?.toFixed(0)} />
        <Row label="Duration" value={file.duration_sec ? `${Math.floor(file.duration_sec / 60)}:${String(Math.floor(file.duration_sec % 60)).padStart(2, "0")}` : null} />
        <Row label="Time sig." value={file.time_signature} />
        <Row label="Tracks" value={file.track_count} />
        <Row label="Source" value={file.source_name} />
        <Row label="File size" value={file.file_size ? `${(file.file_size / 1024).toFixed(1)} KB` : null} />
        <Row label="Added" value={new Date(file.scraped_at).toLocaleDateString()} />
        <Row label="Play count" value={file.play_count} />
        {genres.length > 0 && (
          <div className="flex flex-wrap gap-1 pt-1">
            {genres.map((g) => <span key={g} className="px-2 py-0.5 bg-indigo-50 text-indigo-600 text-xs rounded-full">{g}</span>)}
          </div>
        )}
        <div className="flex gap-2 pt-3">
          <button
            onClick={() => onPlay(file)}
            className="flex-1 py-1.5 bg-indigo-500 text-white text-sm rounded hover:bg-indigo-600"
          >
            Play
          </button>
          <a
            href={`/api/midi/${file.id}/stream`}
            download={file.filename}
            className="flex-1 py-1.5 border text-sm rounded text-center hover:bg-gray-50"
          >
            Download
          </a>
        </div>
        {file.source_url && (
          <a href={file.source_url} target="_blank" rel="noopener noreferrer" className="flex items-center gap-1 text-xs text-indigo-400 hover:underline pt-1">
            <ExternalLink className="h-3 w-3" /> View source
          </a>
        )}
      </div>
    </div>
  );
}
