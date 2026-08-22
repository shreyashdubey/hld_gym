"use client";

import { useSyncExternalStore } from "react";
import {
  SIZES,
  SIZE_KEY,
  SIZE_NAME,
  THEMES,
  THEME_GLYPH,
  THEME_KEY,
  THEME_NAME,
} from "@/lib/prefs";

/* Both header toggles own a value that React does not: the inline script in
   layout.tsx writes it onto <html> before first paint, so the DOM is the store
   and useSyncExternalStore is the primitive for reading one. Holding it in
   useState instead would either flash the wrong value or mismatch on hydration.

   getServerSnapshot returns null, so the server renders a neutral placeholder
   and React swaps in the real label once hydrated. */

/* One store per attribute, created once at module scope, so
   useSyncExternalStore gets stable references instead of resubscribing on
   every render. */
function makeStore(attr: string, key: string) {
  const listeners = new Set<() => void>();
  return {
    subscribe(cb: () => void) {
      listeners.add(cb);
      return () => {
        listeners.delete(cb);
      };
    },
    get: () => document.documentElement.dataset[attr] ?? "",
    set(v: string) {
      document.documentElement.dataset[attr] = v;
      try {
        localStorage.setItem(key, v);
      } catch {
        /* private mode — the toggle still works for this page view */
      }
      listeners.forEach((l) => l());
    },
  };
}

const themeStore = makeStore("theme", THEME_KEY);
const sizeStore = makeStore("fs", SIZE_KEY);

function useCycle<T extends string>(store: ReturnType<typeof makeStore>, values: readonly T[]) {
  const raw = useSyncExternalStore(store.subscribe, store.get, () => null);
  const value = raw && (values as readonly string[]).includes(raw) ? (raw as T) : null;

  return {
    value,
    cycle: () => {
      const i = value ? values.indexOf(value) : 0;
      store.set(values[(i + 1) % values.length]);
    },
  };
}

export function ThemeToggle() {
  const { value, cycle } = useCycle(themeStore, THEMES);
  const label = value ? `Theme: ${THEME_NAME[value]}. Switch theme` : "Switch theme";

  return (
    <button className="prefBtn" onClick={cycle} aria-label={label} title={label}>
      <span className="pg" aria-hidden="true">
        {value ? THEME_GLYPH[value] : "◐"}
      </span>
      <span className="pn">{value ? THEME_NAME[value].toLowerCase() : "theme"}</span>
    </button>
  );
}

export function TextSizeToggle() {
  const { value, cycle } = useCycle(sizeStore, SIZES);
  const label = value ? `Text size: ${SIZE_NAME[value]}. Change text size` : "Change text size";

  return (
    <button className="prefBtn" onClick={cycle} aria-label={label} title={label}>
      <span className="pg" aria-hidden="true">
        aA
      </span>
      <span className="pn">{value ? SIZE_NAME[value].toLowerCase() : "text"}</span>
    </button>
  );
}
