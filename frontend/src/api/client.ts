export interface MidiFile {
  id: number;
  filename: string;
  source_url: string;
  page_url: string | null;
  source_name: string;
  title: string | null;
  composer: string | null;
  genre: string | null;
  bpm: number | null;
  duration_sec: number | null;
  track_count: number | null;
  time_signature: string | null;
  scraped_at: string;
  file_size: number | null;
  play_count: number;
}

export interface MidiFileList {
  items: MidiFile[];
  total: number;
  page: number;
  limit: number;
}

export interface AgentRunStep {
  id: number;
  tool_name: string;
  tool_input: string;
  tool_result: string | null;
  executed_at: string;
}

export interface AgentRun {
  id: number;
  started_at: string;
  finished_at: string | null;
  status: string;
  files_added: number;
  summary: string | null;
  steps: AgentRunStep[];
}

export interface ScrapeSource {
  id: number;
  name: string;
  display_name: string;
  last_scraped: string | null;
  file_count: number;
  error_count: number;
  enabled: boolean;
}

export interface MidiStats {
  total: number;
  total_size_mb: number;
  by_source?: Record<string, number>;
  [key: string]: unknown;
}

export interface JobStatus {
  status: string;
  files_added?: number;
  errors?: number;
  [key: string]: unknown;
}

const BASE = "/api";

async function fetchJSON<T>(input: RequestInfo | URL, init?: RequestInit): Promise<T> {
  const res = await fetch(input as RequestInfo, init);
  if (!res.ok) throw new Error(`HTTP ${res.status}: ${res.statusText}`);
  return res.json();
}

export const api = {
  getMidiFiles: async (params: Record<string, string | number | undefined>): Promise<MidiFileList> => {
    const q = new URLSearchParams();
    for (const [k, v] of Object.entries(params)) {
      if (v !== undefined && v !== "") q.set(k, String(v));
    }
    return fetchJSON<MidiFileList>(`${BASE}/midi?${q}`);
  },

  getMidiStats: async (): Promise<MidiStats> => {
    return fetchJSON<MidiStats>(`${BASE}/midi/stats`);
  },

  incrementPlay: async (id: number) => {
    await fetch(`${BASE}/midi/${id}/play`, { method: "POST" });
  },

  getSources: async (): Promise<ScrapeSource[]> => {
    return fetchJSON<ScrapeSource[]>(`${BASE}/scrape/sources`);
  },

  runScraper: async (source: string, maxFiles: number): Promise<{ job_id: string }> => {
    return fetchJSON<{ job_id: string }>(`${BASE}/scrape/run?source=${source}&max_files=${maxFiles}`, { method: "POST" });
  },

  getJobStatus: async (jobId: string): Promise<JobStatus> => {
    return fetchJSON<JobStatus>(`${BASE}/scrape/status/${jobId}`);
  },

  triggerAgent: async (): Promise<{ run_id: number }> => {
    return fetchJSON<{ run_id: number }>(`${BASE}/agent/run`, { method: "POST" });
  },

  getAgentRuns: async (): Promise<AgentRun[]> => {
    return fetchJSON<AgentRun[]>(`${BASE}/agent/runs`);
  },
};
