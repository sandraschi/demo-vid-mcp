import { Loader, Music2, Play, RefreshCw, Wifi, WifiOff } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
import { apiUrl } from "../lib/api";

const DEFAULT_PROMPT = "calm ambient instrumental background music, no vocals";

export default function Music() {
  const [detected, setDetected] = useState<boolean | null>(null);
  const [probing, setProbing] = useState(false);
  const [enabled, setEnabled] = useState(
    () => localStorage.getItem("demo_vid_music_enabled") === "1",
  );
  const [prompt, setPrompt] = useState(
    () => localStorage.getItem("demo_vid_music_prompt") || DEFAULT_PROMPT,
  );
  const [previewing, setPreviewing] = useState(false);
  const [previewError, setPreviewError] = useState<string | null>(null);
  const [previewBackend, setPreviewBackend] = useState<string | null>(null);
  const audioRef = useRef<HTMLAudioElement>(null);

  const probe = useCallback(async () => {
    setProbing(true);
    try {
      const r = await fetch(apiUrl("/api/health/music"));
      const d = await r.json();
      setDetected(!!d.detected);
    } catch {
      setDetected(false);
    } finally {
      setProbing(false);
    }
  }, []);

  useEffect(() => {
    probe();
  }, [probe]);

  const handleEnabledChange = useCallback((v: boolean) => {
    setEnabled(v);
    localStorage.setItem("demo_vid_music_enabled", v ? "1" : "0");
  }, []);

  const handlePromptChange = useCallback((v: string) => {
    setPrompt(v);
    localStorage.setItem("demo_vid_music_prompt", v);
  }, []);

  const handlePreview = useCallback(async () => {
    if (!prompt.trim()) return;
    setPreviewing(true);
    setPreviewError(null);
    setPreviewBackend(null);
    try {
      const r = await fetch(apiUrl("/api/music/preview"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt, duration: 15 }),
      });
      if (!r.ok) {
        const d = await r.json().catch(() => ({}));
        setPreviewError(d.error || `HTTP ${r.status}`);
        return;
      }
      setPreviewBackend(r.headers.get("X-Backend"));
      const blob = await r.blob();
      const blobUrl = URL.createObjectURL(blob);
      if (audioRef.current) {
        audioRef.current.src = blobUrl;
        audioRef.current.play().catch(() => {});
      }
    } catch (e) {
      setPreviewError(String(e));
    } finally {
      setPreviewing(false);
    }
  }, [prompt]);

  return (
    <div className="p-6 max-w-3xl mx-auto">
      <div className="flex items-center gap-3 mb-6">
        <Music2 className="h-7 w-7 text-amber-400" />
        <h1 className="text-xl font-bold text-zinc-100">Music</h1>
      </div>

      <div className="bg-zinc-900 rounded-lg p-4 border border-zinc-800 mb-4">
        <h2 className="text-sm font-semibold text-zinc-200 mb-2">songgeneration-mcp</h2>
        <div className="flex items-center gap-2 text-sm">
          {probing ? (
            <Loader className="h-4 w-4 animate-spin text-zinc-500" />
          ) : detected ? (
            <Wifi className="h-4 w-4 text-green-500" />
          ) : (
            <WifiOff className="h-4 w-4 text-zinc-600" />
          )}
          <span className="text-zinc-400">
            {probing ? "Probing..." : detected ? "Connected" : "Not detected"}
          </span>
          <button
            type="button"
            onClick={probe}
            disabled={probing}
            className="ml-auto p-1.5 rounded text-zinc-500 hover:text-white hover:bg-zinc-800 cursor-pointer"
          >
            <RefreshCw className={`h-4 w-4 ${probing ? "animate-spin" : ""}`} />
          </button>
        </div>
        {detected === false && (
          <p className="text-xs text-amber-500 mt-2">
            songgeneration-mcp tries Lyria 3 Pro, ACE-Step, Stable Audio and Studio SG2 in order -
            install at least one backend, or set SONGGENERATION_MCP_URL in .env if it's on a
            different port.
          </p>
        )}
      </div>

      <div className="bg-zinc-900 rounded-lg p-4 border border-zinc-800 mb-4">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-sm font-semibold text-zinc-200">Background Music</h2>
          <label className="flex items-center gap-2 text-sm text-zinc-300 cursor-pointer">
            <input
              type="checkbox"
              checked={enabled}
              onChange={(e) => handleEnabledChange(e.target.checked)}
            />
            Enabled
          </label>
        </div>
        <label className="block text-xs text-zinc-500 mb-1">Mood / style prompt</label>
        <textarea
          value={prompt}
          onChange={(e) => handlePromptChange(e.target.value)}
          rows={2}
          className="w-full bg-zinc-800 text-zinc-200 border border-zinc-700 rounded-md px-3 py-2 text-sm"
          placeholder={DEFAULT_PROMPT}
        />
        <p className="text-xs text-zinc-500 mt-2">
          When enabled, the Generate page mixes a generated track under the voiceover with automatic
          ducking (music drops while narration is speaking).
        </p>
      </div>

      <div className="bg-zinc-900 rounded-lg p-4 border border-zinc-800">
        <h2 className="text-sm font-semibold text-zinc-200 mb-3">Preview</h2>
        <p className="text-xs text-zinc-500 mb-3">
          Generates a real ~15s sample - can take up to a couple of minutes on first use.
        </p>
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={handlePreview}
            disabled={previewing || !prompt.trim()}
            className="flex items-center gap-2 px-4 py-2 bg-amber-600 text-white rounded-md text-sm font-medium hover:bg-amber-500 disabled:opacity-50 cursor-pointer"
          >
            <Play className="h-4 w-4" />
            {previewing ? "Generating..." : "Generate & Preview"}
          </button>
          <audio ref={audioRef} controls className="h-9" />
          {previewBackend && <span className="text-xs text-zinc-500">via {previewBackend}</span>}
        </div>
        {previewError && <p className="text-xs text-red-400 mt-2">{previewError}</p>}
      </div>
    </div>
  );
}
