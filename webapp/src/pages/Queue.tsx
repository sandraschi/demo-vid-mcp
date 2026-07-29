import { ListOrdered } from "lucide-react";

export default function Queue() {
  return (
    <div data-testid="queue-page" className="p-6 max-w-3xl mx-auto">
      <div className="flex items-center gap-3 mb-6">
        <ListOrdered className="h-7 w-7 text-amber-400" />
        <h1 className="text-xl font-bold text-zinc-100">Queue</h1>
        <span className="text-sm text-zinc-500">No active jobs</span>
      </div>
      <div className="bg-zinc-900 rounded-lg p-8 border border-zinc-800 text-center text-zinc-600">
        Queue is empty. Start a generation from the Generate page or via the demo_vid_generate MCP tool.
      </div>
    </div>
  );
}
