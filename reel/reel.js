/**
 * Shared timeline machinery for every reel.
 *
 * THE ONE RULE: a scene is a pure function of t. No CSS transitions, no CSS
 * animations, no setTimeout. render(t) computes every visual value from the
 * clock, so seeking is exact and the recorder can step 60 deterministic frames
 * a second instead of racing a wall clock and dropping some.
 */
"use strict";

const $ = (id) => document.getElementById(id);

/* ---- easing and windows: every visual value comes through one of these ---- */
const clamp = (v, a, b) => (v < a ? a : v > b ? b : v);
const outCubic = (p) => 1 - Math.pow(1 - p, 3);

/* d = 0 means "instant, already there" — the case that matters at t=0, where
   (t-a)/d would otherwise be 0/d = 0 and leave the opening card invisible on
   the one frame every feed uses as the thumbnail. */
const raw = (t, a, d) => (d <= 0 ? (t >= a ? 1 : 0) : clamp((t - a) / d, 0, 1));
const es = (t, a, d) => outCubic(raw(t, a, d));

/* visible between `tin` and `tout`, with a fade on each end */
const win = (t, tin, tout, fin = 240, fout = 200) =>
  Math.min(raw(t, tin, fin), 1 - raw(t, tout, fout));

const lerp = (a, b, p) => a + (b - a) * p;
const mix = (t, a, d, from, to) => lerp(from, to, es(t, a, d));

const op = (id, v) => { $(id).style.opacity = v; };
const txt = (id, s) => { const e = $(id); if (e.textContent !== s) e.textContent = s; };

/* Swap a node's state class without disturbing whatever else it carries. */
const state = (id, cls) => {
  const e = $(id);
  e.classList.remove("nHot", "nGood", "nBad");
  if (cls) e.classList.add(cls);
};

/**
 * Wires up a set of straight edges.
 *
 * Lengths come from the endpoints, never getTotalLength(): a hidden or
 * zero-progress element measures 0, which is the trap the product's own docs
 * call out. Straight lines make the measurement unnecessary.
 *
 * Each entry `id: [x1, y1, x2, y2]` expects a `<path id>` for the line and a
 * `<path id=h+ID>` for its arrowhead, pre-rotated here so it can simply fade in.
 */
function edges(map) {
  const lens = {};
  for (const [id, [x1, y1, x2, y2]] of Object.entries(map)) {
    const el = $(id);
    if (!el) throw new Error(`reel.js: no element for edge "${id}"`);
    const len = Math.hypot(x2 - x1, y2 - y1);
    lens[id] = len;
    el.setAttribute("d", `M${x1} ${y1} L${x2} ${y2}`);
    el.style.strokeDasharray = len;
    const headEl = $("h" + id);
    if (headEl) {
      const ux = (x2 - x1) / len, uy = (y2 - y1) / len, s = 6;
      headEl.setAttribute("d",
        `M${x2} ${y2} L${x2 - ux * s - uy * s * 0.55} ${y2 - uy * s + ux * s * 0.55} ` +
        `L${x2 - ux * s + uy * s * 0.55} ${y2 - uy * s - ux * s * 0.55} Z`);
    }
  }
  return {
    /** p = 0 fully retracted, 1 fully drawn */
    draw(id, p, colour) {
      const e = $(id);
      e.style.strokeDashoffset = lens[id] * (1 - p);
      e.style.opacity = p > 0 ? 1 : 0;
      e.style.stroke = colour || "";
      e.style.strokeWidth = colour ? 2.4 : "";
      const headEl = $("h" + id);
      if (headEl) headEl.style.fill = colour || "";
    },
    /** arrowheads paint at full opacity regardless of the dash pattern, so they
     *  must not arm until the line has nearly arrived */
    arm(id, p) { const h = $("h" + id); if (h) h.style.opacity = p; },
  };
}

/**
 * Registers the scene.
 *
 *   mount({ base, pace, beats, hookOut, stageOut, brandIn, render })
 *
 * `render(t, out)` must paint the complete frame for any t in any order — never
 * accumulate state between calls. It always receives **base** time, so the
 * timings inside a scene stay readable no matter how the reel is paced.
 *
 * `pace` stretches the whole clip from one number: at pace 3 a 15s scene plays
 * over 45s and every beat, fade and hold scales with it. Retiming forty
 * constants by hand is how a scene drifts out of sync with itself.
 *
 * `beats` are the scene's own named moments, in base time. The recorder and the
 * preview read them back scaled, so no tool holds a second copy of the timeline.
 *
 * Every reel shares one frame, painted here around the scene: the eyebrow and
 * hook at the top (opaque at t=0 by design — frame 0 is the thumbnail every
 * feed shows before anyone presses play, and this shipped black once), the
 * stage clearing for the kernel, then the kernel and the brand. `out` is that
 * stage fade; the scene must Math.min it into anything it keeps on screen
 * late. Three knobs cover the real variation between scenes, in base ms:
 * `hookOut` (when the hook leaves), `stageOut` (when the stage clears — the
 * kernel always follows 200ms later), `brandIn` (when the brand arrives).
 */
function mount({ base, pace = 1, beats = [],
                 hookOut = 1400, stageOut = 13200, brandIn = 14400, render }) {
  const T_TOTAL = base * pace;
  window.T_TOTAL = T_TOTAL;
  window.BEATS = beats.map(([t, name]) => [Math.round(t * pace), name]);

  /* The camera: one continuous 4.5% push across the whole clip. Constant motion
     under everything is most of the "shot on a camera" feel, and it never draws
     attention because it never changes speed. */
  const camera = $("camera");
  window.seek = (t) => {
    const c = clamp(t, 0, T_TOTAL);
    camera.style.transform =
      `scale(${1 + 0.045 * (c / T_TOTAL)}) translateY(${-6 * (c / T_TOTAL)}px)`;
    const bt = c / pace;
    op("eyebrow", win(bt, 0, 14400, 0, 300));
    op("hook",    win(bt, 0, hookOut, 0, 340));
    const out = 1 - raw(bt, stageOut, 400);        // the stage clears for the kernel
    $("stage").style.opacity = out;
    render(bt, out);
    $("kernel").style.opacity = win(bt, stageOut + 200, 15000, 520, 1);
    $("kernel").style.transform = `translateY(${mix(bt, stageOut + 200, 620, 14, 0)}px)`;
    op("brand", win(bt, brandIn, 15000, 400, 1));
  };

  window.seek(0);

  /* Preview in a normal browser. The recorder never reaches this because it
     seeks explicitly and Playwright sets navigator.webdriver; the preview page
     opts out through the flag, because it drives the clock from its own
     transport and two clocks fight. */
  if (!navigator.webdriver && !window.REEL_NO_AUTOPLAY) {
    const t0 = performance.now();
    const tick = () => {
      window.seek((performance.now() - t0) % (T_TOTAL + 900));
      requestAnimationFrame(tick);
    };
    requestAnimationFrame(tick);
  }
}
