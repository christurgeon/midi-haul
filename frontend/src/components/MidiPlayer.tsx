import "html-midi-player";
import { useRef, useEffect } from "react";
import { api } from "../api/client";
import type { MidiFile } from "../api/client";
import { X } from "lucide-react";

interface Props {
  file: MidiFile | null;
  onClose: () => void;
}

export function MidiPlayer({ file, onClose }: Props) {
  const playerRef = useRef<HTMLElement>(null);

  useEffect(() => {
    const el = playerRef.current;
    if (!el || !file) return;
    const handler = () => api.incrementPlay(file.id);
    el.addEventListener("play", handler);
    return () => el.removeEventListener("play", handler);
  }, [file]);

  if (!file) return null;

  return (
    <div className="fixed bottom-0 left-0 right-0 bg-white border-t shadow-lg px-4 py-3 z-50">
      <div className="max-w-5xl mx-auto flex flex-col gap-2">
        <div className="flex items-center justify-between">
          <div>
            <span className="font-medium">{file.title || file.filename}</span>
            {file.composer && <span className="text-gray-400 text-sm ml-2">— {file.composer}</span>}
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600"><X className="h-5 w-5" /></button>
        </div>
        <midi-player
          ref={playerRef as any}
          src={`/api/midi/${file.id}/stream`}
          sound-font
          style={{ width: "100%" }}
        />
      </div>
    </div>
  );
}
