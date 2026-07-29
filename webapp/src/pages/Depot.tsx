import { useCallback, useEffect, useState } from "react";
import { Play, RotateCcw, Code, Trash2, FileDown } from "lucide-react";

interface DepotEntry {
  repo: string; name: string; video_path: string;
  size_kb: number; created: string;
  has_script: boolean; script: string | null;
}

function getUrlParam(key: string): string {
  if (typeof window === "undefined") return "";
  return new URLSearchParams(window.location.search).get(key) || "";
}

function setUrlParam(key: string, value: string) {
  const sp = new URLSearchParams(window.location.search);
  if (value) sp.set(key, value); else sp.delete(key);
  const qs = sp.toString();
  window.history.replaceState({}, "", qs ? `?${qs}` : window.location.pathname);
}

const CATEGORIES: Record<string, string[]> = {
  "Research & Knowledge": ["arxiv-mcp", "calibre-mcp", "llm-txt-mcp", "notebooklm-fleet-mcp", "readly-mcp", "tvtropes-mcp"],
  "Media & Creativity": ["blender-mcp", "gimp-mcp", "inkscape-mcp", "davinci-resolve-mcp", "vroidstudio-mcp", "resonite-mcp", "godot-mcp", "unity3d-mcp", "comfyops-mcp", "suno-mcp", "songgeneration-mcp", "audiotool-nexus-mcp", "virtualdj-mcp", "reaper-mcp", "obs-mcp", "butterchurn-mcp"],
  "Communication": ["email-mcp", "discord-mcp", "mastodon-mcp", "bluesky-mcp", "alexa-mcp", "telephony-mcp", "chitchat"],
  "Development & DevOps": ["git-github-mcp", "docker-mcp", "filesystem-mcp", "web-development-mcp", "database-operations-mcp", "browser-mcp", "windows-operations-mcp", "meta_mcp", "fleetwatcher-mcp", "monitoring-mcp"],
  "CAD & Design": ["freecad-mcp", "qcad-mcp", "kicad-mcp", "chip-design-mcp", "codecad-mcp", "sketchboard-excalidraw-mcp"],
  "Automation & Control": ["multi-backup-mcp", "devices-mcp", "home-assistant-mcp", "tapo-mcp", "netatmo-weather-mcp", "pdf-mcp", "system-admin-mcp", "disk-usage-mcp"],
  "Robotics & Simulation": ["yahboom-mcp", "robotics-mcp", "gazebo-mcp", "mujoco-mcp", "ros-mcp", "unitree-mcp", "isaac-mcp", "limx-robotics-mcp"],
  "Productivity & MCP": ["advanced-memory-mcp", "bookmarks-mcp", "notion-mcp", "obsidian-mcp", "onenote-mcp", "mcp-studio", "depot-mcp", "speech-mcp", "glama-status-mcp", "toolbench-mcp"],
};

export default function Depot() {
  const [entries, setEntries] = useState<DepotEntry[]>([]);
  const [playing, setPlaying] = useState<string | null>(null);
  const [expanded, setExpanded] = useState<string | null>(null);
  const [regenBusy, setRegenBusy] = useState<string | null>(null);
  const [regenResult, setRegenResult] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      const r = await fetch("/api/depot");
      if (r.ok) { const d = await r.json(); setEntries(d.repos || []); }
    } catch { /* ignore */ }
  }, []);

  useEffect(() => { load();   }, [load]);

  const handleInsert = useCallback(async (repo: string) => {
    try {
      const r = await fetch(`/api/videos/${encodeURIComponent(repo)}/insert`, { method: "POST" });
      const d = await r.json();
      setRegenResult(d.message || "Inserted");
      load();
    } catch { /* ignore */ }
  }, [load]);

  const handleDelete = useCallback(async (repo: string) => {
    if (!confirm(`Delete all videos for ${repo}?`)) return;
    try {
      await fetch(`/api/videos/${encodeURIComponent(repo)}`, { method: "DELETE" });
      load();
    } catch { /* ignore */ }
  }, [load]);

  const grouped = entries.reduce((acc, e) => {
    const cat = Object.entries(CATEGORIES).find(([, repos]) => repos.includes(e.repo))?.[0] || "Other";
    if (!acc[cat]) acc[cat] = [];
    acc[cat].push(e);
    return acc;
  }, {} as Record<string, DepotEntry[]>);

  // URL param filter
  const [repoFilter, setRepoFilter] = useState(() => getUrlParam("repo"));
  const allRepos = [...new Set(entries.map(e => e.repo))].sort();

  useEffect(() => {
    if (repoFilter) setUrlParam("repo", repoFilter);
    else setUrlParam("repo", "");
  }, [repoFilter]);

  const filteredEntries = repoFilter
    ? entries.filter(e => e.repo === repoFilter)
    : entries;

  const filteredGrouped = repoFilter
    ? (() => { const cat = Object.entries(CATEGORIES).find(([, repos]) => repos.includes(repoFilter))?.[0] || "Other";
               return { [cat]: filteredEntries }; })()
    : grouped;

  const handleRebuild = useCallback(async (entry: DepotEntry) => {
    setRegenBusy(entry.repo);
    setRegenResult(null);
    try {
      const r = await fetch("/api/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ repo: entry.repo, script_yaml: entry.script }),
      });
      const d = await r.json();
      setRegenResult(d.success ? `Rebuilt ${entry.repo}` : `Failed: ${d.error}`);
      load();
    } catch (e) {
      setRegenResult(`Error: ${e}`);
    } finally {
      setRegenBusy(null);
    }
  }, [load]);

  return (
    <div data-testid="depot-page" className="p-6 max-w-6xl mx-auto">
      <div className="flex items-center gap-3 mb-4">
        <h1 className="text-xl font-bold text-zinc-100">Depot</h1>
        <span className="text-sm text-zinc-500">{entries.length} videos</span>
        <div className="ml-auto w-48">
          <select value={repoFilter} onChange={e => setRepoFilter(e.target.value)}
            className="w-full bg-zinc-800 text-zinc-200 border border-zinc-700 rounded-md px-2 py-1.5 text-xs">
            <option value="">All repos</option>
            {allRepos.map(r => <option key={r} value={r}>{r}</option>)}
          </select>
        </div>
      </div>

      {regenResult && (
        <div className="bg-zinc-800 rounded-md p-3 mb-4 text-sm text-zinc-300 border border-zinc-700">{regenResult}</div>
      )}

      {Object.entries(filteredGrouped).map(([cat, vids]) => (
        <div key={cat} className="mb-6">
          <h2 className="text-sm font-semibold text-zinc-400 mb-2 uppercase tracking-wide">
            {cat} ({vids.length})
          </h2>
          <div className="grid grid-cols-2 gap-3">
            {vids.map((v) => (
              <div
                key={`${v.repo}-${v.name}`}
                className="bg-zinc-900 rounded-lg border border-zinc-800 overflow-hidden hover:border-zinc-700 transition-colors"
              >
                <div
                  className="aspect-video bg-zinc-800 flex items-center justify-center relative cursor-pointer group"
                  onClick={() => setPlaying(playing === v.video_path ? null : v.video_path)}
                >
                  {playing === v.video_path ? (
                    <video controls autoPlay className="absolute inset-0 w-full h-full" src={v.video_path}>
                      Your browser does not support video playback.
                    </video>
                  ) : (
                    <div className="absolute inset-0 flex items-center justify-center">
                      <div className="h-12 w-12 rounded-full bg-black/50 flex items-center justify-center group-hover:bg-amber-600/80 transition-colors">
                        <Play className="h-6 w-6 text-white ml-0.5" />
                      </div>
                    </div>
                  )}
                </div>
                <div className="p-3">
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="text-sm font-medium text-zinc-200 truncate">{v.repo}</div>
                      <div className="text-xs text-zinc-500">{v.size_kb} KB</div>
                    </div>
                    <div className="flex gap-2">
                      {v.has_script && (
                        <button
                          onClick={() => setExpanded(expanded === v.repo ? null : v.repo)}
                          className="p-1.5 rounded text-zinc-400 hover:text-white hover:bg-zinc-700 cursor-pointer"
                          title="Show script"
                        >
                          <Code className="h-3.5 w-3.5" />
                        </button>
                      )}
                      <button
                        onClick={() => handleRebuild(v)}
                        disabled={regenBusy === v.repo}
                        className="p-1.5 rounded text-zinc-400 hover:text-amber-400 hover:bg-zinc-700 disabled:opacity-50 cursor-pointer"
                        title="Rebuild"
                      >
                        <RotateCcw className={`h-3.5 w-3.5 ${regenBusy === v.repo ? "animate-spin" : ""}`} />
                      </button>
                      <button
                        onClick={() => handleInsert(v.repo)}
                        className="p-1.5 rounded text-zinc-400 hover:text-green-400 hover:bg-zinc-700 cursor-pointer"
                        title="Insert into repo README"
                      >
                        <FileDown className="h-3.5 w-3.5" />
                      </button>
                      <button
                        onClick={() => handleDelete(v.repo)}
                        className="p-1.5 rounded text-zinc-400 hover:text-red-400 hover:bg-zinc-700 cursor-pointer"
                        title="Delete"
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </button>
                    </div>
                  </div>
                  {expanded === v.repo && v.script && (
                    <pre className="mt-2 bg-zinc-950 rounded p-2 text-xs text-zinc-400 overflow-auto max-h-40">{v.script}</pre>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      ))}

      {filteredEntries.length === 0 && entries.length > 0 && (
        <div className="text-center text-zinc-600 py-12">No videos for this repo.</div>
      )}
      {entries.length === 0 && (
        <div className="text-center text-zinc-600 py-12">No videos in depot. Generate one first.</div>
      )}
    </div>
  );
}
