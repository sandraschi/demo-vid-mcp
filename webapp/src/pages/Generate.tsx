import { useCallback, useEffect, useState } from "react";
import { Send } from "lucide-react";

interface RepoCategory { name: string; repos: string[]; }

export default function Generate() {
  const [categories, setCategories] = useState<RepoCategory[]>([]);
  const [selectedCat, setSelectedCat] = useState("");
  const [selectedRepo, setSelectedRepo] = useState("");
  const [script, setScript] = useState("");
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<string | null>(null);

  useEffect(() => {
    fetch("/api/repos").then(r => r.json()).then(d => setCategories(d.categories || [])).catch(() => {});
  }, []);

  const currentRepos = categories.find(c => c.name === selectedCat)?.repos || [];

  const handleGenerate = useCallback(async () => {
    if (!selectedRepo) return;
    setBusy(true);
    setResult(null);
    try {
      const r = await fetch("/api/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ repo: selectedRepo, script_yaml: script || null }),
      });
      const d = await r.json();
      setResult(JSON.stringify(d, null, 2));
    } catch (e) {
      setResult(`Error: ${e}`);
    } finally {
      setBusy(false);
    }
  }, [selectedRepo, script]);

  return (
    <div data-testid="generate-page" className="p-6 max-w-3xl mx-auto">
      <h1 className="text-xl font-bold text-zinc-100 mb-6">Generate Video</h1>
      <div className="bg-zinc-900 rounded-lg p-4 border border-zinc-800 space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm text-zinc-400 mb-1">Category</label>
            <select
              value={selectedCat}
              onChange={e => { setSelectedCat(e.target.value); setSelectedRepo(""); }}
              data-testid="category-select"
              className="w-full bg-zinc-800 text-zinc-200 border border-zinc-700 rounded-md px-3 py-2 text-sm"
            >
              <option value="">Select category...</option>
              {categories.map(c => (
                <option key={c.name} value={c.name}>{c.name} ({c.repos.length})</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm text-zinc-400 mb-1">Repo</label>
            <select
              value={selectedRepo}
              onChange={e => setSelectedRepo(e.target.value)}
              data-testid="repo-select"
              disabled={!selectedCat}
              className="w-full bg-zinc-800 text-zinc-200 border border-zinc-700 rounded-md px-3 py-2 text-sm disabled:opacity-50"
            >
              <option value="">{selectedCat ? "Select repo..." : "Pick a category first"}</option>
              {currentRepos.map(r => <option key={r} value={r}>{r}</option>)}
            </select>
          </div>
        </div>

        <div>
          <label className="block text-sm text-zinc-400 mb-1">Script YAML (optional)</label>
          <textarea
            value={script}
            onChange={e => setScript(e.target.value)}
            rows={8}
            className="w-full bg-zinc-800 text-zinc-200 border border-zinc-700 rounded-md px-3 py-2 text-sm font-mono"
            placeholder="title: Demo..."
          />
        </div>

        <button
          onClick={handleGenerate}
          disabled={busy || !selectedRepo}
          data-testid="generate-btn"
          className="flex items-center gap-2 px-4 py-2 bg-amber-600 text-white rounded-md text-sm hover:bg-amber-500 disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
        >
          <Send className="h-4 w-4" />
          {busy ? "Generating..." : "Generate"}
        </button>

        {result && (
          <pre className="bg-zinc-950 rounded-md p-3 text-xs text-zinc-400 overflow-auto max-h-96">{result}</pre>
        )}
      </div>
    </div>
  );
}
