import {
  AlertCircle,
  CheckCircle2,
  Clock,
  ListOrdered,
  Play,
  RefreshCw,
  XCircle,
} from "lucide-react";
import { useCallback, useEffect, useState } from "react";

interface Job {
  id: string;
  repo: string;
  script_yaml?: string;
  aspect_ratio: string;
  resolution: string;
  status: "pending" | "running" | "completed" | "failed" | "canceled";
  created_at: number;
  started_at?: number;
  completed_at?: number;
  result?: any;
  error?: string;
}

export default function Queue() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(false);

  const loadQueue = useCallback(async () => {
    try {
      const r = await fetch("/api/queue");
      if (r.ok) {
        const d = await r.json();
        setJobs(d.jobs || []);
      }
    } catch {
      /* ignore */
    }
  }, []);

  useEffect(() => {
    loadQueue();
    const t = setInterval(loadQueue, 3000);
    return () => clearInterval(t);
  }, [loadQueue]);

  const handleCancel = async (jobId: string) => {
    try {
      await fetch(`/api/queue/${jobId}`, { method: "DELETE" });
      loadQueue();
    } catch {
      /* ignore */
    }
  };

  const pending = jobs.filter((j) => j.status === "pending").length;
  const running = jobs.filter((j) => j.status === "running").length;
  const completed = jobs.filter((j) => j.status === "completed").length;

  return (
    <div className="p-6 max-w-5xl mx-auto">
      <div className="flex items-center gap-3 mb-6">
        <ListOrdered className="h-7 w-7 text-amber-400" />
        <div>
          <h1 className="text-xl font-bold text-zinc-100">Generation Queue</h1>
          <p className="text-xs text-zinc-400">Persistent FIFO background video rendering queue</p>
        </div>
        <button
          type="button"
          onClick={() => {
            setLoading(true);
            loadQueue().finally(() => setLoading(false));
          }}
          className="ml-auto flex items-center gap-1.5 px-3 py-1.5 bg-zinc-800 hover:bg-zinc-700 text-xs text-zinc-200 rounded border border-zinc-700 cursor-pointer"
        >
          <RefreshCw className={`h-3.5 w-3.5 ${loading ? "animate-spin" : ""}`} />
          Refresh
        </button>
      </div>

      {/* KPI Stats */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        <div className="bg-zinc-900 rounded-lg p-3 border border-zinc-800">
          <span className="text-xs text-zinc-400 block mb-1">Active</span>
          <span className="text-xl font-bold text-amber-400">{running}</span>
        </div>
        <div className="bg-zinc-900 rounded-lg p-3 border border-zinc-800">
          <span className="text-xs text-zinc-400 block mb-1">Pending</span>
          <span className="text-xl font-bold text-zinc-300">{pending}</span>
        </div>
        <div className="bg-zinc-900 rounded-lg p-3 border border-zinc-800">
          <span className="text-xs text-zinc-400 block mb-1">Completed</span>
          <span className="text-xl font-bold text-green-400">{completed}</span>
        </div>
        <div className="bg-zinc-900 rounded-lg p-3 border border-zinc-800">
          <span className="text-xs text-zinc-400 block mb-1">Total History</span>
          <span className="text-xl font-bold text-zinc-100">{jobs.length}</span>
        </div>
      </div>

      {jobs.length === 0 ? (
        <div className="bg-zinc-900 rounded-lg p-8 border border-zinc-800 text-center text-zinc-400">
          Queue is empty. Enqueue video generation jobs from the{" "}
          <strong className="text-amber-400">Generate</strong> page or via the{" "}
          <code className="bg-zinc-800 px-1 py-0.5 rounded font-mono text-zinc-300">
            demo_vid_generate
          </code>{" "}
          MCP tool.
        </div>
      ) : (
        <div className="bg-zinc-900 rounded-lg border border-zinc-800 overflow-hidden">
          <table className="w-full text-left text-sm">
            <thead className="bg-zinc-950/60 border-b border-zinc-800 text-xs text-zinc-400">
              <tr>
                <th className="py-2.5 px-4">Job ID</th>
                <th className="py-2.5 px-4">Repo</th>
                <th className="py-2.5 px-4">Aspect</th>
                <th className="py-2.5 px-4">Status</th>
                <th className="py-2.5 px-4">Created</th>
                <th className="py-2.5 px-4 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-800/60">
              {jobs.map((j) => (
                <tr key={j.id} className="hover:bg-zinc-800/40">
                  <td className="py-2.5 px-4 font-mono text-xs text-zinc-300">{j.id}</td>
                  <td className="py-2.5 px-4 font-medium text-zinc-100">{j.repo}</td>
                  <td className="py-2.5 px-4">
                    <span className="px-1.5 py-0.5 rounded text-xs bg-zinc-800 text-zinc-300 border border-zinc-700 font-mono">
                      {j.aspect_ratio || "16:9"}
                    </span>
                  </td>
                  <td className="py-2.5 px-4">
                    {j.status === "running" && (
                      <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs bg-amber-500/20 text-amber-300 border border-amber-500/40">
                        <RefreshCw className="h-3 w-3 animate-spin" />
                        Rendering
                      </span>
                    )}
                    {j.status === "pending" && (
                      <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs bg-zinc-700/40 text-zinc-300 border border-zinc-600">
                        <Clock className="h-3 w-3" />
                        Queued
                      </span>
                    )}
                    {j.status === "completed" && (
                      <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs bg-green-500/20 text-green-300 border border-green-500/40">
                        <CheckCircle2 className="h-3 w-3" />
                        Done
                      </span>
                    )}
                    {j.status === "failed" && (
                      <span
                        className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs bg-red-500/20 text-red-300 border border-red-500/40"
                        title={j.error || "Failed"}
                      >
                        <AlertCircle className="h-3 w-3" />
                        Failed
                      </span>
                    )}
                    {j.status === "canceled" && (
                      <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs bg-zinc-800 text-zinc-400">
                        <XCircle className="h-3 w-3" />
                        Canceled
                      </span>
                    )}
                  </td>
                  <td className="py-2.5 px-4 text-xs text-zinc-400">
                    {new Date(j.created_at * 1000).toLocaleTimeString()}
                  </td>
                  <td className="py-2.5 px-4 text-right">
                    {j.status === "pending" && (
                      <button
                        type="button"
                        onClick={() => handleCancel(j.id)}
                        className="px-2 py-1 text-xs text-red-400 hover:text-red-300 hover:bg-red-950/40 rounded border border-red-900 cursor-pointer"
                      >
                        Cancel
                      </button>
                    )}
                    {j.status === "completed" && j.result?.video_path && (
                      <a
                        href="/#depot"
                        className="inline-flex items-center gap-1 px-2 py-1 text-xs text-amber-400 hover:text-amber-300 hover:bg-zinc-800 rounded border border-zinc-700"
                      >
                        <Play className="h-3 w-3" />
                        View
                      </a>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
