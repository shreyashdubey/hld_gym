"use client";

import type { CSSProperties } from "react";

/* Two hand-laid variants of the same sequence. The wide one is the book's
   original 720-unit drawing; the narrow one is redrawn at viewBox width 320 so
   its 11px labels still render near 11px on a phone instead of 4.5px.

   Both are always in the DOM and swapped with CSS. That is only safe because
   every line carries its draw length as --len, computed from its own endpoints
   — a getTotalLength() measurement would return 0 on the hidden variant. */

function Edge({
  x1, y1, x2, y2, arrow,
}: { x1: number; y1: number; x2: number; y2: number; arrow: boolean }) {
  const len = Math.round(Math.hypot(x2 - x1, y2 - y1));
  return (
    <line
      className="dgEdge dgDraw"
      x1={x1} y1={y1} x2={x2} y2={y2}
      markerEnd={arrow ? "url(#arrow)" : undefined}
      style={{ "--len": len } as CSSProperties}
    />
  );
}

/* A short bright segment that runs the length of a lifeline and fades out, on a
   slow loop, while the rep is idle. It is the whole reason the panel reads as a
   live instrument instead of an empty grey box before anyone presses play.

   pathLength="100" rescales all dash maths to a fixed 100 units, so one set of
   constant keyframes drives both the 171-unit wide lifeline and the 272-unit
   narrow one. It also sidesteps a real bug: a keyframe value of
   calc(-1 * (var(--len) + 26)) does not interpolate — the browser cannot
   resolve the var at parse time and falls back to a discrete jump, so the pulse
   teleported to the end instead of travelling. */
function Pulse({ x, y1, y2, i }: { x: number; y1: number; y2: number; i: number }) {
  return (
    <line
      className="dgPulse"
      x1={x} y1={y1} x2={x} y2={y2}
      pathLength={100}
      style={{ "--i": i } as CSSProperties}
    />
  );
}

const LABELS = [
  "1. GET product:88871",
  "2. miss",
  "3. run the expensive queries",
  "4. rows",
  "5. SET product:88871, ttl 300s",
];

type Props = { step: number; armed: number };

const on = (step: number, n: number) => (step >= n ? "dgOn" : "");

export function DiagramWide({ step, armed }: Props) {
  const rows: [number, number, number][] = [
    [95, 105, 365],
    [125, 365, 105],
    [160, 105, 625],
    [190, 625, 105],
    [222, 105, 365],
  ];
  const labelX = [150, 180, 280, 300, 140];
  return (
    <svg className="dgWide" viewBox="0 0 720 250" role="img"
      aria-label="Cache-aside read path on a miss">
      <g className={`dgScaffold ${on(step, 0)}`}>
        <rect className="dgNode dgPart" x="40" y="20" width="130" height="44" />
        <rect className="dgHalo" x="40" y="20" width="130" height="44" style={{ "--i": 0 } as CSSProperties} />
        <text className="dgTxt dgPart" x="72" y="47">App</text>
        <rect className="dgNodeAlt dgPart" x="300" y="20" width="130" height="44" />
        <rect className="dgHalo" x="300" y="20" width="130" height="44" style={{ "--i": 1 } as CSSProperties} />
        <text className="dgTxt dgPart" x="330" y="47">Cache</text>
        <rect className="dgNode dgPart" x="560" y="20" width="130" height="44" />
        <rect className="dgHalo" x="560" y="20" width="130" height="44" style={{ "--i": 2 } as CSSProperties} />
        <text className="dgTxt dgPart" x="600" y="47">DB</text>
        <Edge x1={105} y1={64} x2={105} y2={235} arrow={false} />
        <Edge x1={365} y1={64} x2={365} y2={235} arrow={false} />
        <Edge x1={625} y1={64} x2={625} y2={235} arrow={false} />
        <g className="dgPulses">
          <Pulse x={105} y1={64} y2={235} i={0} />
          <Pulse x={365} y1={64} y2={235} i={1} />
          <Pulse x={625} y1={64} y2={235} i={2} />
        </g>
      </g>
      {rows.map(([y, x1, x2], i) => (
        <g key={i} className={on(step, i + 1)}>
          <Edge x1={x1} y1={y} x2={x2} y2={y} arrow={armed >= i + 1} />
          <text className="dgTxtS dgPart" x={labelX[i]} y={y - 7}>{LABELS[i]}</text>
        </g>
      ))}
    </svg>
  );
}

export function DiagramNarrow({ step, armed }: Props) {
  const APP = 47, CACHE = 160, DB = 273;
  const rows: [number, number, number][] = [
    [100, APP, CACHE],
    [150, CACHE, APP],
    [200, APP, DB],
    [250, DB, APP],
    [300, APP, CACHE],
  ];
  return (
    <svg className="dgNarrow" viewBox="0 0 320 330" role="img"
      aria-label="Cache-aside read path on a miss">
      <g className={`dgScaffold ${on(step, 0)}`}>
        <rect className="dgNode dgPart" x="8" y="16" width="78" height="30" />
        <rect className="dgHalo" x="8" y="16" width="78" height="30" style={{ "--i": 0 } as CSSProperties} />
        <text className="dgTxt dgPart" x="30" y="36">App</text>
        <rect className="dgNodeAlt dgPart" x="121" y="16" width="78" height="30" />
        <rect className="dgHalo" x="121" y="16" width="78" height="30" style={{ "--i": 1 } as CSSProperties} />
        <text className="dgTxt dgPart" x="136" y="36">Cache</text>
        <rect className="dgNode dgPart" x="234" y="16" width="78" height="30" />
        <rect className="dgHalo" x="234" y="16" width="78" height="30" style={{ "--i": 2 } as CSSProperties} />
        <text className="dgTxt dgPart" x="262" y="36">DB</text>
        <Edge x1={APP} y1={46} x2={APP} y2={318} arrow={false} />
        <Edge x1={CACHE} y1={46} x2={CACHE} y2={318} arrow={false} />
        <Edge x1={DB} y1={46} x2={DB} y2={318} arrow={false} />
        <g className="dgPulses">
          <Pulse x={APP} y1={46} y2={318} i={0} />
          <Pulse x={CACHE} y1={46} y2={318} i={1} />
          <Pulse x={DB} y1={46} y2={318} i={2} />
        </g>
      </g>
      {rows.map(([y, x1, x2], i) => (
        <g key={i} className={on(step, i + 1)}>
          <Edge x1={x1} y1={y} x2={x2} y2={y} arrow={armed >= i + 1} />
          <text className="dgTxtS dgPart" x="8" y={y - 8}>{LABELS[i]}</text>
        </g>
      ))}
    </svg>
  );
}
