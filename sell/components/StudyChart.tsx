"use client";

import { useEffect, useRef, type CSSProperties } from "react";

/* Roediger & Karpicke 2006, Experiment 2. Two learning conditions, two
   retention intervals, and the lines cross — which is the entire argument for
   the lock, and is far harder to hold in your head as four numbers in a
   sentence. The page claims diagrams beat prose for this material; making that
   claim in prose alone undercuts it.

   Figures are the paper's: at five minutes restudying leads 81 to 75, at one
   week testing leads 61 to 40. Checked against the source, not recalled.

   Series names sit in a legend under the plot rather than beside the line ends.
   Labels hanging off the right edge forced a wide viewBox, and a wide viewBox
   squeezed into a phone column renders its type at ~8px — the same failure the
   diagrams were redrawn to avoid. Everything now lives inside 360 units, so one
   drawing works at both widths. */

const V = { readEarly: 81, readLate: 40, recallEarly: 75, recallLate: 61 };

/* Plot box inside the 360x300 viewBox. */
const X1 = 86;
const X2 = 300;
const TOP = 34;
const BOT = 196;
const y = (pct: number) => BOT - (pct / 100) * (BOT - TOP);
const len = (yA: number, yB: number) => Math.round(Math.hypot(X2 - X1, yB - yA));

export default function StudyChart() {
  const ref = useRef<HTMLElement>(null);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;

    /* Classes are toggled on the DOM rather than held in React state, for two
       reasons. The undrawn state lives behind .chartArm, which only JavaScript
       ever adds — so with JS off, or if the observer never fires, the server's
       markup renders the chart complete instead of blank. And no setState in an
       effect means no react-hooks/set-state-in-effect to work around.

       The rAF matters: the chart may already be on screen at mount, and adding
       both classes in one frame gives the transition nothing to interpolate
       from. */
    el.classList.add("chartArm");

    let io: IntersectionObserver | undefined;
    const raf = requestAnimationFrame(() => {
      io = new IntersectionObserver(
        (entries) => {
          if (entries.some((e) => e.isIntersecting)) {
            el.classList.add("chartOn");
            io?.disconnect();
          }
        },
        { threshold: 0.3 },
      );
      io.observe(el);
    });

    return () => {
      cancelAnimationFrame(raf);
      io?.disconnect();
    };
  }, []);

  return (
    <figure className="chart" ref={ref}>
      <svg
        viewBox="0 0 360 300"
        role="img"
        aria-label="Recall after five minutes and after one week. Re-reading falls from 81 percent to 40 percent. Recall practice falls from 75 percent to 61 percent, overtaking it."
      >
        <line className="chAxis" x1={64} y1={TOP} x2={64} y2={BOT} />
        <line className="chAxis" x1={64} y1={BOT} x2={320} y2={BOT} />
        <line className="chRule" x1={64} y1={y(50)} x2={320} y2={y(50)} />

        <text className="chAxisTxt" x={56} y={TOP + 4} textAnchor="end">100%</text>
        <text className="chAxisTxt" x={56} y={y(50) + 4} textAnchor="end">50%</text>
        <text className="chAxisTxt" x={56} y={BOT + 4} textAnchor="end">0</text>

        <text className="chAxisTxt" x={X1} y={BOT + 20} textAnchor="middle">5 min later</text>
        <text className="chAxisTxt" x={X2} y={BOT + 20} textAnchor="middle">1 week later</text>

        {/* Read four times: starts ahead, collapses. */}
        <line
          className="chLine chRead"
          x1={X1} y1={y(V.readEarly)} x2={X2} y2={y(V.readLate)}
          style={{ "--len": len(y(V.readEarly), y(V.readLate)) } as CSSProperties}
        />
        {/* Recall three times: starts behind, holds, ends on top. */}
        <line
          className="chLine chRecall"
          x1={X1} y1={y(V.recallEarly)} x2={X2} y2={y(V.recallLate)}
          style={{ "--len": len(y(V.recallEarly), y(V.recallLate)) } as CSSProperties}
        />

        <circle className="chDot chReadDot" cx={X1} cy={y(V.readEarly)} r="4" />
        <circle className="chDot chReadDot" cx={X2} cy={y(V.readLate)} r="4" />
        <circle className="chDot chRecallDot" cx={X1} cy={y(V.recallEarly)} r="4" />
        <circle className="chDot chRecallDot" cx={X2} cy={y(V.recallLate)} r="4" />

        <text className="chVal" x={X1} y={y(V.readEarly) - 12} textAnchor="middle">81</text>
        <text className="chVal" x={X1} y={y(V.recallEarly) + 20} textAnchor="middle">75</text>
        <text className="chVal chDim" x={X2} y={y(V.readLate) + 20} textAnchor="middle">40</text>
        <text className="chVal chHot" x={X2} y={y(V.recallLate) - 12} textAnchor="middle">61</text>

        <line className="chLine chRead chKey" x1={64} y1={248} x2={92} y2={248} />
        <text className="chSeries chReadTxt" x={100} y={252}>read it 4 times</text>
        <line className="chLine chRecall chKey" x1={64} y1={274} x2={92} y2={274} />
        <text className="chSeries chRecallTxt" x={100} y={278}>recalled it 3 times</text>
      </svg>
      <figcaption>
        Roediger &amp; Karpicke 2006, experiment 2. Percentage of the passage still recalled.
      </figcaption>
    </figure>
  );
}
