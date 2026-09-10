import { Camera, Film, Loader2, Monitor, Music, RotateCw } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { apiUrl } from "../lib/api";
import { useBackendStore } from "../store/backend";

export default function Dashboard() {
  const [stats, setStats] = useState<{
    videos_served: number;
    version: string;
  } | null>(null);
  const backendOk = useBackendStore((s) => s.backendOk);
  const restarting = useBackendStore((s) => s.restarting);
  const restart = useBackendStore((s) => s.restart);
  const [speechOk, setSpeechOk] = useState<boolean | null>(null);
  const [videoCount, setVideoCount] = useState(0);

  const refresh = useCallback(async () => {
    useBackendStore.getState().refresh();
    try {
      const r = await fetch(apiUrl("/api/health"));
      if (r.ok) {
        const d = await r.json();
        setStats(d);
      }
    } catch {
      /* backend status already tracked by the shared store */
    }

    try {
      const d = await fetch(apiUrl("/api/videos")).then((r) => r.json());
      const count = (d.videos || d.repos || []).length;
      setVideoCount(count);
    } catch {
      /* ignore */
    }

    try {
      const r = await fetch(apiUrl("/api/health/speech")).then((r) => r.json());
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
      <div
        data-testid="dashboard-hero"
        className="mb-6 p-5 rounded-lg bg-zinc-900 border border-zinc-800"
      >
        <div className="flex items-center gap-3">
          <Film className="h-8 w-8 text-amber-400 shrink-0" />
          <div>
            <h1 className="text-2xl font-bold text-zinc-100">demo-vid-mcp</h1>
            <p className="text-sm text-zinc-300">
              Fleet intro video pipeline v{stats?.version ?? "0.4.0"}
            </p>
          </div>
          <div className="ml-auto flex items-center gap-2">
            <div
              data-testid="backend-dot"
              className={`w-2 h-2 rounded-full ${
                backendOk === null ? "bg-zinc-500" : backendOk ? "bg-green-500" : "bg-red-500"
              }`}
            />
            <span className="text-sm text-zinc-300">
              {backendOk === null ? "Connecting..." : backendOk ? "Connected" : "Offline"}
            </span>
          </div>
        </div>
        <p className="mt-3 text-sm text-zinc-300 leading-relaxed">
          Turns a script into an intro video: Playwright records the target UI, speech-mcp voices
          the narration, and FFmpeg composes the final MP4. New here? Open{" "}
          <span className="font-semibold text-zinc-100">Generate</span> to render your first video
          from a script, or <span className="font-semibold text-zinc-100">Scripts</span> to write
          one first.
        </p>
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
          <div className="flex items-center gap-2 shrink-0 ml-4">
            <button
              type="button"
              onClick={() => refresh()}
              className="px-3 py-1.5 bg-red-900/60 hover:bg-red-800 text-sm text-white rounded border border-red-700 cursor-pointer"
            >
              Retry Connection
            </button>
            <button
              type="button"
              data-testid="restart-backend"
              onClick={() => restart()}
              disabled={restarting}
              className="px-3 py-1.5 bg-red-900/60 hover:bg-red-800 disabled:opacity-60 disabled:cursor-not-allowed text-sm text-white rounded border border-red-700 cursor-pointer flex items-center gap-1.5"
              title="Restart the bundled backend (Tauri desktop app only)"
            >
              {restarting ? (
                <Loader2 className="h-3.5 w-3.5 animate-spin" />
              ) : (
                <RotateCw className="h-3.5 w-3.5" />
              )}
              {restarting ? "Restarting..." : "Restart Backend"}
            </button>
          </div>
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
          <span className="text-2xl font-bold text-amber-400">v{stats?.version ?? "0.4.0"}</span>
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
