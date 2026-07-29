import { HelpCircle, BookOpen, Terminal, Wrench } from "lucide-react";

const SECTIONS = [
  {
    icon: BookOpen,
    title: "Architecture",
    content: "demo-vid-mcp orchestrates the fleet video pipeline. It delegates recording (Playwright), voiceover (speech-mcp), title art (blender-mcp/gimp-mcp), and composition (davinci-resolve-mcp/FFmpeg). Each fleet service has a fallback tier — only speech-mcp is mandatory.",
  },
  {
    icon: Terminal,
    title: "Ports",
    content: "Backend: 11134, Frontend: 11135. Fleet services: speech-mcp (10909), blender-mcp (10849), gimp-mcp (10773), davinci-resolve-mcp (10843), vfx-mcp (11123), stems-mcp (11127), sfx-mcp (11121).",
  },
  {
    icon: Wrench,
    title: "Tools",
    content: "6 MCP tools: demo_vid_generate, demo_vid_list, demo_vid_refine, demo_vid_script_draft, demo_vid_script_validate, demo_vid_help. Use from Claude Desktop, Cursor, or any MCP host.",
  },
];

export default function Help() {
  return (
    <div data-testid="help-page" className="p-6 max-w-3xl mx-auto">
      <div className="flex items-center gap-3 mb-6">
        <HelpCircle className="h-7 w-7 text-amber-400" />
        <h1 className="text-xl font-bold text-zinc-100">Help</h1>
      </div>
      <div className="space-y-4">
        {SECTIONS.map((s) => (
          <div key={s.title} className="bg-zinc-900 rounded-lg p-4 border border-zinc-800">
            <div className="flex items-center gap-2 mb-2">
              <s.icon className="h-4 w-4 text-amber-400" />
              <h2 className="text-sm font-semibold text-zinc-200">{s.title}</h2>
            </div>
            <p className="text-sm text-zinc-400 leading-relaxed">{s.content}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
