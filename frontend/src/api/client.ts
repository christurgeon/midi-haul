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

const BASE = "/api";

export const api = {
  getMidiFiles: async (params: Record<string, string | number | undefined>): Promise<MidiFileList> => {
    const q = new URLSearchParams();
    for (const [k, v] of Object.entries(params)) {
      if (v !== undefined && v !== "") q.set(k, String(v));
    }
    const res = await fetch(`${BASE}/midi?${q}`);
    return res.json();
  },

  getMidiStats: async () => {
    const res = await fetch(`${BASE}/midi/stats`);
    return res.json();
  },

  incrementPlay: async (id: number) => {
    await fetch(`${BASE}/midi/${id}/play`, { method: "POST" });
  },

  getSources: async (): Promise<ScrapeSource[]> => {
    const res = await fetch(`${BASE}/scrape/sources`);
    return res.json();
  },

  runScraper: async (source: string, maxFiles: number): Promise<{ job_id: string }> => {
    const res = await fetch(`${BASE}/scrape/run?source=${source}&max_files=${maxFiles}`, { method: "POST" });
    return res.json();
  },

  getJobStatus: async (jobId: string) => {
    const res = await fetch(`${BASE}/scrape/status/${jobId}`);
    return res.json();
  },

  triggerAgent: async (): Promise<{ run_id: number }> => {
    const res = await fetch(`${BASE}/agent/run`, { method: "POST" });
    return res.json();
  },

  getAgentRuns: async (): Promise<AgentRun[]> => {
    const res = await fetch(`${BASE}/agent/runs`);
    return res.json();
  },
};
