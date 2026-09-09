import { Loader, Mic, Play, RefreshCw, Wifi, WifiOff } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
import { apiUrl } from "../lib/api";

const VOICES = ["heart", "sky", "adam"] as const;

export default function Speech() {
  const [detected, setDetected] = useState<boolean | null>(null);
  const [probing, setProbing] = useState(false);
  const [voice, setVoice] = useState(() => localStorage.getItem("demo_vid_voice") || "heart");
  const [previewText, setPreviewText] = useState(
    "This is a preview of the demo-vid-mcp narration voice.",
  );
  const [previewing, setPreviewing] = useState(false);
  const [previewError, setPreviewError] = useState<string | null>(null);
  const audioRef = useRef<HTMLAudioElement>(null);

  const probe = useCallback(async () => {
    setProbing(true);
    try {
      const r = await fetch(apiUrl("/api/health/speech"));
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

  const handleVoiceChange = useCallback((v: string) => {
    setVoice(v);
    localStorage.setItem("demo_vid_voice", v);
  }, []);

  const handlePreview = useCallback(async () => {
    if (!previewText.trim()) return;
    setPreviewing(true);
    setPreviewError(null);
    try {
      const url = apiUrl(
        `/api/speech/preview?text=${encodeURIComponent(previewText)}&voice_id=${encodeURIComponent(voice)}`,
      );
      const r = await fetch(url);
      if (!r.ok) {
        const d = await r.json().catch(() => ({}));
        setPreviewError(d.error || `HTTP ${r.status}`);
        return;
      }
      const blob = await r.blob();
      const blobUrl = URL.createObjectURL(blob);
      if (audioRef.current) {
        audioRef.current.src = blobUrl;
        audioRef.current.play().catch((e) => setPreviewError(`Playback blocked: ${e}`));
      }
    } catch (e) {
      setPreviewError(String(e));
    } finally {
      setPreviewing(false);
    }
  }, [previewText, voice]);

  return (
    <div className="p-6 max-w-3xl mx-auto">
      <div className="flex items-center gap-3 mb-6">
        <Mic className="h-7 w-7 text-amber-400" />
        <h1 className="text-xl font-bold text-zinc-100">Speech</h1>
      </div>

      <div className="bg-zinc-900 rounded-lg p-4 border border-zinc-800 mb-4">
        <h2 className="text-sm font-semibold text-zinc-200 mb-2">speech-mcp</h2>
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
            Voiceover will be skipped (silent video with subtitles) until speech-mcp is reachable.
            Start it, or set SPEECH_MCP_URL in .env if it's on a different port.
          </p>
        )}
      </div>

      <div className="bg-zinc-900 rounded-lg p-4 border border-zinc-800 mb-4">
        <h2 className="text-sm font-semibold text-zinc-200 mb-3">Narration Voice</h2>
        <div className="flex gap-2">
          {VOICES.map((v) => (
            <button
              key={v}
              type="button"
              onClick={() => handleVoiceChange(v)}
              className={`px-4 py-2 rounded-md text-sm capitalize cursor-pointer border ${
                voice === v
                  ? "bg-amber-600 text-white border-amber-600"
                  : "bg-zinc-800 text-zinc-300 border-zinc-700 hover:text-white"
              }`}
            >
              {v}
            </button>
          ))}
        </div>
        <p className="text-xs text-zinc-500 mt-2">
          Used by the Generate page for auto-drafted videos. Choreography has its own voice picker
          per script.
        </p>
      </div>

      <div className="bg-zinc-900 rounded-lg p-4 border border-zinc-800">
        <h2 className="text-sm font-semibold text-zinc-200 mb-3">Preview</h2>
        <textarea
          value={previewText}
          onChange={(e) => setPreviewText(e.target.value)}
          rows={3}
          className="w-full bg-zinc-800 text-zinc-200 border border-zinc-700 rounded-md px-3 py-2 text-sm mb-3"
        />
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={handlePreview}
            disabled={previewing || !previewText.trim()}
            className="flex items-center gap-2 px-4 py-2 bg-amber-600 text-white rounded-md text-sm font-medium hover:bg-amber-500 disabled:opacity-50 cursor-pointer"
          >
            <Play className="h-4 w-4" />
            {previewing ? "Generating..." : `Preview as ${voice}`}
          </button>
          <audio
            ref={audioRef}
            controls
            className="h-9"
            onError={() => setPreviewError("Audio failed to load (blocked or unsupported)")}
          />
        </div>
        {previewError && <p className="text-xs text-red-400 mt-2">{previewError}</p>}
      </div>
    </div>
  );
}
