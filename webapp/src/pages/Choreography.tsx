import {
  ArrowDown,
  ArrowUp,
  Clapperboard,
  Eye,
  Monitor,
  MousePointer,
  Music,
  Play,
  Send,
  Subtitles,
  Timer,
  Trash2,
  Type,
  Volume2,
  Wand2,
} from "lucide-react";
import { useCallback, useEffect, useState } from "react";

type StepType =
  | "goto"
  | "capture_window"
  | "click"
  | "type"
  | "wait"
  | "say"
  | "sfx"
  | "transition"
  | "text_overlay"
  | "obs_scene"
  | "end";

interface ScriptStep {
  id: string;
  action: StepType;
  url?: string;
  target?: string;
  text?: string;
  wait?: number;
  say?: string;
  scene?: string;
  x?: number;
  y?: number;
  duration?: number;
}

const STEP_TEMPLATES: Record<
  StepType,
  { icon: any; label: string; color: string; fields: string[] }
> = {
  goto: {
    icon: Eye,
    label: "Navigate",
    color: "border-blue-500/50",
    fields: ["url", "wait", "say"],
  },
  capture_window: {
    icon: Monitor,
    label: "Capture Window",
    color: "border-purple-500/50",
    fields: ["target", "wait", "say", "duration"],
  },
  click: {
    icon: MousePointer,
    label: "Click",
    color: "border-amber-500/50",
    fields: ["target", "x", "y", "wait"],
  },
  type: {
    icon: Type,
    label: "Type Text",
    color: "border-green-500/50",
    fields: ["target", "text", "wait"],
  },
  wait: {
    icon: Timer,
    label: "Wait",
    color: "border-zinc-500/50",
    fields: ["wait"],
  },
  say: {
    icon: Volume2,
    label: "Narrate",
    color: "border-cyan-500/50",
    fields: ["say"],
  },
  sfx: {
    icon: Music,
    label: "Sound Effect",
    color: "border-pink-500/50",
    fields: ["text", "wait"],
  },
  transition: {
    icon: Wand2,
    label: "Transition",
    color: "border-orange-500/50",
    fields: ["text", "duration"],
  },
  text_overlay: {
    icon: Subtitles,
    label: "Text Overlay",
    color: "border-violet-500/50",
    fields: ["text", "duration", "wait"],
  },
  obs_scene: {
    icon: Clapperboard,
    label: "OBS Scene",
    color: "border-yellow-500/50",
    fields: ["scene", "wait", "say"],
  },
  end: {
    icon: Play,
    label: "End",
    color: "border-red-500/50",
    fields: ["say"],
  },
};

let _stepCounter = 0;
function newId() {
  return `step-${++_stepCounter}`;
}

const DEFAULT_STEPS: ScriptStep[] = [
  {
    id: newId(),
    action: "goto",
    url: "/",
    wait: 3,
    say: "Welcome to this demo.",
  },
  { id: newId(), action: "end", say: "Thanks for watching." },
];

interface GlobalOptions {
  voiceover: boolean;
  music: boolean;
  subtitles: boolean;
  desktop_capture: boolean;
  title_card: boolean;
}

export default function Choreography() {
  const [steps, setSteps] = useState<ScriptStep[]>(DEFAULT_STEPS);
  const [options, setOptions] = useState<GlobalOptions>({
    voiceover: true,
    music: false,
    subtitles: true,
    desktop_capture: false,
    title_card: false,
  });
  const [title, setTitle] = useState("Demo Video");
  const [voiceName, setVoiceName] = useState("heart");
  const [yamlPreview, setYamlPreview] = useState("");
  const [repo, setRepo] = useState("");

  const updateStep = useCallback((id: string, field: string, value: any) => {
    setSteps((prev) => prev.map((s) => (s.id === id ? { ...s, [field]: value } : s)));
  }, []);

  const removeStep = useCallback((id: string) => {
    setSteps((prev) => prev.filter((s) => s.id !== id));
  }, []);

  const moveStep = useCallback((index: number, dir: -1 | 1) => {
    setSteps((prev) => {
      const next = [...prev];
      const target = index + dir;
      if (target < 0 || target >= next.length) return next;
      [next[index], next[target]] = [next[target], next[index]];
      return next;
    });
  }, []);

  const addStep = useCallback((type: StepType) => {
    const step: ScriptStep = { id: newId(), action: type, wait: 2 };
    if (type === "goto") step.url = "/";
    if (type === "capture_window") step.target = "Window Title";
    if (type === "click") step.target = "[data-testid='...']";
    if (type === "text_overlay") step.text = "Your text here";
    if (type === "obs_scene") step.scene = "talking-head";
    if (type === "say") step.say = "Narration text...";
    if (type === "transition") step.text = "crossfade";
    if (type === "sfx") step.text = "click";
    setSteps((prev) => [...prev.slice(0, -1), step, ...prev.slice(-1)]);
  }, []);

  const [categorizedRepos, setCategorizedRepos] = useState<Record<string, string[]>>({});

  useEffect(() => {
    fetch("/api/repos")
      .then((r) => r.json())
      .then((d) => {
        const m: Record<string, string[]> = {};
        (d.categories || []).forEach((c: any) => {
          m[c.name] = c.repos;
        });
        setCategorizedRepos(m);
      })
      .catch(() => {});
  }, []);

  const generateYaml = useCallback(() => {
    const hasSay = (s: ScriptStep) => options.voiceover && s.say;
    const yaml = {
      title,
      duration_target: steps.reduce((t, s) => t + (s.wait || 2), 0) + 5,
      voice: voiceName,
      title_style: options.title_card ? { type: "plain", duration: 4 } : undefined,
      music: options.music ? { source: "stems", track: "ambient-calm", volume: 0.3 } : undefined,
      subtitle_style: options.subtitles ? { font: "Inter", color: "#ffffff", size: 24 } : undefined,
      steps: steps.map((s) => {
        const base: any = { action: s.action };
        if (s.url) base.url = base.url || s.url;
        if (s.target) base.target = s.target;
        if (s.text) base.text = s.text;
        if (s.wait) base.wait = s.wait;
        if (s.scene) base.scene = s.scene;
        if (s.x !== undefined && s.y !== undefined) {
          base.x = s.x;
          base.y = s.y;
        }
        if (s.duration) base.duration = s.duration;
        if (hasSay(s)) base.say = s.say;
        return base;
      }),
    };
    return yaml;
  }, [steps, options, title, voiceName]);

  useEffect(() => {
    setYamlPreview(JSON.stringify(generateYaml(), null, 2));
  }, [generateYaml]);

  const handleGenerate = useCallback(async () => {
    if (!repo) {
      alert("Select a repo first");
      return;
    }
    const yaml_str = generateYaml();
    const body = { repo, script_yaml: JSON.stringify(yaml_str) };
    try {
      const r = await fetch("/api/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      const d = await r.json();
      alert(JSON.stringify(d, null, 2));
    } catch (e) {
      alert(`Error: ${e}`);
    }
  }, [repo, generateYaml]);

  return (
    <div data-testid="choreography-page" className="p-6 max-w-6xl mx-auto">
      <div className="flex items-center gap-3 mb-6">
        <Clapperboard className="h-7 w-7 text-amber-400" />
        <h1 className="text-xl font-bold text-zinc-100">Choreography</h1>
      </div>

      {/* Global Options */}
      <div className="bg-zinc-900 rounded-lg p-4 border border-zinc-800 mb-4">
        <div className="flex flex-wrap gap-4 items-center">
          <input
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            className="bg-zinc-800 text-zinc-200 border border-zinc-700 rounded-md px-3 py-1.5 text-sm w-48"
            placeholder="Video title"
          />
          <label className="flex items-center gap-2 text-xs text-zinc-400 cursor-pointer">
            <input
              type="checkbox"
              checked={options.voiceover}
              onChange={(e) => setOptions((o) => ({ ...o, voiceover: e.target.checked }))}
            />
            Voiceover
          </label>
          <label className="flex items-center gap-2 text-xs text-zinc-400 cursor-pointer">
            <input
              type="checkbox"
              checked={options.music}
              onChange={(e) => setOptions((o) => ({ ...o, music: e.target.checked }))}
            />
            Music
          </label>
          <label className="flex items-center gap-2 text-xs text-zinc-400 cursor-pointer">
            <input
              type="checkbox"
              checked={options.subtitles}
              onChange={(e) => setOptions((o) => ({ ...o, subtitles: e.target.checked }))}
            />
            Subtitles
          </label>
          <label className="flex items-center gap-2 text-xs text-zinc-400 cursor-pointer">
            <input
              type="checkbox"
              checked={options.desktop_capture}
              onChange={(e) => setOptions((o) => ({ ...o, desktop_capture: e.target.checked }))}
            />
            Desktop
          </label>
          <label className="flex items-center gap-2 text-xs text-zinc-400 cursor-pointer">
            <input
              type="checkbox"
              checked={options.title_card}
              onChange={(e) => setOptions((o) => ({ ...o, title_card: e.target.checked }))}
            />
            Title Card
          </label>
          <select
            value={voiceName}
            onChange={(e) => setVoiceName(e.target.value)}
            className="bg-zinc-800 text-zinc-200 border border-zinc-700 rounded-md px-2 py-1.5 text-xs"
          >
            <option value="heart">Heart</option>
            <option value="sky">Sky</option>
            <option value="adam">Adam</option>
          </select>
        </div>
      </div>

      {/* Repo Selector + Generate */}
      <div className="bg-zinc-900 rounded-lg p-4 border border-zinc-800 mb-4 flex gap-3 items-center">
        <select
          value={repo}
          onChange={(e) => setRepo(e.target.value)}
          className="bg-zinc-800 text-zinc-200 border border-zinc-700 rounded-md px-3 py-1.5 text-sm flex-1"
        >
          <option value="">Select target repo...</option>
          {Object.entries(categorizedRepos).map(([cat, repos]) => (
            <optgroup key={cat} label={cat}>
              {repos.map((r) => (
                <option key={r} value={r}>
                  {r}
                </option>
              ))}
            </optgroup>
          ))}
        </select>
        <button
          onClick={handleGenerate}
          disabled={!repo}
          className="flex items-center gap-2 px-4 py-2 bg-amber-600 text-white rounded-md text-sm hover:bg-amber-500 disabled:opacity-50 cursor-pointer"
        >
          <Send className="h-4 w-4" /> Generate
        </button>
      </div>

      {/* Step Timeline */}
      <div className="grid grid-cols-3 gap-4">
        <div className="col-span-2">
          <div className="flex items-center justify-between mb-3">
            <span className="text-sm font-semibold text-zinc-400 uppercase tracking-wide">
              Timeline ({steps.length} steps)
            </span>
            <div className="flex gap-1 flex-wrap">
              {(
                [
                  "goto",
                  "click",
                  "type",
                  "wait",
                  "say",
                  "capture_window",
                  "transition",
                  "sfx",
                  "text_overlay",
                  "obs_scene",
                  "end",
                ] as StepType[]
              ).map((t) => {
                const tmpl = STEP_TEMPLATES[t];
                return (
                  <button
                    key={t}
                    onClick={() => addStep(t)}
                    className="flex items-center gap-1 px-2 py-1 rounded text-xs text-zinc-400 hover:text-white hover:bg-zinc-800 cursor-pointer border border-zinc-800"
                  >
                    <tmpl.icon className="h-3 w-3" /> {tmpl.label}
                  </button>
                );
              })}
            </div>
          </div>

          <div className="space-y-2">
            {steps.map((step, i) => {
              const tmpl = STEP_TEMPLATES[step.action];
              const Icon = tmpl.icon;
              return (
                <div
                  key={step.id}
                  className={`bg-zinc-900 rounded-lg border-l-4 ${tmpl.color} border border-zinc-800 p-3`}
                >
                  <div className="flex items-center gap-2 mb-2">
                    <span className="text-xs text-zinc-600 w-5">{i + 1}</span>
                    <Icon className="h-4 w-4 text-zinc-400" />
                    <span className="text-sm font-medium text-zinc-200">{tmpl.label}</span>
                    <div className="ml-auto flex gap-1">
                      <button
                        onClick={() => moveStep(i, -1)}
                        disabled={i === 0}
                        className="p-1 rounded text-zinc-500 hover:text-white hover:bg-zinc-800 disabled:opacity-30 cursor-pointer"
                      >
                        <ArrowUp className="h-3 w-3" />
                      </button>
                      <button
                        onClick={() => moveStep(i, 1)}
                        disabled={i === steps.length - 1}
                        className="p-1 rounded text-zinc-500 hover:text-white hover:bg-zinc-800 disabled:opacity-30 cursor-pointer"
                      >
                        <ArrowDown className="h-3 w-3" />
                      </button>
                      <button
                        onClick={() => removeStep(step.id)}
                        className="p-1 rounded text-zinc-500 hover:text-red-400 cursor-pointer"
                      >
                        <Trash2 className="h-3 w-3" />
                      </button>
                    </div>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {tmpl.fields.includes("url") && (
                      <Field
                        label="URL"
                        value={step.url || ""}
                        onChange={(v) => updateStep(step.id, "url", v)}
                        placeholder="http://..."
                      />
                    )}
                    {tmpl.fields.includes("target") && (
                      <Field
                        label="Target"
                        value={step.target || ""}
                        onChange={(v) => updateStep(step.id, "target", v)}
                        placeholder="window / selector"
                      />
                    )}
                    {tmpl.fields.includes("text") && (
                      <Field
                        label="Text"
                        value={step.text || ""}
                        onChange={(v) => updateStep(step.id, "text", v)}
                        placeholder="text content"
                      />
                    )}
                    {tmpl.fields.includes("say") && options.voiceover && (
                      <Field
                        label="Narration"
                        value={step.say || ""}
                        onChange={(v) => updateStep(step.id, "say", v)}
                        placeholder="spoken text..."
                        wide
                      />
                    )}
                    {tmpl.fields.includes("scene") && (
                      <Field
                        label="OBS Scene"
                        value={step.scene || ""}
                        onChange={(v) => updateStep(step.id, "scene", v)}
                        placeholder="talking-head / screen-only"
                      />
                    )}
                    {tmpl.fields.includes("wait") && (
                      <NumberField
                        label="Wait (s)"
                        value={step.wait ?? 2}
                        onChange={(v) => updateStep(step.id, "wait", v)}
                      />
                    )}
                    {tmpl.fields.includes("duration") && (
                      <NumberField
                        label="Duration (s)"
                        value={step.duration ?? 2}
                        onChange={(v) => updateStep(step.id, "duration", v)}
                      />
                    )}
                    {(tmpl.fields.includes("x") || tmpl.fields.includes("y")) && (
                      <>
                        <NumberField
                          label="X"
                          value={step.x ?? 0}
                          onChange={(v) => updateStep(step.id, "x", v)}
                        />
                        <NumberField
                          label="Y"
                          value={step.y ?? 0}
                          onChange={(v) => updateStep(step.id, "y", v)}
                        />
                      </>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* YAML Preview */}
        <div>
          <span className="text-sm font-semibold text-zinc-400 uppercase tracking-wide mb-2 block">
            Script Preview
          </span>
          <pre className="bg-zinc-950 rounded-lg border border-zinc-800 p-3 text-xs text-zinc-400 font-mono overflow-auto max-h-[75vh]">
            {yamlPreview}
          </pre>
        </div>
      </div>
    </div>
  );
}

function Field({
  label,
  value,
  onChange,
  placeholder,
  wide,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
  wide?: boolean;
}) {
  return (
    <div className={`${wide ? "w-full" : "w-44"}`}>
      <label className="text-xs text-zinc-500 mb-0.5 block">{label}</label>
      <input
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="w-full bg-zinc-800 text-zinc-200 border border-zinc-700 rounded px-2 py-1 text-xs placeholder-zinc-600"
      />
    </div>
  );
}

function NumberField({
  label,
  value,
  onChange,
}: {
  label: string;
  value: number;
  onChange: (v: number) => void;
}) {
  return (
    <div className="w-20">
      <label className="text-xs text-zinc-500 mb-0.5 block">{label}</label>
      <input
        type="number"
        min={0}
        max={300}
        value={value}
        onChange={(e) => onChange(Number.parseInt(e.target.value, 10) || 0)}
        className="w-full bg-zinc-800 text-zinc-200 border border-zinc-700 rounded px-2 py-1 text-xs"
      />
    </div>
  );
}
