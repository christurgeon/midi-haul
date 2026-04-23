import { useState } from "react";
import { QueryClient, QueryClientProvider, useQuery } from "@tanstack/react-query";
import { Music } from "lucide-react";
import { api } from "./api/client";
import type { MidiFile } from "./api/client";
import { MidiTable } from "./components/MidiTable";
import { MidiPlayer } from "./components/MidiPlayer";
import { MetadataPanel } from "./components/MetadataPanel";
import { SearchBar } from "./components/SearchBar";
import { ScrapeControl } from "./components/ScrapeControl";
import { AgentStatus } from "./components/AgentStatus";

const queryClient = new QueryClient();

function AppInner() {
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [source, setSource] = useState("");
  const [genre, setGenre] = useState("");
  const [sort, setSort] = useState("scraped_at:desc");
  const [activeFile, setActiveFile] = useState<MidiFile | null>(null);
  const [selectedFile, setSelectedFile] = useState<MidiFile | null>(null);
  const [showAdmin, setShowAdmin] = useState(false);

  const { data, isLoading } = useQuery({
    queryKey: ["midi", { page, search, source, genre, sort }],
    queryFn: () => api.getMidiFiles({ page, search, source, genre, sort, limit: 50 }),
    placeholderData: (prev) => prev,
  });

  const { data: stats } = useQuery({ queryKey: ["stats"], queryFn: api.getMidiStats });

  function handleSearch(s: string, src: string, g: string) {
    setSearch(s);
    setSource(src);
    setGenre(g);
    setPage(1);
  }

  function handlePlay(file: MidiFile) {
    setActiveFile(file);
  }

  const sources = stats?.by_source ? Object.keys(stats.by_source) : [];

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col" style={{ paddingBottom: activeFile ? "140px" : "0" }}>
      {/* Header */}
      <header className="bg-white border-b px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Music className="h-6 w-6 text-indigo-500" />
          <span className="font-bold text-lg">midi-haul</span>
          {stats && (
            <span className="text-sm text-gray-400 ml-2">{stats.total?.toLocaleString()} files · {stats.total_size_mb} MB</span>
          )}
        </div>
        <button onClick={() => setShowAdmin(!showAdmin)} className="text-sm text-gray-500 hover:text-gray-700">
          {showAdmin ? "Hide" : "Admin"}
        </button>
      </header>

      <div className="flex flex-1 overflow-hidden">
        {/* Main content */}
        <div className="flex-1 p-4 flex flex-col gap-3 overflow-auto">
          <SearchBar onSearch={handleSearch} sources={sources} />
          {isLoading ? (
            <div className="text-gray-400 text-center py-8">Loading…</div>
          ) : (
            <MidiTable
              files={data?.items || []}
              total={data?.total || 0}
              page={page}
              limit={50}
              onPageChange={setPage}
              onPlay={handlePlay}
              onSelect={setSelectedFile}
              activeId={activeFile?.id ?? null}
              sort={sort}
              onSort={setSort}
            />
          )}
        </div>

        {/* Metadata panel */}
        {selectedFile && (
          <MetadataPanel
            file={selectedFile}
            onClose={() => setSelectedFile(null)}
            onPlay={handlePlay}
          />
        )}

        {/* Admin panel */}
        {showAdmin && (
          <div className="w-80 border-l bg-white p-4 flex flex-col gap-4 overflow-y-auto">
            <h2 className="font-semibold">Admin</h2>
            <ScrapeControl />
            <AgentStatus />
          </div>
        )}
      </div>

      <MidiPlayer file={activeFile} onClose={() => setActiveFile(null)} />
    </div>
  );
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AppInner />
    </QueryClientProvider>
  );
}
