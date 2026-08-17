/* Viewer preferences that live on <html> as data attributes, written before
   first paint by the init script below and cycled by the header toggles.
   Both follow the same shape: an ordered list of values, a name per value, and
   a localStorage key. */

export const THEMES = ["light", "dark", "manim"] as const;
export type Theme = (typeof THEMES)[number];

export const THEME_GLYPH: Record<Theme, string> = {
  light: "◐",
  dark: "◑",
  manim: "π",
};

export const THEME_NAME: Record<Theme, string> = {
  light: "Paper",
  dark: "Blueprint",
  manim: "Manim",
};

export const THEME_KEY = "hldsprint_theme";

/* Text size. The values are multipliers applied to reading text in globals.css
   through --fs; the names are what the button says. Three steps and nothing
   finer on purpose — a slider invites fiddling, and this is a control someone
   sets once and forgets. */
export const SIZES = ["m", "l", "xl"] as const;
export type Size = (typeof SIZES)[number];

export const SIZE_NAME: Record<Size, string> = {
  m: "Normal",
  l: "Large",
  xl: "Largest",
};

export const SIZE_KEY = "hldsprint_size";

/* Runs before first paint, inlined into <head>. Without it the server-rendered
   page paints the default palette at the default size and then jumps once React
   hydrates. Kept dependency-free and tiny because it blocks rendering by
   design.

   The hldgym_v1 fallback: the book shares this origin and keeps its theme under
   that key. A reader arriving from a Blueprint book should not land on a Paper
   page, so the book's choice is read before the OS is. Once a toggle is used
   here, this page's own key wins, as before. */
export const PREFS_INIT_SCRIPT = `
(function(){
  try {
    var d = document.documentElement, s = localStorage;
    var t = s.getItem(${JSON.stringify(THEME_KEY)});
    if (!t) { try { t = JSON.parse(s.getItem('hldgym_v1') || '{}').theme || null; } catch (e) {} }
    if (${JSON.stringify(THEMES)}.indexOf(t) < 0) {
      t = matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    }
    d.dataset.theme = t;
    var f = s.getItem(${JSON.stringify(SIZE_KEY)});
    d.dataset.fs = ${JSON.stringify(SIZES)}.indexOf(f) < 0 ? 'm' : f;
  } catch (e) {}
})();
`.trim();
