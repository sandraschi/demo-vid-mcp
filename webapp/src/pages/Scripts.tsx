import { FileText } from "lucide-react";

const SCRIPTS = [
  { repo: "chitchat", status: "done" as const },
  { repo: "arxiv-mcp", status: "pending" as const },
  { repo: "calibre-mcp", status: "pending" as const },
  { repo: "pywinauto-mcp", status: "pending" as const },
  { repo: "blender-mcp", status: "pending" as const },
  { repo: "inkscape-mcp", status: "pending" as const },
];

export default function Scripts() {
  return (
    <div data-testid="scripts-page" className="p-6 max-w-3xl mx-auto">
      <div className="flex items-center gap-3 mb-6">
        <FileText className="h-7 w-7 text-amber-400" />
        <h1 className="text-xl font-bold text-zinc-100">Narration Scripts</h1>
      </div>
      <div className="bg-zinc-900 rounded-lg border border-zinc-800 overflow-hidden">
        {SCRIPTS.map((s) => (
          <div key={s.repo} className="flex items-center justify-between px-4 py-3 border-b border-zinc-800 last:border-0">
            <span className="text-sm text-zinc-200">{s.repo}</span>
            <span className={`text-xs px-2 py-0.5 rounded-full ${s.status === "done" ? "bg-green-900 text-green-300" : "bg-zinc-800 text-zinc-400"}`}>
              {s.status === "done" ? "Has script" : "Pending"}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
