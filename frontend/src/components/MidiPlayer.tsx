import "html-midi-player";
import { api } from "../api/client";
import type { MidiFile } from "../api/client";
import { X } from "lucide-react";

interface Props {
  file: MidiFile | null;
  onClose: () => void;
}

export function MidiPlayer({ file, onClose }: Props) {
  if (!file) return null;

  function handlePlay() {
    api.incrementPlay(file!.id);
  }

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
          src={`/api/midi/${file.id}/stream`}
          sound-font
          onPlay={handlePlay}
          style={{ width: "100%" }}
        />
      </div>
    </div>
  );
}
