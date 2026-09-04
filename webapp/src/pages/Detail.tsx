import { apiUrl } from "@/lib/api";
import { useSearchParams } from "@/lib/routing";
import { useCallback, useEffect, useState } from "react";

export default function Detail() {
  const [params] = useSearchParams();
  const name = params.get("name") || "Unknown";
  const [videoUrl, setVideoUrl] = useState<string | null>(null);
  const [posterUrl, setPosterUrl] = useState<string | null>(null);
  const [vttUrl, setVttUrl] = useState<string | null>(null);
  const [generating, setGenerating] = useState(false);
  const [statusMsg, setStatusMsg] = useState<string | null>(null);

  const loadDetail = useCallback(() => {
    fetch(apiUrl("/api/videos"))
      .then((r) => r.json())
      .then((d) => {
        const found = (d.videos || []).find((v: any) => v.name === name || v.repo === name);
        if (found) {
          if (found.video_path) setVideoUrl(apiUrl(found.video_path));
          if (found.poster_path) setPosterUrl(apiUrl(found.poster_path));
          if (found.vtt_path) setVttUrl(apiUrl(found.vtt_path));
        }
      })
      .catch(() => {});
  }, [name]);

  useEffect(() => {
    loadDetail();
  }, [loadDetail]);

  const handleReGenerate = useCallback(async () => {
    setGenerating(true);
    setStatusMsg("Re-generating video...");
    try {
      const r = await fetch(apiUrl("/api/generate"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ repo: name }),
      });
      const d = await r.json();
      if (d.success) {
        setStatusMsg("Video re-generated successfully!");
        loadDetail();
      } else {
        setStatusMsg(`Failed: ${d.error}`);
      }
    } catch (e) {
      setStatusMsg(`Error: ${e}`);
    } finally {
      setGenerating(false);
    }
  }, [name, loadDetail]);

  return (
    <div data-testid="detail-page" className="p-6 max-w-4xl mx-auto">
      <h1 className="text-xl font-bold text-zinc-100 mb-4">{name}</h1>
      {videoUrl ? (
        <video
          controls
          className="w-full rounded-lg border border-zinc-800 mb-4"
          src={videoUrl}
          poster={posterUrl || undefined}
        >
          {vttUrl && <track src={vttUrl} kind="subtitles" srcLang="en" label="English" default />}
          Your browser does not support video playback.
        </video>
      ) : (
        <div className="aspect-video bg-zinc-900 rounded-lg border border-zinc-800 flex items-center justify-center text-zinc-600 mb-4">
          Video not found
        </div>
      )}
      <div className="flex items-center gap-3">
        <button
          type="button"
          onClick={handleReGenerate}
          disabled={generating}
          className="px-4 py-2 bg-amber-600 hover:bg-amber-500 text-white rounded-md text-sm font-medium disabled:opacity-50 cursor-pointer"
        >
          {generating ? "Re-generating..." : "Re-generate"}
        </button>
        {statusMsg && <span className="text-xs text-zinc-300">{statusMsg}</span>}
      </div>
    </div>
  );
}
