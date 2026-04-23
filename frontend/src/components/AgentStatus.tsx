import { useState, useEffect, useRef } from "react";
import { Bot, RefreshCw } from "lucide-react";
import { api } from "../api/client";

interface LiveStep {
  id: number;
  tool_name: string;
  tool_input: string;
  tool_result: string | null;
  executed_at: string;
}

export function AgentStatus() {
  const [_runId, setRunId] = useState<number | null>(null);
  const [steps, setSteps] = useState<LiveStep[]>([]);
  const [status, setStatus] = useState<string | null>(null);
  const [running, setRunning] = useState(false);
  const esRef = useRef<EventSource | null>(null);

  async function startRun() {
    setSteps([]);
    setStatus("running");
    setRunning(true);
    try {
      const { run_id } = await api.triggerAgent();
      setRunId(run_id);

      const es = new EventSource(`/api/agent/runs/${run_id}/stream`);
      esRef.current = es;

      es.onmessage = (e) => {
        const data = JSON.parse(e.data);
        if (data.done) {
          setStatus(data.status);
          setRunning(false);
          es.close();
        } else if (data.error) {
          setStatus("failed");
          setRunning(false);
          es.close();
        } else {
          setSteps((prev) => [...prev, data as LiveStep]);
        }
      };

      es.onerror = () => {
        setStatus("failed");
        setRunning(false);
        es.close();
      };
    } catch (e) {
      console.error("Failed to start agent run:", e);
      setStatus("failed");
      setRunning(false);
    }
  }

  useEffect(() => () => esRef.current?.close(), []);

  return (
    <div className="border rounded p-4 flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <h3 className="font-semibold text-sm flex items-center gap-1"><Bot className="h-4 w-4" /> Agent</h3>
        <button
          onClick={startRun}
          disabled={running}
          className="flex items-center gap-1 px-3 py-1.5 bg-violet-500 text-white text-sm rounded hover:bg-violet-600 disabled:opacity-50"
        >
          {running ? <RefreshCw className="h-4 w-4 animate-spin" /> : <Bot className="h-4 w-4" />}
          {running ? "Running…" : "Run Agent"}
        </button>
      </div>
      {status && (
        <p className="text-xs text-gray-500">Status: <span className={status === "completed" ? "text-green-600" : status === "failed" ? "text-red-500" : "text-violet-500"}>{status}</span></p>
      )}
      {steps.length > 0 && (
        <div className="max-h-64 overflow-y-auto flex flex-col gap-1">
          {steps.map((s) => (
            <div key={s.id} className="text-xs border rounded p-2 bg-gray-50">
              <div className="font-medium text-violet-700">{s.tool_name}</div>
              <div className="text-gray-500 truncate">{s.tool_input}</div>
              {s.tool_result && <div className="text-gray-400 truncate">→ {s.tool_result}</div>}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
