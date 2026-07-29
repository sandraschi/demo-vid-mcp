import { useState } from "react";
import { Video, SquareStack, FileText, ListOrdered, HelpCircle, LayoutDashboard, Clapperboard } from "lucide-react";
import Dashboard from "./pages/Dashboard";
import Gallery from "./pages/Gallery";
import Detail from "./pages/Detail";
import Generate from "./pages/Generate";
import Scripts from "./pages/Scripts";
import Queue from "./pages/Queue";
import Help from "./pages/Help";

const NAV = [
  { id: "dashboard", label: "Dashboard", icon: LayoutDashboard },
  { id: "gallery", label: "Gallery", icon: Clapperboard },
  { id: "generate", label: "Generate", icon: Video },
  { id: "scripts", label: "Scripts", icon: FileText },
  { id: "queue", label: "Queue", icon: ListOrdered },
  { id: "help", label: "Help", icon: HelpCircle },
] as const;

type Page = typeof NAV[number]["id"];

export default function App() {
  const [page, setPage] = useState<Page>("dashboard");
  const [sidebarOpen, setSidebarOpen] = useState(true);

  const PageComponent = {
    dashboard: Dashboard,
    gallery: Gallery,
    detail: Detail,
    generate: Generate,
    scripts: Scripts,
    queue: Queue,
    help: Help,
  }[page];

  return (
    <div className="flex h-screen">
      <aside data-testid="sidebar" className={`${sidebarOpen ? "w-56" : "w-16"} bg-zinc-950 border-r border-zinc-800 flex flex-col transition-all duration-200`}>
        <div className="p-4 flex items-center gap-3 border-b border-zinc-800">
          {sidebarOpen && <span className="font-bold text-zinc-100 text-lg">demo-vid</span>}
          <button onClick={() => setSidebarOpen(!sidebarOpen)} className="ml-auto text-zinc-400 hover:text-white cursor-pointer" aria-label="Toggle sidebar">
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
