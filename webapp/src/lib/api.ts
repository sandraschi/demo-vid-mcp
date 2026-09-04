// The packaged Tauri app serves the webapp from the `tauri://localhost`
// origin, not from the backend's own http://127.0.0.1:11134 - a relative
// fetch("/api/...") resolves against tauri://localhost (Tauri's asset
// protocol, which 404s on API paths) instead of reaching the backend. In
// dev mode (`bun run dev`), Vite's proxy makes relative paths work, which
// is why this went unnoticed until testing the actual packaged installer.
// tauri.conf.json's CSP already whitelists http://127.0.0.1:11134 in
// connect-src for exactly this reason.
const TAURI_BACKEND_ORIGIN = "http://127.0.0.1:11134";

function isTauriRuntime(): boolean {
  return typeof window !== "undefined" && "__TAURI_INTERNALS__" in window;
}

export const API_BASE = isTauriRuntime() ? TAURI_BACKEND_ORIGIN : "";

/** Prefix an "/api/..." (or "/videos/...", "/mcp/...") path with the backend origin when running inside Tauri; relative otherwise (dev server proxy). */
export function apiUrl(path: string): string {
  return `${API_BASE}${path}`;
}
