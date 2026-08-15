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

type Store = {
  subscribe: (cb: () => void) => () => void;
  get: () => string;
  set: (v: string) => void;
};

/* One store per attribute, created once and reused, so useSyncExternalStore
   gets stable references instead of resubscribing on every render. */
const stores = new Map<string, Store>();

function storeFor(attr: string, key: string): Store {
  const existing = stores.get(attr);
  if (existing) return existing;

  let listeners: Array<() => void> = [];
  const store: Store = {
    subscribe(cb) {
      listeners.push(cb);
      return () => {
        listeners = listeners.filter((l) => l !== cb);
      };
    },
    get: () => document.documentElement.dataset[attr] ?? "",
    set(v) {
      document.documentElement.dataset[attr] = v;
      try {
        localStorage.setItem(key, v);
      } catch {
        /* private mode — the toggle still works for this page view */
      }
      listeners.forEach((l) => l());
    },
  };
  stores.set(attr, store);
  return store;
}

function useCycle<T extends string>(attr: string, key: string, values: readonly T[]) {
  const store = storeFor(attr, key);
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
  const { value, cycle } = useCycle("theme", THEME_KEY, THEMES);
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
  const { value, cycle } = useCycle("fs", SIZE_KEY, SIZES);
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
