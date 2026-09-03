import { Bot, Download, Eraser, Send, Sparkles, User } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";

const STORAGE_KEY = "demo-vid-mcp-chat-history";
const PERSONALITY_KEY = "demo-vid-mcp-chat-personality";

interface Message {
  role: "user" | "assistant";
  content: string;
  ts?: string;
}

const PERSONALITIES: Record<string, string> = {
  "Research Assistant":
    "You are a thorough research assistant. Provide detailed, well-structured answers with citations where relevant.",
  "Expert Reviewer":
    "You are a code and architecture reviewer. Analyze critically, point out issues, suggest improvements.",
  "Quick Summarizer": "You summarize concisely in 3-5 bullet points. No fluff, no preamble.",
  Custom: "",
};

const EXAMPLE_PROMPTS = [
  {
    group: "Discovery",
    prompts: [
      "How do I generate a video?",
      "List all available tools",
      "What ports does this service use?",
    ],
  },
  {
    group: "Scripting",
    prompts: [
      "Draft a narration script for chitchat",
      "Validate this YAML script",
      "How do I add a desktop capture step?",
    ],
  },
  {
    group: "Troubleshooting",
    prompts: ["Why is my video blank?", "No voiceover in output", "Playwright capture hangs"],
  },
];

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>(() => {
    try {
      return JSON.parse(localStorage.getItem(STORAGE_KEY) || "[]");
    } catch {
      return [];
    }
  });
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [personality, setPersonality] = useState(
    () => localStorage.getItem(PERSONALITY_KEY) || "Research Assistant",
  );
  const [customPrompt, setCustomPrompt] = useState("");
  const [provider, setProvider] = useState(() => localStorage.getItem("llm_provider") || "ollama");
  const [model, setModel] = useState(() => localStorage.getItem("llm_model") || "");
  const [providerOk, setProviderOk] = useState<boolean | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(messages.slice(-100)));
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  useEffect(() => {
    localStorage.setItem(PERSONALITY_KEY, personality);
  }, [personality]);

  useEffect(() => {
    const stored = localStorage.getItem("llm_provider");
    if (stored) setProvider(stored);
    const storedModel = localStorage.getItem("llm_model");
    if (storedModel) setModel(storedModel);
  }, []);

  // Provider health check — via backend proxy (not direct browser fetch, CORS)
  useEffect(() => {
    fetch("/api/llm/discover", { signal: AbortSignal.timeout(3000) })
      .then((r) => r.json())
      .then((d) => {
        const provs = d.providers || [];
        const found = provs.find((p: any) => p.name.toLowerCase() === provider.toLowerCase());
        if (found) setProviderOk(found.detected);
        else setProviderOk(false);
      })
      .catch(() => setProviderOk(false));
  }, [provider]);

  const sendMessage = useCallback(async () => {
    if (!input.trim() || busy) return;
    const userMsg: Message = {
      role: "user",
      content: input.trim(),
      ts: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setBusy(true);

    try {
      const personalityPrompt =
        personality === "Custom" ? customPrompt : PERSONALITIES[personality] || "";
      const systemContent = `You are a helpful AI assistant for demo-vid-mcp, the fleet demo video pipeline. Answer questions about generating videos, using MCP tools, and the fleet architecture. Be concise and accurate.\n\n${personalityPrompt ? `---\n\n## Role\n${personalityPrompt}` : ""}`;
      const mcpMessages = [{ role: "system", content: systemContent }, ...messages, userMsg].map(
        (m) => ({ role: m.role, content: m.content }),
      );

      const r = await fetch("/api/llm/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ provider, model, messages: mcpMessages }),
      });
      const data = await r.json();
      if (data.success && data.message?.content) {
        setMessages((prev) => [
          ...prev,
          {
            role: "assistant",
            content: data.message.content,
            ts: new Date().toISOString(),
          },
        ]);
      } else {
        setMessages((prev) => [
          ...prev,
          {
            role: "assistant",
            content: data.error || "No response from provider",
            ts: new Date().toISOString(),
          },
        ]);
      }
    } catch (e) {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: `Error: ${e}`,
          ts: new Date().toISOString(),
        },
      ]);
    } finally {
      setBusy(false);
    }
  }, [input, busy, messages, personality, customPrompt, provider, model]);

  const handleClear = useCallback(() => {
    setMessages([]);
    localStorage.removeItem(STORAGE_KEY);
  }, []);

  const handleExport = useCallback(() => {
    if (messages.length === 0) return;
    const text = messages
      .map(
        (m) =>
          `[${new Date(m.ts || "").toLocaleString()}] ${m.role === "user" ? "You" : "AI"}: ${m.content}`,
      )
      .join("\n\n");
    const blob = new Blob([text], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `demo-vid-mcp-chat-${Date.now()}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  }, [messages]);

  const handleExampleClick = useCallback((prompt: string) => {
    setInput(prompt);
  }, []);

  return (
    <div className="flex flex-col h-full">
      {/* Controls Bar */}
      <div
        data-testid="chat-controls"
        className="flex items-center gap-3 px-6 py-3 border-b border-zinc-800 bg-zinc-950 shrink-0 flex-wrap"
      >
        <select
          value={personality}
          onChange={(e) => setPersonality(e.target.value)}
          data-testid="personality-select"
          className="bg-zinc-800 text-zinc-200 border border-zinc-700 rounded-md px-2 py-1.5 text-xs"
        >
          {Object.keys(PERSONALITIES).map((p) => (
            <option key={p} value={p}>
              {p}
            </option>
          ))}
        </select>

        {personality === "Custom" && (
          <input
            value={customPrompt}
            onChange={(e) => setCustomPrompt(e.target.value)}
            className="bg-zinc-800 text-zinc-200 border border-zinc-700 rounded-md px-2 py-1.5 text-xs w-48"
            placeholder="Custom system prompt..."
          />
        )}

        <div className="flex items-center gap-1.5 ml-auto">
          <div
            className={`w-2 h-2 rounded-full ${providerOk === null ? "bg-zinc-500" : providerOk ? "bg-green-500" : "bg-red-500"}`}
          />
          <span className="text-xs text-zinc-500">
            {provider} {model ? `· ${model}` : ""}
          </span>
        </div>

        <button
          onClick={handleExport}
          disabled={messages.length === 0}
          data-testid="chat-export"
          className="p-1.5 rounded text-zinc-500 hover:text-white hover:bg-zinc-800 disabled:opacity-30 cursor-pointer"
          title="Export"
        >
          <Download className="h-4 w-4" />
        </button>
        <button
          onClick={handleClear}
          disabled={messages.length === 0}
          data-testid="chat-clear"
          className="p-1.5 rounded text-zinc-500 hover:text-red-400 hover:bg-zinc-800 disabled:opacity-30 cursor-pointer"
          title="Clear"
        >
          <Eraser className="h-4 w-4" />
        </button>
      </div>

      {providerOk === false && (
        <div className="bg-zinc-900/90 border-b border-amber-500/30 px-6 py-2.5 text-xs text-zinc-300 flex items-center justify-between shrink-0">
          <div className="flex items-center gap-2">
            <span className="inline-block w-2 h-2 rounded-full bg-amber-500" />
            <span>
              <strong className="text-zinc-100">Ollama is offline on port 11434.</strong> Video
              recording, voiceover, and FFmpeg composition are fully independent and working. Run{" "}
              <code className="bg-zinc-800 px-1.5 py-0.5 rounded border border-zinc-700 font-mono text-amber-300">
                ollama serve
              </code>{" "}
              to enable local AI chat.
            </span>
          </div>
        </div>
      )}

      {/* Messages */}
      <div data-testid="chat-messages" className="flex-1 overflow-y-auto px-6 py-4 space-y-4">
        {messages.length === 0 && (
          <>
            <div className="text-center py-12">
              <Sparkles className="h-10 w-10 text-zinc-700 mx-auto mb-3" />
              <h2 className="text-lg font-semibold text-zinc-400 mb-1">Ask about demo videos</h2>
              <p className="text-sm text-zinc-600">
                Generate, script, or troubleshoot your fleet video pipeline.
              </p>
            </div>

            <div data-testid="example-prompts" className="space-y-3">
              {EXAMPLE_PROMPTS.map((group) => (
                <div key={group.group}>
                  <div className="text-xs text-zinc-600 mb-1.5 font-medium uppercase tracking-wide">
                    {group.group}
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {group.prompts.map((p) => (
                      <button
                        key={p}
                        onClick={() => handleExampleClick(p)}
                        className="px-3 py-1.5 rounded-full bg-zinc-900 border border-zinc-800 text-xs text-zinc-400 hover:text-zinc-200 hover:border-zinc-600 cursor-pointer transition-colors"
                      >
                        {p}
                      </button>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </>
        )}

        {messages.map((m, i) => (
          <div key={i} className={`flex gap-3 ${m.role === "user" ? "justify-end" : ""}`}>
            {m.role === "assistant" && (
              <div className="w-8 h-8 rounded-full bg-zinc-800 flex items-center justify-center shrink-0">
                <Bot className="h-4 w-4 text-amber-400" />
              </div>
            )}
            <div className={`max-w-[75%] ${m.role === "user" ? "order-1" : ""}`}>
              {m.role === "user" && (
                <div className="flex items-center gap-2 justify-end mb-1">
                  <span className="text-xs text-zinc-500">You</span>
                  <User className="h-3.5 w-3.5 text-zinc-500" />
                </div>
              )}
              <div
                className={`rounded-lg px-4 py-2.5 text-sm leading-relaxed whitespace-pre-wrap ${
                  m.role === "user"
                    ? "bg-amber-600/20 text-zinc-200 border border-amber-700/30"
                    : "bg-zinc-900 text-zinc-300 border border-zinc-800"
                }`}
              >
                {m.content}
              </div>
            </div>
          </div>
        ))}

        {busy && (
          <div className="flex gap-3">
            <div className="w-8 h-8 rounded-full bg-zinc-800 flex items-center justify-center shrink-0">
              <Bot className="h-4 w-4 text-amber-400" />
            </div>
            <div className="bg-zinc-900 rounded-lg px-4 py-2.5 border border-zinc-800">
              <div className="flex gap-1">
                <span
                  className="w-2 h-2 bg-zinc-500 rounded-full animate-bounce"
                  style={{ animationDelay: "0ms" }}
                />
                <span
                  className="w-2 h-2 bg-zinc-500 rounded-full animate-bounce"
                  style={{ animationDelay: "150ms" }}
                />
                <span
                  className="w-2 h-2 bg-zinc-500 rounded-full animate-bounce"
                  style={{ animationDelay: "300ms" }}
                />
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="border-t border-zinc-800 p-4 bg-zinc-950 shrink-0">
        <div className="flex gap-3 max-w-3xl mx-auto">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
              }
            }}
            data-testid="chat-input"
            placeholder={
              providerOk === false
                ? "No LLM detected — start Ollama or LM Studio"
                : "Ask about demo videos..."
            }
            disabled={busy || providerOk === false}
            className="flex-1 bg-zinc-900 text-zinc-200 border border-zinc-700 rounded-lg px-4 py-2.5 text-sm placeholder-zinc-600 focus:outline-none focus:border-amber-600/50 disabled:opacity-50"
          />
          <button
            onClick={sendMessage}
            disabled={busy || !input.trim() || providerOk === false}
            data-testid="chat-send"
            className="px-4 py-2.5 bg-amber-600 text-white rounded-lg hover:bg-amber-500 disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer transition-colors"
          >
            <Send className="h-4 w-4" />
          </button>
        </div>
      </div>
    </div>
  );
}
