import { RefreshCw, Terminal } from "lucide-react";
import { useCallback, useEffect, useState } from "react";

interface LogEntry {
  time: string;
  level: string;
  source: string;
  message: string;
}

const LEVELS = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"];

export default function Logs() {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [level, setLevel] = useState("INFO");
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({ limit: "100", level, search });
      const r = await fetch(`/api/logs?${params}`);
      if (r.ok) {
        const d = await r.json();
        setLogs(d.logs || []);
      }
    } catch {
      /* ignore */
    } finally {
      setLoading(false);
    }
  }, [level, search]);

  useEffect(() => {
    load();
    const t = setInterval(load, 5000);
    return () => clearInterval(t);
  }, [load]);

  const levelColor = (lvl: string) => {
    switch (lvl) {
      case "ERROR":
        return "text-red-400";
      case "WARNING":
        return "text-amber-400";
      case "CRITICAL":
        return "text-red-500 font-bold";
      default:
        return "text-zinc-400";
    }
  };

  return (
    <div className="p-6 max-w-5xl mx-auto">
      <div className="flex items-center gap-3 mb-4">
        <Terminal className="h-7 w-7 text-amber-400" />
        <h1 className="text-xl font-bold text-zinc-100">Logs</h1>
        <button
          onClick={load}
          disabled={loading}
          className="ml-auto p-2 rounded text-zinc-400 hover:text-white hover:bg-zinc-800 cursor-pointer"
          title="Refresh"
        >
          <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
        </button>
      </div>

      <div className="flex gap-3 mb-4">
        <select
          value={level}
          onChange={(e) => setLevel(e.target.value)}
          className="bg-zinc-800 text-zinc-200 border border-zinc-700 rounded-md px-3 py-1.5 text-xs"
        >
          {LEVELS.map((l) => (
            <option key={l} value={l}>
              {l}
            </option>
          ))}
        </select>
        <input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search logs..."
          className="flex-1 bg-zinc-800 text-zinc-200 border border-zinc-700 rounded-md px-3 py-1.5 text-xs"
        />
      </div>

      <div className="bg-zinc-950 rounded-lg border border-zinc-800 overflow-hidden font-mono text-xs">
        {logs.length === 0 && !loading && (
          <div className="p-6 text-center text-zinc-600">No log entries match the filter.</div>
        )}
        {logs.map((e, i) => (
          <div
            key={i}
            className="flex px-3 py-1.5 border-b border-zinc-900 last:border-0 hover:bg-zinc-900/50"
          >
            <span className="text-zinc-600 w-20 shrink-0">{e.time?.slice(11, 19)}</span>
            <span className={`w-16 shrink-0 ${levelColor(e.level)}`}>{e.level}</span>
            <span className="text-zinc-600 w-28 shrink-0 truncate mr-2">{e.source}</span>
            <span className="text-zinc-300 truncate">{e.message}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
