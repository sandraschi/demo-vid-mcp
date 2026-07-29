import { useCallback, useState } from "react";
import { Send } from "lucide-react";

const REPO_OPTIONS = ["chitchat", "arxiv-mcp", "calibre-mcp", "pywinauto-mcp", "blender-mcp", "inkscape-mcp"];

export default function Generate() {
  const [repo, setRepo] = useState("");
  const [script, setScript] = useState("");
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<string | null>(null);

  const handleGenerate = useCallback(async () => {
    if (!repo.trim()) return;
    setBusy(true);
    setResult(null);
    try {
      const r = await fetch("/api/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ repo: repo.trim(), script_yaml: script || null }),
      });
      if (r.ok) {
        const d = await r.json();
        setResult(JSON.stringify(d, null, 2));
      } else {
        setResult(`Error: HTTP ${r.status}`);
      }
    } catch (e) {
      setResult(`Error: ${e}`);
    } finally {
      setBusy(false);
    }
  }, [repo, script]);

  return (
    <div data-testid="generate-page" className="p-6 max-w-3xl mx-auto">
      <h1 className="text-xl font-bold text-zinc-100 mb-6">Generate Video</h1>
      <div className="bg-zinc-900 rounded-lg p-4 border border-zinc-800 space-y-4">
        <div>
          <label className="block text-sm text-zinc-400 mb-1">Repo</label>
          <select value={repo} onChange={e => setRepo(e.target.value)} data-testid="repo-select" className="w-full bg-zinc-800 text-zinc-200 border border-zinc-700 rounded-md px-3 py-2 text-sm">
            <option value="">Select repo...</option>
            {REPO_OPTIONS.map(r => <option key={r} value={r}>{r}</option>)}
          </select>
        </div>
        <div>
          <label className="block text-sm text-zinc-400 mb-1">Script YAML (optional)</label>
          <textarea value={script} onChange={e => setScript(e.target.value)} rows={8} className="w-full bg-zinc-800 text-zinc-200 border border-zinc-700 rounded-md px-3 py-2 text-sm font-mono" placeholder="title: Demo...&#10;steps:&#10;  - action: goto&#10;    url: /" />
        </div>
        <button
          onClick={handleGenerate}
          disabled={busy || !repo.trim()}
          data-testid="generate-btn"
          className="flex items-center gap-2 px-4 py-2 bg-amber-600 text-white rounded-md text-sm hover:bg-amber-500 disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
        >
          <Send className="h-4 w-4" />
          {busy ? "Generating..." : "Generate"}
        </button>
        {result && (
          <pre className="bg-zinc-950 rounded-md p-3 text-xs text-zinc-400 overflow-auto max-h-60">{result}</pre>
        )}
      </div>
    </div>
  );
}
