import { BookOpen, Bug, HelpCircle, Puzzle, Settings, Terminal, Wrench } from "lucide-react";
import { useState } from "react";

const TABS = [
  { id: "overview", label: "Overview", icon: BookOpen },
  { id: "architecture", label: "Architecture", icon: Puzzle },
  { id: "tools", label: "Tools", icon: Terminal },
  { id: "config", label: "Configuration", icon: Settings },
  { id: "fleet", label: "Fleet Integration", icon: Wrench },
  { id: "troubleshooting", label: "Troubleshooting", icon: Bug },
] as const;

export default function Help() {
  const [tab, setTab] = useState("overview");

  return (
    <div data-testid="help-page" className="p-6 max-w-4xl mx-auto">
      <div className="flex items-center gap-3 mb-6">
        <HelpCircle className="h-7 w-7 text-amber-400" />
        <h1 className="text-xl font-bold text-zinc-100">Help</h1>
      </div>

      {/* Horizontal Tabs */}
      <div className="border-b border-zinc-800 mb-6">
        <div className="flex gap-0 -mb-px overflow-x-auto">
          {TABS.map((t) => (
            <button
              key={t.id}
              onClick={() => setTab(t.id)}
              className={`flex items-center gap-2 px-4 py-2.5 text-sm whitespace-nowrap border-b-2 transition-colors cursor-pointer ${
                tab === t.id
                  ? "border-amber-400 text-amber-300"
                  : "border-transparent text-zinc-500 hover:text-zinc-300 hover:border-zinc-600"
              }`}
            >
              <t.icon className="h-4 w-4" />
              {t.label}
            </button>
          ))}
        </div>
      </div>

      {/* Tab Content */}
      {tab === "overview" && (
        <div className="space-y-4">
          <div className="bg-zinc-900 rounded-lg p-5 border border-zinc-800">
            <h2 className="text-base font-semibold text-zinc-100 mb-2">What is demo-vid-mcp?</h2>
            <p className="text-sm text-zinc-400 leading-relaxed">
              A centralized video pipeline server that produces narrated walkthrough videos for any
              fleet webapp. It automates: starting the target repo's backend + frontend, recording
              screen interactions via Playwright, generating TTS voiceover via speech-mcp, and
              composing everything into an MP4 with FFmpeg.
            </p>
          </div>
          <div className="bg-zinc-900 rounded-lg p-5 border border-zinc-800">
            <h2 className="text-base font-semibold text-zinc-100 mb-2">Quick Start</h2>
            <div className="text-sm text-zinc-400 space-y-1 font-mono">
              <div>
                <span className="text-zinc-500">$</span> git clone
                https://github.com/sandraschi/demo-vid-mcp
              </div>
              <div>
                <span className="text-zinc-500">$</span> cd demo-vid-mcp && just bootstrap
              </div>
              <div>
                <span className="text-zinc-500">$</span> just serve # starts backend on :11134
              </div>
              <div className="text-zinc-600 mt-3">
                Then open http://127.0.0.1:11135 in your browser.
              </div>
            </div>
          </div>
          <div className="bg-zinc-900 rounded-lg p-5 border border-zinc-800">
            <h2 className="text-base font-semibold text-zinc-100 mb-2">
              One-command video generation
            </h2>
            <div className="text-sm text-zinc-400 font-mono">
              From any MCP client:{" "}
              <span className="text-amber-300">demo_vid_generate(repo="chitchat")</span>
            </div>
            <p className="text-sm text-zinc-500 mt-2">
              The pipeline auto-starts the target webapp, records it, adds voiceover, and saves the
              MP4 to the depot.
            </p>
          </div>
        </div>
      )}

      {tab === "architecture" && (
        <div className="space-y-4">
          <div className="bg-zinc-900 rounded-lg p-5 border border-zinc-800">
            <h2 className="text-base font-semibold text-zinc-100 mb-3">Pipeline</h2>
            <pre className="text-xs text-zinc-400 font-mono leading-relaxed whitespace-pre">
              {`narration.yaml → demo-vid-mcp (conductor)
                      │
           ┌──────────┼──────────┐
           ▼          ▼          ▼
      speech-mcp  Playwright  FFmpeg
      (voiceover) (recording) (compose)
           │          │          │
           └──────────┼──────────┘
                      ▼
                 data/videos/{repo}/
                 (depot with rebuild scripts)`}
            </pre>
          </div>
          <div className="bg-zinc-900 rounded-lg p-5 border border-zinc-800">
            <h2 className="text-base font-semibold text-zinc-100 mb-2">Stage Sequence</h2>
            <div className="text-sm text-zinc-400 space-y-2">
              <div>
                <span className="text-amber-400 font-medium">1. Script</span> — Generate or validate
                narration YAML. Auto-generated from repo README if not provided.
              </div>
              <div>
                <span className="text-amber-400 font-medium">2. Auto-start</span> — Start target
                repo's backend and Vite frontend. Zombie-kills stale processes first.
              </div>
              <div>
                <span className="text-amber-400 font-medium">3. Voiceover</span> — speech-mcp TTS
                per <code className="text-zinc-300">say:</code> segment, concatenated to .wav. Runs
                parallel with recording.
              </div>
              <div>
                <span className="text-amber-400 font-medium">4. Record</span> — Playwright headless
                Chromium, native .webm recording. Content gate checks for blank pages.
              </div>
              <div>
                <span className="text-amber-400 font-medium">5. Compose</span> — FFmpeg: video +
                audio + title card + optional subtitle burn-in → MP4.
              </div>
              <div>
                <span className="text-amber-400 font-medium">6. Depot</span> — Store in{" "}
                <code className="text-zinc-300">data/videos/&lt;repo&gt;/</code> with narration.yaml
                for rebuild.
              </div>
            </div>
          </div>
          <div className="bg-zinc-900 rounded-lg p-5 border border-zinc-800">
            <h2 className="text-base font-semibold text-zinc-100 mb-2">Ports</h2>
            <div className="text-sm text-zinc-400">
              <table className="w-full text-left">
                <thead>
                  <tr className="text-zinc-500 border-b border-zinc-800">
                    <th className="py-1 pr-4">Port</th>
                    <th className="py-1">Service</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td className="py-1 pr-4 text-zinc-200">11134</td>
                    <td>Backend (FastAPI + FastMCP HTTP)</td>
                  </tr>
                  <tr>
                    <td className="py-1 pr-4 text-zinc-200">11135</td>
                    <td>Frontend (Vite React)</td>
                  </tr>
                  <tr>
                    <td className="py-1 pr-4 text-zinc-200">10909</td>
                    <td>speech-mcp (TTS voiceover)</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {tab === "tools" && (
        <div className="space-y-3">
          {[
            {
              name: "demo_vid_generate",
              desc: "Full pipeline: auto-start target webapp, record (Playwright), voiceover (speech-mcp), compose (FFmpeg) → MP4.",
              args: [
                "repo (str) — Repository name",
                "script_yaml (str, optional) — Custom YAML script",
                "base_url (str, optional) — Override target URL",
              ],
            },
            {
              name: "demo_vid_list",
              desc: "List produced videos with metadata (name, repo, size, created date).",
              args: ["repo (str, optional) — Filter by repo"],
            },
            {
              name: "demo_vid_refine",
              desc: "NOT YET IMPLEMENTED. Edit the narration.yaml directly and re-run demo_vid_generate.",
              args: [
                "video_name (str) — Video to refine",
                "feedback (str) — Description of changes",
              ],
            },
            {
              name: "demo_vid_script_draft",
              desc: "Generate a narration YAML from the target repo's README and webapp page structure.",
              args: ["repo (str) — Repository name"],
            },
            {
              name: "demo_vid_script_validate",
              desc: "Validate a narration script's structure, timing, and step integrity.",
              args: ["script_yaml (str) — YAML script content"],
            },
            {
              name: "demo_vid_help",
              desc: "List all available tools and their purpose.",
            },
          ].map((t) => (
            <div key={t.name} className="bg-zinc-900 rounded-lg p-4 border border-zinc-800">
              <div className="text-sm font-semibold text-amber-300 font-mono mb-1">{t.name}</div>
              <div className="text-sm text-zinc-400 mb-2">{t.desc}</div>
              {t.args && t.args.length > 0 && (
                <div className="text-xs text-zinc-500 space-y-0.5">
                  {t.args.map((a) => (
                    <div key={a}>{a}</div>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {tab === "config" && (
        <div className="space-y-4">
          <div className="bg-zinc-900 rounded-lg p-5 border border-zinc-800">
            <h2 className="text-base font-semibold text-zinc-100 mb-3">Environment Variables</h2>
            <div className="text-sm">
              <table className="w-full text-left">
                <thead>
                  <tr className="text-zinc-500 border-b border-zinc-800 text-xs uppercase tracking-wide">
                    <th className="py-2 pr-4">Variable</th>
                    <th className="py-2 pr-4">Default</th>
                    <th className="py-2">Description</th>
                  </tr>
                </thead>
                <tbody className="text-zinc-400">
                  {[
                    ["HOST", "127.0.0.1", "Backend bind address"],
                    ["PORT", "11134", "Backend port"],
                    ["SPEECH_MCP_URL", "http://127.0.0.1:10909", "speech-mcp TTS endpoint"],
                    ["DEMO_VID_DATA_DIR", "data", "Video storage directory"],
                    ["DEMO_VID_LOG_LEVEL", "info", "Logging level"],
                  ].map(([varName, def, desc]) => (
                    <tr key={varName} className="border-b border-zinc-800/50">
                      <td className="py-2 pr-4 text-zinc-200 font-mono text-xs">{varName}</td>
                      <td className="py-2 pr-4 text-zinc-500 font-mono text-xs">{def}</td>
                      <td className="py-2 text-sm">{desc}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
          <div className="bg-zinc-900 rounded-lg p-5 border border-zinc-800">
            <h2 className="text-base font-semibold text-zinc-100 mb-2">Narration Script Format</h2>
            <div className="text-xs text-zinc-400 font-mono whitespace-pre bg-zinc-950 rounded p-3 border border-zinc-800 overflow-x-auto">{`title: "Demo of chitchat"
duration_target: 45
voice: "heart"
steps:
  - action: goto
    url: http://127.0.0.1:10975/
    wait: 3
    say: "Chitchat gives Claude 64 conversation starters."
  - action: end
    say: "Open source."`}</div>
          </div>
        </div>
      )}

      {tab === "fleet" && (
        <div className="space-y-4">
          <div className="bg-zinc-900 rounded-lg p-5 border border-zinc-800">
            <h2 className="text-base font-semibold text-zinc-100 mb-2">Required Services</h2>
            <div className="text-sm text-zinc-400 space-y-2">
              <div>
                <span className="text-green-400">●</span>{" "}
                <strong className="text-zinc-200">speech-mcp</strong> (10909) — TTS voiceover. Must
                be running for narrated videos.
              </div>
              <div>
                <span className="text-green-400">●</span>{" "}
                <strong className="text-zinc-200">Playwright</strong> — Headless Chromium recording.
                Installed via <code className="text-zinc-300">bun add playwright</code>.
              </div>
              <div>
                <span className="text-green-400">●</span>{" "}
                <strong className="text-zinc-200">FFmpeg</strong> — Video composition. Install via{" "}
                <code className="text-zinc-300">scoop install ffmpeg</code> or{" "}
                <code className="text-zinc-300">winget install ffmpeg</code>.
              </div>
            </div>
          </div>
          <div className="bg-zinc-900 rounded-lg p-5 border border-zinc-800">
            <h2 className="text-base font-semibold text-zinc-100 mb-2">Optional Services</h2>
            <div className="text-sm text-zinc-400 space-y-2">
              <div>
                <span className="text-zinc-500">○</span>{" "}
                <strong className="text-zinc-200">OBS-mcp</strong> — Human-in-video via webcam/scene
                composition.
              </div>
              <div>
                <span className="text-zinc-500">○</span>{" "}
                <strong className="text-zinc-200">blender-mcp</strong> — 3D animated title cards.
              </div>
              <div>
                <span className="text-zinc-500">○</span>{" "}
                <strong className="text-zinc-200">stems-mcp</strong> — Background music.
              </div>
              <div>
                <span className="text-zinc-500">○</span>{" "}
                <strong className="text-zinc-200">vfx-mcp</strong> — Video transitions and effects.
              </div>
            </div>
          </div>
          <div className="bg-zinc-900 rounded-lg p-5 border border-zinc-800">
            <h2 className="text-base font-semibold text-zinc-100 mb-2">Auto-Discovery</h2>
            <p className="text-sm text-zinc-400 leading-relaxed">
              The pipeline reads <code className="text-zinc-300">WEBAPP_PORTS.md</code> from{" "}
              <code className="text-zinc-300">mcp-central-docs</code> to discover which repos have
              frontend webapps and their ports. 136 repos are auto-detected. No manual registration
              needed. The auto-start function runs each repo's{" "}
              <code className="text-zinc-300">start.ps1</code> and Vite dev server before recording.
            </p>
          </div>
        </div>
      )}

      {tab === "troubleshooting" && (
        <div className="space-y-3">
          {[
            {
              problem: "Target webapp not reachable",
              cause: "The repo's backend or frontend isn't running on the expected port.",
              fix: "Click Generate again — the auto-start tries to start it. Check the Logs page to see if start.ps1 ran successfully. Verify the repo's frontend port in WEBAPP_PORTS.md.",
            },
            {
              problem: "Video shows white screen",
              cause: "Playwright captured a blank page — the target URL isn't serving valid HTML.",
              fix: "The content gate should catch this and abort. If not, check the repo's frontend is actually serving a React app, not a JSON API.",
            },
            {
              problem: "No voiceover audio",
              cause: "speech-mcp may not be running, or the wrong TTS endpoint was called.",
              fix: "Verify speech-mcp is running on port 10909. Check the Logs page for TTS failures. The voiceover now uses GET /api/v1/tts/wav (not POST /api/v1/tts).",
            },
            {
              problem: "Video is silent with tiny filesize",
              cause:
                "Old voiceover code used POST /api/v1/tts which returns JSON, not audio bytes.",
              fix: "Update to latest code and restart backend. The fix was landed in commit be0cc19.",
            },
            {
              problem: "Depot video player doesn't work",
              cause: "Vite dev server isn't proxying /videos/ to the backend.",
              fix: "Restart the frontend (bun run dev). The proxy rule was added in commit 99654c5.",
            },
            {
              problem: "Playwright capture hangs",
              cause: "The node process may be stuck on networkidle or a Vite HMR WebSocket.",
              fix: "The capture script now uses waitUntil: 'load' instead of 'networkidle'. If it still hangs, the kill-switch is the 45s timeout in recorder.py.",
            },
          ].map((item, i) => (
            <div key={i} className="bg-zinc-900 rounded-lg p-4 border border-zinc-800">
              <div className="text-sm font-semibold text-zinc-100 mb-1">{item.problem}</div>
              <div className="text-sm text-zinc-500 mb-1">
                <strong className="text-zinc-400">Cause:</strong> {item.cause}
              </div>
              <div className="text-sm text-zinc-500">
                <strong className="text-zinc-400">Fix:</strong> {item.fix}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
