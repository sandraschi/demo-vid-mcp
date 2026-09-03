import { Film, Play } from "lucide-react";
import { useCallback, useEffect, useState } from "react";

interface VideoItem {
  name: string;
  repo: string;
  size_kb: number;
  created: string;
}

export default function Gallery() {
  const [videos, setVideos] = useState<VideoItem[]>([]);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    try {
      const r = await fetch("/api/videos");
      if (r.ok) {
        const d = await r.json();
        setVideos(d.videos || []);
      }
    } catch {
      /* ignore */
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  return (
    <div data-testid="gallery-page" className="p-6 max-w-5xl mx-auto">
      <div className="flex items-center gap-3 mb-6">
        <Film className="h-7 w-7 text-amber-400" />
        <h1 className="text-xl font-bold text-zinc-100">Gallery</h1>
        <span className="text-sm text-zinc-500">{videos.length} videos</span>
      </div>

      {loading && <div className="text-center text-zinc-500 py-12">Loading...</div>}
      {!loading && videos.length === 0 && (
        <div className="text-center text-zinc-600 py-12">
          No videos yet. Generate one from the Generate page.
        </div>
      )}

      <div className="grid grid-cols-2 gap-4">
        {videos.map((v) => (
          <div
            key={v.name}
            className="bg-zinc-900 rounded-lg border border-zinc-800 overflow-hidden hover:border-zinc-700 transition-colors"
          >
            <div className="aspect-video bg-zinc-800 flex items-center justify-center text-zinc-600 relative">
              <div className="absolute inset-0 flex items-center justify-center">
                <Play className="h-10 w-10 text-zinc-600" />
              </div>
            </div>
            <div className="p-3">
              <div className="text-sm font-medium text-zinc-200 truncate">{v.name}</div>
              <div className="text-xs text-zinc-500 mt-1">
                {v.repo} · {v.size_kb} KB
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
