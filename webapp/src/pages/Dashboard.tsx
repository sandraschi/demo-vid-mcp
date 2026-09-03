import { Camera, Film, Monitor, Music } from "lucide-react";
import { useCallback, useEffect, useState } from "react";

export default function Dashboard() {
  const [stats, setStats] = useState<{
    videos_served: number;
    version: string;
  } | null>(null);
  const [backendOk, setBackendOk] = useState<boolean | null>(null);
  const [speechOk, setSpeechOk] = useState<boolean | null>(null);
  const [videoCount, setVideoCount] = useState(0);

  const refresh = useCallback(async () => {
    try {
      const r = await fetch("/api/health");
      if (r.ok) {
        const d = await r.json();
        setStats(d);
        setBackendOk(true);
      } else {
        setBackendOk(false);
      }
    } catch {
      setBackendOk(false);
    }

    try {
      const d = await fetch("/api/videos").then((r) => r.json());
      const count = (d.videos || d.repos || []).length;
      setVideoCount(count);
    } catch {
      /* ignore */
    }

    try {
      const r = await fetch("/api/health/speech").then((r) => r.json());
      setSpeechOk(r.detected || false);
    } catch {
      setSpeechOk(false);
    }
  }, []);

  useEffect(() => {
    refresh();
    const t = setInterval(refresh, 10000);
    return () => clearInterval(t);
  }, [refresh]);

  return (
    <div data-testid="dashboard" className="p-6 max-w-5xl mx-auto">
      <div className="flex items-center gap-3 mb-6">
        <Film className="h-8 w-8 text-amber-400" />
        <div>
          <h1 className="text-2xl font-bold text-zinc-100">demo-vid-mcp</h1>
          <p className="text-sm text-zinc-400">
            Fleet intro video pipeline {stats?.version ? `v${stats.version}` : "v0.2.0"}
          </p>
        </div>
        <div className="ml-auto flex items-center gap-2">
          <div
            data-testid="backend-dot"
            className={`w-2 h-2 rounded-full ${
              backendOk === null ? "bg-zinc-500" : backendOk ? "bg-green-500" : "bg-red-500"
            }`}
          />
          <span className="text-sm text-zinc-400">
            {backendOk === null ? "Connecting..." : backendOk ? "Connected" : "Offline"}
          </span>
        </div>
      </div>

      {backendOk === false && (
        <div className="mb-6 p-4 rounded-lg bg-red-950/40 border border-red-800/60 text-sm text-red-200 flex items-center justify-between">
          <div>
            <strong>Backend service is offline on port 11134.</strong>
            <p className="text-xs text-red-300 mt-1">
              Start the backend with{" "}
              <code className="bg-zinc-900 px-1.5 py-0.5 rounded border border-red-900 font-mono text-red-200">
                just serve
              </code>{" "}
              or{" "}
              <code className="bg-zinc-900 px-1.5 py-0.5 rounded border border-red-900 font-mono text-red-200">
                .\start.ps1
              </code>{" "}
              to enable video generation and API routes.
            </p>
          </div>
          <button
            type="button"
            onClick={() => refresh()}
            className="px-3 py-1.5 bg-red-900/60 hover:bg-red-800 text-xs text-white rounded border border-red-700 cursor-pointer shrink-0 ml-4"
          >
            Retry Connection
          </button>
        </div>
      )}

      <div className="grid grid-cols-4 gap-4 mb-6">
        <div data-testid="kpi-videos" className="bg-zinc-900 rounded-lg p-4 border border-zinc-800">
          <div className="flex items-center gap-2 text-zinc-400 mb-1">
            <Monitor className="h-4 w-4" />
            <span className="text-sm">Videos</span>
          </div>
          <span className="text-2xl font-bold text-zinc-100">{videoCount}</span>
        </div>
        <div className="bg-zinc-900 rounded-lg p-4 border border-zinc-800">
          <div className="flex items-center gap-2 text-zinc-400 mb-1">
            <Camera className="h-4 w-4" />
            <span className="text-sm">Depot</span>
          </div>
          <span className="text-2xl font-bold text-amber-400">
            {stats?.videos_served ?? videoCount} videos
          </span>
        </div>
        <div className="bg-zinc-900 rounded-lg p-4 border border-zinc-800">
          <div className="flex items-center gap-2 text-zinc-400 mb-1">
            <Music className="h-4 w-4" />
            <span className="text-sm">Voiceover</span>
          </div>
          <span
            className={`text-2xl font-bold ${
              speechOk === null ? "text-zinc-500" : speechOk ? "text-green-400" : "text-red-400"
            }`}
          >
            {speechOk === null ? "..." : speechOk ? "Ready" : "Offline"}
          </span>
        </div>
        <div className="bg-zinc-900 rounded-lg p-4 border border-zinc-800">
          <div className="flex items-center gap-2 text-zinc-400 mb-1">
            <Film className="h-4 w-4" />
            <span className="text-sm">Pipeline</span>
          </div>
          <span className="text-2xl font-bold text-amber-400">
            {stats?.version ? `v${stats.version}` : "v0.2"}
          </span>
        </div>
      </div>

      <div className="bg-zinc-900 rounded-lg p-4 border border-zinc-800">
        <h2 className="text-sm font-semibold text-zinc-300 mb-2">Pipeline</h2>
        <div className="text-sm text-zinc-400 leading-relaxed">
          Script → Auto-start target → Record (Playwright) + Voiceover (speech-mcp) → Compose
          (FFmpeg) → MP4
        </div>
      </div>
    </div>
  );
}
