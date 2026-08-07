import { useEffect, useState } from "react";
import { Video, SquareStack, FileText, ListOrdered, HelpCircle, LayoutDashboard, Warehouse, Terminal, Clapperboard, Settings, MessageSquare, Moon, Sun } from "lucide-react";
import Dashboard from "./pages/Dashboard";
import Depot from "./pages/Depot";
import Detail from "./pages/Detail";
import Generate from "./pages/Generate";
import Choreography from "./pages/Choreography";
import Chat from "./pages/Chat";
import SettingsPage from "./pages/Settings";
import Logs from "./pages/Logs";
import Scripts from "./pages/Scripts";
import Queue from "./pages/Queue";
import Help from "./pages/Help";

const NAV = [
  { id: "dashboard", label: "Dashboard", icon: LayoutDashboard },
  { id: "depot", label: "Depot", icon: Warehouse },
  { id: "generate", label: "Generate", icon: Video },
  { id: "choreography", label: "Choreography", icon: Clapperboard },
  { id: "chat", label: "Chat", icon: MessageSquare },
  { id: "scripts", label: "Scripts", icon: FileText },
  { id: "settings", label: "Settings", icon: Settings },
  { id: "logs", label: "Logs", icon: Terminal },
  { id: "queue", label: "Queue", icon: ListOrdered },
  { id: "help", label: "Help", icon: HelpCircle },
] as const;

type Page = typeof NAV[number]["id"];

export default function App() {
  const [page, setPage] = useState<Page>("dashboard");
  const [sidebarOpen, setSidebarOpen] = useState(true);

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
    chat: Chat,
    settings: SettingsPage,
    logs: Logs,
    scripts: Scripts,
    queue: Queue,
    help: Help,
  }[page];

  return (
    <div className="flex h-screen">
      <aside data-testid="sidebar" className={`${sidebarOpen ? "w-56" : "w-16"} bg-zinc-950 border-r border-zinc-800 flex flex-col transition-all duration-200`}>
        <div className="p-4 flex items-center gap-3 border-b border-zinc-800">
          {sidebarOpen && <span className="font-bold text-zinc-100 text-lg">demo-vid</span>}
          <button
            type="button"
            onClick={() => setLight((v) => !v)}
            className="ml-auto text-zinc-400 hover:text-white cursor-pointer"
            aria-label="Toggle light mode (experimental)"
            title={light ? "Switch to dark (experimental light mode)" : "Switch to light (experimental, ugly)"}
          >
            {light ? <Moon className="h-4 w-4" /> : <Sun className="h-4 w-4" />}
          </button>
          <button onClick={() => setSidebarOpen(!sidebarOpen)} className="text-zinc-400 hover:text-white cursor-pointer" aria-label="Toggle sidebar">
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
        <div className="p-3 border-t border-zinc-800 text-xs text-zinc-600">
          {sidebarOpen && <span>v0.1.0</span>}
        </div>
      </aside>

      <main data-testid={`${page}-page`} className="flex-1 overflow-auto bg-zinc-950">
        <PageComponent />
      </main>
    </div>
  );
}
