import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Play, RefreshCw } from "lucide-react";
import { api } from "../api/client";

export function ScrapeControl() {
  const [source, setSource] = useState("bitmidi");
  const [maxFiles, setMaxFiles] = useState(50);
  const [jobId, setJobId] = useState<string | null>(null);

  const { data: sources } = useQuery({ queryKey: ["sources"], queryFn: api.getSources });

  const { data: jobStatus } = useQuery({
    queryKey: ["job", jobId],
    queryFn: () => api.getJobStatus(jobId!),
    enabled: !!jobId,
    refetchInterval: (q) => {
      const status = (q.state.data as any)?.status;
      return status === "running" ? 1000 : false;
    },
  });

  async function startScrape() {
    const { job_id } = await api.runScraper(source, maxFiles);
    setJobId(job_id);
  }

  const running = jobStatus?.status === "running";

  return (
    <div className="border rounded p-4 flex flex-col gap-3">
      <h3 className="font-semibold text-sm">Run Scraper</h3>
      <div className="flex gap-2 flex-wrap items-end">
        <div>
          <label className="text-xs text-gray-500 block mb-1">Source</label>
          <select
            className="border rounded px-2 py-1.5 text-sm"
            value={source}
            onChange={(e) => setSource(e.target.value)}
          >
            {(sources || []).map((s) => (
              <option key={s.name} value={s.name}>{s.display_name}</option>
            ))}
          </select>
        </div>
        <div>
          <label className="text-xs text-gray-500 block mb-1">Max files</label>
          <input
            type="number"
            className="border rounded px-2 py-1.5 text-sm w-20"
            value={maxFiles}
            onChange={(e) => setMaxFiles(Number(e.target.value))}
            min={1}
            max={1000}
          />
        </div>
        <button
          onClick={startScrape}
          disabled={running}
          className="flex items-center gap-1 px-3 py-1.5 bg-indigo-500 text-white text-sm rounded hover:bg-indigo-600 disabled:opacity-50"
        >
          {running ? <RefreshCw className="h-4 w-4 animate-spin" /> : <Play className="h-4 w-4" />}
          {running ? "Running…" : "Start"}
        </button>
      </div>
      {jobStatus && (
        <div className="text-sm text-gray-600">
          Status: <span className={jobStatus.status === "completed" ? "text-green-600" : jobStatus.status === "failed" ? "text-red-500" : "text-indigo-500"}>{jobStatus.status}</span>
          {" · "}{jobStatus.files_added ?? 0} added · {jobStatus.errors ?? 0} errors
        </div>
      )}
    </div>
  );
}
