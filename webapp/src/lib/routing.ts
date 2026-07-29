import { useState, useCallback } from "react";

export function useSearchParams() {
  const [params] = useState(() => new URLSearchParams(window.location.search));
  return [params, useCallback((k: string, v: string) => {
    const sp = new URLSearchParams(window.location.search);
    sp.set(k, v);
    window.history.replaceState({}, "", `?${sp.toString()}`);
  }, [])] as const;
}
