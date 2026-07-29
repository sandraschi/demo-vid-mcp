import { create } from "zustand";

interface LLMState {
  provider: string;
  model: string;
  setProvider: (p: string) => void;
  setModel: (m: string) => void;
}

export const useLLMStore = create<LLMState>((set) => ({
  provider: localStorage.getItem("llm_provider") || "",
  model: localStorage.getItem("llm_model") || "",
  setProvider: (p) => { localStorage.setItem("llm_provider", p); set({ provider: p }); },
  setModel: (m) => { localStorage.setItem("llm_model", m); set({ model: m }); },
}));
