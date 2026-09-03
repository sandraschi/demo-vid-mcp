import { FileText, Send } from "lucide-react";
import { useCallback, useEffect, useState } from "react";

interface RepoCategory {
  name: string;
  repos: string[];
}

export default function Generate() {
  const [categories, setCategories] = useState<RepoCategory[]>([]);
  const [selectedCat, setSelectedCat] = useState("");
  const [selectedRepo, setSelectedRepo] = useState("");
  const [script, setScript] = useState("");
  const [busy, setBusy] = useState(false);
  const [drafting, setDrafting] = useState(false);
  const [result, setResult] = useState<string | null>(null);

  useEffect(() => {
    fetch("/api/repos")
      .then((r) => r.json())
      .then((d) => setCategories(d.categories || []))
      .catch(() => {});
  }, []);

  const currentRepos = categories.find((c) => c.name === selectedCat)?.repos || [];

  const handleDraft = useCallback(async () => {
    if (!selectedRepo) return;
    setDrafting(true);
    try {
      const r = await fetch("/api/script-draft", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ repo: selectedRepo }),
      });
      const d = await r.json();
      if (d.success && d.script) {
        setScript(JSON.stringify(d.script, null, 2));
      } else {
        setScript(`# Error: ${d.error || "failed to draft"}`);
      }
    } catch (e) {
      setScript(
        "# Error: Backend service is not reachable on port 11134.\n# Please start the server using 'just serve' or 'start.ps1'.",
      );
    } finally {
      setDrafting(false);
    }
  }, [selectedRepo]);

  const handleGenerate = useCallback(async () => {
    if (!selectedRepo) return;
    setBusy(true);
    setResult(null);
    try {
      const body: any = { repo: selectedRepo };
      const trimmed = script.trim();
      if (trimmed && (trimmed.startsWith("{") || trimmed.startsWith("title:"))) {
        body.script_yaml = trimmed;
      }
      const r = await fetch("/api/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      const d = await r.json();
      setResult(JSON.stringify(d, null, 2));
    } catch (e) {
      setResult(
        "Error: Backend service is not reachable on port 11134. Please start it with 'just serve' or 'start.ps1'.",
      );
    } finally {
      setBusy(false);
    }
  }, [selectedRepo, script]);

  const [aspectRatio, setAspectRatio] = useState("16:9");
  const [resolution, setResolution] = useState("720p");
  const [enqueueing, setEnqueueing] = useState(false);

  const handleEnqueue = useCallback(async () => {
    if (!selectedRepo) return;
    setEnqueueing(true);
    setResult(null);
    try {
      const body: any = {
        repo: selectedRepo,
        aspect_ratio: aspectRatio,
        resolution: resolution,
      };
      const trimmed = script.trim();
      if (trimmed && (trimmed.startsWith("{") || trimmed.startsWith("title:"))) {
        body.script_yaml = trimmed;
      }
      const r = await fetch("/api/queue", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      const d = await r.json();
      if (d.success) {
        setResult(
          `Job enqueued successfully!\nJob ID: ${d.job.id}\nCheck the Queue tab to monitor rendering progress.`,
        );
      } else {
        setResult(`Failed to enqueue: ${d.error}`);
      }
    } catch (e) {
      setResult("Error: Failed to reach backend on port 11134.");
    } finally {
      setEnqueueing(false);
    }
  }, [selectedRepo, script, aspectRatio, resolution]);

  return (
    <div data-testid="generate-page" className="p-6 max-w-3xl mx-auto">
      <h1 className="text-xl font-bold text-zinc-100 mb-6">Generate Video</h1>
      <div className="bg-zinc-900 rounded-lg p-4 border border-zinc-800 space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm text-zinc-400 mb-1">Category</label>
            <select
              value={selectedCat}
              onChange={(e) => {
                setSelectedCat(e.target.value);
                setSelectedRepo("");
              }}
              data-testid="category-select"
              className="w-full bg-zinc-800 text-zinc-200 border border-zinc-700 rounded-md px-3 py-2 text-sm"
            >
              <option value="">Select category...</option>
              {categories.map((c) => (
                <option key={c.name} value={c.name}>
                  {c.name} ({c.repos.length})
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm text-zinc-400 mb-1">Repo</label>
            <select
              value={selectedRepo}
              onChange={(e) => setSelectedRepo(e.target.value)}
              data-testid="repo-select"
              disabled={!selectedCat}
              className="w-full bg-zinc-800 text-zinc-200 border border-zinc-700 rounded-md px-3 py-2 text-sm disabled:opacity-50"
            >
              <option value="">{selectedCat ? "Select repo..." : "Pick a category first"}</option>
              {currentRepos.map((r) => (
                <option key={r} value={r}>
                  {r}
                </option>
              ))}
            </select>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm text-zinc-400 mb-1">Aspect Ratio</label>
            <select
              value={aspectRatio}
              onChange={(e) => setAspectRatio(e.target.value)}
              className="w-full bg-zinc-800 text-zinc-200 border border-zinc-700 rounded-md px-3 py-2 text-sm"
            >
              <option value="16:9">16:9 Landscape (Desktop Walkthrough)</option>
              <option value="9:16">9:16 Vertical (Mobile / Social Reel)</option>
            </select>
          </div>
          <div>
            <label className="block text-sm text-zinc-400 mb-1">Resolution</label>
            <select
              value={resolution}
              onChange={(e) => setResolution(e.target.value)}
              className="w-full bg-zinc-800 text-zinc-200 border border-zinc-700 rounded-md px-3 py-2 text-sm"
            >
              <option value="720p">720p (Fast)</option>
              <option value="1080p">1080p (High Definition)</option>
            </select>
          </div>
        </div>

        <div>
          <div className="flex items-center justify-between mb-1">
            <label className="block text-sm text-zinc-400">Script YAML (optional)</label>
            <button
              type="button"
              onClick={handleDraft}
              disabled={!selectedRepo || drafting}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded text-xs text-zinc-400 hover:text-white hover:bg-zinc-800 disabled:opacity-50 cursor-pointer border border-zinc-700"
            >
              <FileText className="h-3.5 w-3.5" />
              {drafting ? "Drafting..." : "Draft script"}
            </button>
          </div>
          <textarea
            value={script}
            onChange={(e) => setScript(e.target.value)}
            rows={8}
            className="w-full bg-zinc-800 text-zinc-200 border border-zinc-700 rounded-md px-3 py-2 text-sm font-mono"
            placeholder="Click 'Draft script' or paste YAML manually"
          />
        </div>

        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={handleGenerate}
            disabled={busy || enqueueing || !selectedRepo}
            data-testid="generate-btn"
            className="flex items-center gap-2 px-4 py-2 bg-amber-600 text-white rounded-md text-sm font-medium hover:bg-amber-500 disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
          >
            <Send className="h-4 w-4" />
            {busy ? "Generating..." : "Generate Now"}
          </button>
          <button
            type="button"
            onClick={handleEnqueue}
            disabled={busy || enqueueing || !selectedRepo}
            className="flex items-center gap-2 px-4 py-2 bg-zinc-800 text-zinc-200 rounded-md text-sm font-medium hover:bg-zinc-700 disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer border border-zinc-700"
          >
            {enqueueing ? "Enqueueing..." : "Add to Background Queue"}
          </button>
        </div>

        {result && (
          <pre className="bg-zinc-950 rounded-md p-3 text-xs text-zinc-400 overflow-auto max-h-96">
            {result}
          </pre>
        )}
      </div>
    </div>
  );
}
