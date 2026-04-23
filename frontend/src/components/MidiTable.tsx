import { Play } from "lucide-react";
import type { MidiFile } from "../api/client";

interface Props {
  files: MidiFile[];
  total: number;
  page: number;
  limit: number;
  onPageChange: (page: number) => void;
  onPlay: (file: MidiFile) => void;
  onSelect: (file: MidiFile) => void;
  activeId: number | null;
  sort: string;
  onSort: (col: string) => void;
}

const cols: { key: string; label: string }[] = [
  { key: "title", label: "Title" },
  { key: "composer", label: "Composer" },
  { key: "bpm", label: "BPM" },
  { key: "duration_sec", label: "Duration" },
  { key: "source_name", label: "Source" },
  { key: "scraped_at", label: "Added" },
  { key: "play_count", label: "Plays" },
];

function fmt(sec: number | null) {
  if (!sec) return "—";
  const m = Math.floor(sec / 60);
  const s = Math.floor(sec % 60);
  return `${m}:${s.toString().padStart(2, "0")}`;
}

export function MidiTable({ files, total, page, limit, onPageChange, onPlay, onSelect, activeId, sort, onSort }: Props) {
  const [sortCol, sortDir] = sort.split(":");
  const pages = Math.ceil(total / limit);

  function handleSort(col: string) {
    if (sortCol === col) {
      onSort(`${col}:${sortDir === "desc" ? "asc" : "desc"}`);
    } else {
      onSort(`${col}:desc`);
    }
  }

  return (
    <div className="flex flex-col gap-2">
      <div className="overflow-x-auto rounded border">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 text-gray-600 text-xs uppercase">
            <tr>
              <th className="w-8 px-2 py-2"></th>
              {cols.map((c) => (
                <th
                  key={c.key}
                  className="px-3 py-2 text-left cursor-pointer select-none hover:bg-gray-100"
                  onClick={() => handleSort(c.key)}
                >
                  {c.label} {sortCol === c.key ? (sortDir === "desc" ? "↓" : "↑") : ""}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {files.map((f) => (
              <tr
                key={f.id}
                className={`border-t hover:bg-indigo-50 cursor-pointer ${activeId === f.id ? "bg-indigo-50" : ""}`}
                onClick={() => onSelect(f)}
              >
                <td className="px-2 py-1.5 text-center">
                  <button
                    onClick={(e) => { e.stopPropagation(); onPlay(f); }}
                    className="text-indigo-500 hover:text-indigo-700"
                  >
                    <Play className="h-4 w-4" />
                  </button>
                </td>
                <td className="px-3 py-1.5 font-medium">{f.title || f.filename}</td>
                <td className="px-3 py-1.5 text-gray-500">{f.composer || "—"}</td>
                <td className="px-3 py-1.5 text-gray-500">{f.bpm ? f.bpm.toFixed(0) : "—"}</td>
                <td className="px-3 py-1.5 text-gray-500">{fmt(f.duration_sec)}</td>
                <td className="px-3 py-1.5">
                  <span className="px-1.5 py-0.5 rounded bg-gray-100 text-xs">{f.source_name}</span>
                </td>
                <td className="px-3 py-1.5 text-gray-400 text-xs">{new Date(f.scraped_at).toLocaleDateString()}</td>
                <td className="px-3 py-1.5 text-gray-400">{f.play_count}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="flex items-center justify-between text-sm text-gray-500">
        <span>{total} files</span>
        <div className="flex gap-1">
          <button disabled={page <= 1} onClick={() => onPageChange(page - 1)} className="px-2 py-1 border rounded disabled:opacity-40">←</button>
          <span className="px-2 py-1">{page} / {pages || 1}</span>
          <button disabled={page >= pages} onClick={() => onPageChange(page + 1)} className="px-2 py-1 border rounded disabled:opacity-40">→</button>
        </div>
      </div>
    </div>
  );
}
