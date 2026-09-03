import { Loader, RefreshCw, Settings as SettingsIcon, Wifi, WifiOff } from "lucide-react";
import { useCallback, useEffect, useState } from "react";

interface Provider {
  name: string;
  port: number;
  detected: boolean;
  models?: string[];
}

export default function SettingsPage() {
  const [providers, setProviders] = useState<Provider[]>([]);
  const [selectedProvider, setSelectedProvider] = useState(
    () => localStorage.getItem("llm_provider") || "",
  );
  const [selectedModel, setSelectedModel] = useState(() => localStorage.getItem("llm_model") || "");
  const [probing, setProbing] = useState(false);
  const [backendVersion, setBackendVersion] = useState("");

  const currentProvider = providers.find((p) => p.name === selectedProvider);

  const probe = useCallback(async () => {
    setProbing(true);
    try {
      const [h, d] = await Promise.all([
        fetch("/api/health")
          .then((r) => r.json())
          .catch(() => ({})),
        fetch("/api/llm/discover")
          .then((r) => r.json())
          .catch(() => ({ providers: [] })),
      ]);
      setBackendVersion(h.version || "");
      setProviders(d.providers || []);
      const detected = (d.providers || []).filter((p: Provider) => p.detected);
      if (!selectedProvider && detected.length > 0) {
        setSelectedProvider(detected[0].name);
        localStorage.setItem("llm_provider", detected[0].name);
      }
    } catch {
      /* ignore */
    } finally {
      setProbing(false);
    }
  }, [selectedProvider]);

  useEffect(() => {
    probe();
  }, [probe]);

  useEffect(() => {
    if (currentProvider?.models && !selectedModel && currentProvider.models.length > 0) {
      const m = currentProvider.models[0];
      setSelectedModel(m);
      localStorage.setItem("llm_model", typeof m === "string" ? m : "");
    }
  }, [currentProvider, selectedModel]);

  const handleProviderChange = useCallback((name: string) => {
    setSelectedProvider(name);
    setSelectedModel("");
    localStorage.setItem("llm_provider", name);
    localStorage.removeItem("llm_model");
  }, []);

  const handleModelChange = useCallback((model: string) => {
    setSelectedModel(model);
    localStorage.setItem("llm_model", model);
  }, []);

  return (
    <div data-testid="settings-page" className="p-6 max-w-3xl mx-auto">
      <div className="flex items-center gap-3 mb-6">
        <SettingsIcon className="h-7 w-7 text-amber-400" />
        <h1 className="text-xl font-bold text-zinc-100">Settings</h1>
      </div>

      {/* Backend Health */}
      <div className="bg-zinc-900 rounded-lg p-4 border border-zinc-800 mb-4">
        <h2 className="text-sm font-semibold text-zinc-200 mb-2">Backend Health</h2>
        <div className="flex items-center gap-2 text-sm">
          <span className="w-2 h-2 rounded-full bg-green-500" />
          <span className="text-zinc-400">Connected</span>
          {backendVersion && <span className="text-zinc-600">v{backendVersion}</span>}
          <button
            onClick={probe}
            disabled={probing}
            className="ml-auto p-1.5 rounded text-zinc-500 hover:text-white hover:bg-zinc-800 cursor-pointer"
          >
            <RefreshCw className={`h-4 w-4 ${probing ? "animate-spin" : ""}`} />
          </button>
        </div>
      </div>

      {/* LLM Provider */}
      <div className="bg-zinc-900 rounded-lg p-4 border border-zinc-800 mb-4">
        <h2 className="text-sm font-semibold text-zinc-200 mb-3">Local LLM</h2>

        <div className="space-y-2 mb-4">
          {providers.length === 0 && probing && (
            <div className="flex items-center gap-2 text-sm text-zinc-500">
              <Loader className="h-4 w-4 animate-spin" /> Probing providers...
            </div>
          )}
          {providers.length === 0 && !probing && (
            <div className="text-sm text-amber-500">
              No local LLM detected. Install Ollama or LM Studio to enable AI features.
            </div>
          )}
          {providers.map((p) => (
            <div
              key={p.name}
              className="flex items-center gap-3 p-2 rounded-md bg-zinc-950 border border-zinc-800"
            >
              {p.detected ? (
                <Wifi className="h-4 w-4 text-green-500" />
              ) : (
                <WifiOff className="h-4 w-4 text-zinc-600" />
              )}
              <span className="text-sm text-zinc-300 flex-1">{p.name}</span>
              <span className="text-xs text-zinc-600">:{p.port}</span>
              <span className={`text-xs ${p.detected ? "text-green-500" : "text-zinc-600"}`}>
                {p.detected ? "Detected" : "Not found"}
              </span>
            </div>
          ))}
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-xs text-zinc-500 mb-1">Provider</label>
            <select
              value={selectedProvider}
              onChange={(e) => handleProviderChange(e.target.value)}
              data-testid="llm-provider-select"
              className="w-full bg-zinc-800 text-zinc-200 border border-zinc-700 rounded-md px-3 py-2 text-sm"
              disabled={providers.filter((p) => p.detected).length === 0}
            >
              {providers.filter((p) => p.detected).length === 0 && (
                <option value="">No provider detected</option>
              )}
              {providers
                .filter((p) => p.detected)
                .map((p) => (
                  <option key={p.name} value={p.name}>
                    {p.name}
                  </option>
                ))}
            </select>
          </div>
          <div>
            <label className="block text-xs text-zinc-500 mb-1">Model</label>
            <select
              value={selectedModel}
              onChange={(e) => handleModelChange(e.target.value)}
              data-testid="llm-model-select"
              className="w-full bg-zinc-800 text-zinc-200 border border-zinc-700 rounded-md px-3 py-2 text-sm"
              disabled={!currentProvider?.models?.length}
            >
              {(!currentProvider?.models || currentProvider.models.length === 0) && (
                <option value="">No models</option>
              )}
              {(currentProvider?.models || []).map((m) => (
                <option key={m} value={m}>
                  {m}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* About */}
      <div className="bg-zinc-900 rounded-lg p-4 border border-zinc-800">
        <h2 className="text-sm font-semibold text-zinc-200 mb-2">About</h2>
        <div className="text-sm text-zinc-500 space-y-1">
          <div>demo-vid-mcp v0.1.0</div>
          <div>Backend: 11134 · Frontend: 11135</div>
          <div>speech-mcp: 10909</div>
          <div className="text-xs text-zinc-600 mt-2">
            Fleet repo: {providers.length} providers probed ·{" "}
            {providers.filter((p) => p.detected).length} detected
          </div>
        </div>
      </div>
    </div>
  );
}
