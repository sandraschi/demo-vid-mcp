import { create } from "zustand";
import { apiUrl } from "../lib/api";

const BACKOFF_MS = [1000, 2000, 4000, 8000, 16000];
const STEADY_MS = 10000;
const HEALTH_URL = apiUrl("/api/health");

interface BackendState {
  backendOk: boolean | null;
  restarting: boolean;
  lastChecked: number | null;
  version: string | null;
  refresh: () => Promise<void>;
  restart: () => Promise<void>;
  init: () => () => void;
}

let initialized = false;
let pollTimer: ReturnType<typeof setTimeout> | null = null;
let failureStreak = 0;

export const useBackendStore = create<BackendState>((set, get) => ({
  backendOk: null,
  restarting: false,
  lastChecked: null,
  version: null,

  refresh: async () => {
    let ok = false;
    let version: string | null = null;
    try {
      const r = await fetch(HEALTH_URL);
      ok = r.ok;
      if (ok) {
        const d = await r.json();
        if (typeof d?.version === "string") version = d.version;
      }
    } catch {
      ok = false;
    }
    set((state) => ({
      backendOk: ok,
      lastChecked: Date.now(),
      restarting: ok ? false : state.restarting,
      version: version ?? state.version,
    }));
    failureStreak = ok ? 0 : failureStreak + 1;
    scheduleNextPoll();
  },

  restart: async () => {
    set({ restarting: true });
    try {
      const { invoke } = await import("@tauri-apps/api/core");
      await invoke("start_backend");
      // The "backend-status" ready event (or the next poll) will clear
      // `restarting`; give the process a moment before the next HTTP probe.
      setTimeout(() => get().refresh(), 1500);
    } catch {
      // Not running inside Tauri (dev browser) - nothing to invoke, fall
      // back to a plain HTTP re-check so the button doesn't spin forever.
      set({ restarting: false });
      get().refresh();
    }
  },

  init: () => {
    if (initialized) {
      return () => {};
    }
    initialized = true;

    get().refresh();

    let unlisten: (() => void) | undefined;
    (async () => {
      try {
        const { listen } = await import("@tauri-apps/api/event");
        unlisten = await listen<string>("backend-status", (event) => {
          if (event.payload === "ready") {
            failureStreak = 0;
            get().refresh();
          } else if (typeof event.payload === "string" && event.payload.startsWith("error:")) {
            set({ backendOk: false, restarting: false, lastChecked: Date.now() });
          }
        });
      } catch {
        // Not inside Tauri - HTTP polling (steady + backoff) covers it.
      }
    })();

    return () => {
      if (pollTimer) clearTimeout(pollTimer);
      if (unlisten) unlisten();
      initialized = false;
    };
  },
}));

function scheduleNextPoll() {
  if (pollTimer) clearTimeout(pollTimer);
  const delay =
    failureStreak > 0 ? BACKOFF_MS[Math.min(failureStreak - 1, BACKOFF_MS.length - 1)] : STEADY_MS;
  pollTimer = setTimeout(() => useBackendStore.getState().refresh(), delay);
}
