import { useCallback, useEffect, useState } from "react";
import { Film, Camera, Music, Monitor } from "lucide-react";

export default function Dashboard() {
  const [stats, setStats] = useState<{ videos_served: number } | null>(null);
  const [backendOk, setBackendOk] = useState<boolean | null>(null);

  const refresh = useCallback(async () => {
    try {
      const r = await fetch("/api/health");
      if (r.ok) { const d = await r.json(); setStats(d); setBackendOk(true); return; }
      setBackendOk(false);
    } catch { setBackendOk(false); }
  }, []);

  useEffect(() => { refresh(); const t = setInterval(refresh, 15000); return () => clearInterval(t); }, [refresh]);

  return (
    <div data-testid="dashboard" className="p-6 max-w-5xl mx-auto">
      <div className="flex items-center gap-3 mb-6">
        <Film className="h-8 w-8 text-amber-400" />
        <div>
          <h1 className="text-2xl font-bold text-zinc-100">demo-vid-mcp</h1>
          <p className="text-sm text-zinc-500">Fleet intro video pipeline</p>
        </div>
        <div className="ml-auto flex items-center gap-2">
          <div data-testid="backend-dot" className={`w-2 h-2 rounded-full ${backendOk === null ? "bg-zinc-500" : backendOk ? "bg-green-500" : "bg-red-500"}`} />
          <span className="text-xs text-zinc-500">{backendOk === null ? "Connecting..." : backendOk ? "Connected" : "Offline"}</span>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-4 mb-6">
        <div data-testid="kpi-videos" className="bg-zinc-900 rounded-lg p-4 border border-zinc-800">
          <div className="flex items-center gap-2 text-zinc-400 mb-1"><Monitor className="h-4 w-4" /><span className="text-xs">Videos</span></div>
          <span className="text-2xl font-bold text-zinc-100">{stats?.videos_served ?? 0}</span>
        </div>
        <div className="bg-zinc-900 rounded-lg p-4 border border-zinc-800">
          <div className="flex items-center gap-2 text-zinc-400 mb-1"><Camera className="h-4 w-4" /><span className="text-xs">Fleet Services</span></div>
          <span className="text-2xl font-bold text-amber-400">6</span>
        </div>
        <div className="bg-zinc-900 rounded-lg p-4 border border-zinc-800">
          <div className="flex items-center gap-2 text-zinc-400 mb-1"><Music className="h-4 w-4" /><span className="text-xs">Voiceover</span></div>
          <span className="text-2xl font-bold text-green-400">Ready</span>
        </div>
      </div>

      <div className="bg-zinc-900 rounded-lg p-4 border border-zinc-800">
        <h2 className="text-sm font-semibold text-zinc-300 mb-2">Pipeline</h2>
        <div className="text-xs text-zinc-500 leading-relaxed">
          Script → Record (Playwright) + Voiceover (speech-mcp) → Compose (FFmpeg) → MP4
        </div>
      </div>
    </div>
  );
}
