import {
  Clapperboard,
  FileText,
  HelpCircle,
  LayoutDashboard,
  ListOrdered,
  MessageSquare,
  Mic,
  Moon,
  Music2,
  Settings,
  SquareStack,
  Sun,
  Terminal,
  Video,
  Warehouse,
} from "lucide-react";
import { useEffect, useState } from "react";
import Chat from "./pages/Chat";
import Choreography from "./pages/Choreography";
import Dashboard from "./pages/Dashboard";
import Depot from "./pages/Depot";
import Detail from "./pages/Detail";
import Generate from "./pages/Generate";
import Help from "./pages/Help";
import Logs from "./pages/Logs";
import Music from "./pages/Music";
import Queue from "./pages/Queue";
import Scripts from "./pages/Scripts";
import SettingsPage from "./pages/Settings";
import Speech from "./pages/Speech";
import { useBackendStore } from "./store/backend";

const NAV = [
  { id: "dashboard", label: "Dashboard", icon: LayoutDashboard },
  { id: "depot", label: "Depot", icon: Warehouse },
  { id: "generate", label: "Generate", icon: Video },
  { id: "choreography", label: "Choreography", icon: Clapperboard },
  { id: "speech", label: "Speech", icon: Mic },
  { id: "music", label: "Music", icon: Music2 },
  { id: "chat", label: "Chat", icon: MessageSquare },
  { id: "scripts", label: "Scripts", icon: FileText },
  { id: "settings", label: "Settings", icon: Settings },
  { id: "logs", label: "Logs", icon: Terminal },
  { id: "queue", label: "Queue", icon: ListOrdered },
  { id: "help", label: "Help", icon: HelpCircle },
] as const;

type Page = (typeof NAV)[number]["id"];

export default function App() {
  const [page, setPage] = useState<Page>("dashboard");
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const backendOk = useBackendStore((s) => s.backendOk);
  const backendVersion = useBackendStore((s) => s.version);

  // Global backend connection watcher: Tauri "backend-status" event +
  // HTTP poll fallback (steady 10s when healthy, exponential backoff
  // 1s/2s/4s/8s/16s while unreachable). Lives in the store, not per-page
  // state, so every page sees the same connection status.
  useEffect(() => useBackendStore.getState().init(), []);

  const [zoom, setZoom] = useState(() => {
    try {
      const saved = localStorage.getItem("tauri-zoom");
      return saved ? Number.parseFloat(saved) : 1.0;
    } catch {
      return 1.0;
    }
  });

  useEffect(() => {
    const handleWheel = (e: WheelEvent) => {
      if (e.ctrlKey) {
        e.preventDefault();
        const delta = e.deltaY < 0 ? 0.1 : -0.1;
        setZoom((z) => {
          const next = Math.min(Math.max(Math.round((z + delta) * 10) / 10, 0.5), 2.0);
          try {
            localStorage.setItem("tauri-zoom", next.toString());
          } catch {}
          return next;
        });
      }
    };
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.ctrlKey && e.key === "0") {
        e.preventDefault();
        setZoom(1.0);
        try {
          localStorage.setItem("tauri-zoom", "1.0");
        } catch {}
      }
    };
    window.addEventListener("wheel", handleWheel, { passive: false });
    window.addEventListener("keydown", handleKeyDown);
    return () => {
      window.removeEventListener("wheel", handleWheel);
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, []);

  // EXPERIMENTAL light mode (invert hack). Not fleet standard - see index.css.
  // Toggling `.dark` off the root flips the invert filter; persisted so the
  // choice survives reloads. Delete this + the CSS block to revert.
  const [light, setLight] = useState(() => {
    try {
      return localStorage.getItem("demo-vid-light-mode") === "1";
    } catch {
      return false;
    }
  });

  useEffect(() => {
    document.documentElement.classList.toggle("dark", !light);
    try {
      localStorage.setItem("demo-vid-light-mode", light ? "1" : "0");
    } catch {
      // ignore storage errors
    }
  }, [light]);

  const PageComponent = {
    dashboard: Dashboard,
    depot: Depot,
    detail: Detail,
    generate: Generate,
    choreography: Choreography,
    speech: Speech,
    music: Music,
    chat: Chat,
    settings: SettingsPage,
    logs: Logs,
    scripts: Scripts,
    queue: Queue,
    help: Help,
  }[page];

  return (
    <div className="flex h-screen" style={{ zoom }}>
      <aside
        data-testid="sidebar"
        className={`${sidebarOpen ? "w-56" : "w-16"} bg-zinc-950 border-r border-zinc-800 flex flex-col transition-all duration-200`}
      >
        <div className="p-4 flex items-center gap-3 border-b border-zinc-800">
          {sidebarOpen && <span className="font-bold text-zinc-100 text-lg">demo-vid</span>}
          <button
            type="button"
            onClick={() => setLight((v) => !v)}
            className="ml-auto text-zinc-400 hover:text-white cursor-pointer"
            aria-label="Toggle light mode (experimental)"
            title={
              light
                ? "Switch to dark (experimental light mode)"
                : "Switch to light (experimental, ugly)"
            }
          >
            {light ? <Moon className="h-4 w-4" /> : <Sun className="h-4 w-4" />}
          </button>
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="text-zinc-400 hover:text-white cursor-pointer"
            aria-label="Toggle sidebar"
          >
            <SquareStack className="h-4 w-4" />
          </button>
        </div>
        <nav className="flex-1 p-2 space-y-1">
          {NAV.map((n) => (
            <button
              key={n.id}
              onClick={() => setPage(n.id)}
              data-testid={`nav-${n.id}`}
              className={`w-full flex items-center gap-3 px-3 py-2 rounded-md text-sm transition-colors cursor-pointer ${page === n.id ? "bg-zinc-800 text-white" : "text-zinc-400 hover:text-white hover:bg-zinc-900"}`}
            >
              <n.icon className="h-4 w-4 shrink-0" />
              {sidebarOpen && <span>{n.label}</span>}
            </button>
          ))}
        </nav>
        <div className="p-3 border-t border-zinc-800 text-sm text-zinc-300 flex items-center justify-between">
          {sidebarOpen && (
            <span
              data-testid="sidebar-backend-dot"
              className="flex items-center gap-1.5"
              title={
                backendOk === null
                  ? "Connecting..."
                  : backendOk
                    ? "Backend connected"
                    : "Backend offline"
              }
            >
              <span
                className={`w-2 h-2 rounded-full ${backendOk === null ? "bg-zinc-500" : backendOk ? "bg-green-500" : "bg-red-500"}`}
              />
              v{backendVersion ?? "0.3.0"}
            </span>
          )}
          {sidebarOpen && <span>{Math.round(zoom * 100)}%</span>}
        </div>
      </aside>

      <main data-testid={`${page}-page`} className="flex-1 overflow-auto bg-zinc-950">
        <PageComponent />
      </main>
    </div>
  );
}
