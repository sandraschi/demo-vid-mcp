import { useCallback, useEffect, useState } from "react";
import { useSearchParams } from "@/lib/routing";

export default function Detail() {
  const [params] = useSearchParams();
  const name = params.get("name") || "Unknown";
  const [videoUrl, setVideoUrl] = useState<string | null>(null);

  useEffect(() => {
    fetch(`/api/videos`)
      .then(r => r.json())
      .then(d => {
        const found = (d.videos || []).find((v: any) => v.name === name);
        if (found) setVideoUrl(found.path);
      })
      .catch(() => {});
  }, [name]);

  const handleReGenerate = useCallback(async () => {
    alert("Re-generate not yet implemented — use demo_vid_generate MCP tool");
  }, []);

  return (
    <div data-testid="detail-page" className="p-6 max-w-4xl mx-auto">
      <h1 className="text-xl font-bold text-zinc-100 mb-4">{name}</h1>
      {videoUrl ? (
        <video controls className="w-full rounded-lg border border-zinc-800 mb-4" src={videoUrl}>
          Your browser does not support video playback.
        </video>
      ) : (
        <div className="aspect-video bg-zinc-900 rounded-lg border border-zinc-800 flex items-center justify-center text-zinc-600 mb-4">
          Video not found
        </div>
      )}
      <div className="flex gap-3">
        <button onClick={handleReGenerate} className="px-4 py-2 bg-zinc-800 text-zinc-200 rounded-md text-sm hover:bg-zinc-700 cursor-pointer">Re-generate</button>
      </div>
    </div>
  );
}
