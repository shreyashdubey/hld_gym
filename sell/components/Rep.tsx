"use client";

import { useCallback, useEffect, useRef, useState, type CSSProperties } from "react";
import { PROBES, RUBRIC, STEPS, STEP_MS, REP_TITLE, verdictFor } from "@/lib/rep";
import { RESERVE_URL } from "@/lib/links";
import { DiagramNarrow, DiagramWide } from "./Diagram";

type Phase = "idle" | "watching" | "locked" | "graded" | "done";

const PHASE_LABEL: Record<Phase, string> = {
  idle: "watch",
  watching: "watch",
  locked: "locked",
  graded: "graded",
  done: "done",
};

export default function Rep() {
  const [phase, setPhase] = useState<Phase>("idle");
  /* 0, not -1: the scaffold (nodes + lifelines) is gated on step >= 0, so this
     is what puts a real diagram on screen at idle instead of an empty panel.
     The numbered steps still start at 1. */
  const [step, setStep] = useState(0);
  const [armed, setArmed] = useState(-1);
  const [recall, setRecall] = useState("");
  const [revealed, setRevealed] = useState(false);

  const timers = useRef<ReturnType<typeof setTimeout>[]>([]);
  const recallRef = useRef<HTMLTextAreaElement>(null);
  const probeRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    const t = timers.current;
    return () => t.forEach(clearTimeout);
  }, []);

  const start = useCallback(() => {
    const reduced =
      typeof window !== "undefined" &&
      window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    setPhase("watching");
    setStep(0);

    if (reduced) {
      setStep(STEPS.length);
      setArmed(STEPS.length);
      timers.current.push(setTimeout(() => setPhase("locked"), 1200));
      return;
    }

    let t = 700;
    STEPS.forEach((_, i) => {
      timers.current.push(
        setTimeout(() => {
          setStep(i + 1);
          timers.current.push(setTimeout(() => setArmed(i + 1), 520));
        }, t),
      );
      t += STEP_MS;
    });
    timers.current.push(setTimeout(() => setPhase("locked"), t + 400));
  }, []);

  useEffect(() => {
    if (phase === "locked") recallRef.current?.focus();
    if (phase === "graded") probeRef.current?.focus();
  }, [phase]);

  const hits = RUBRIC.map((k) => ({ label: k.label, ok: k.re.test(recall) }));
  const score = hits.filter((h) => h.ok).length;

  const showDiagram = phase === "idle" || phase === "watching" || phase === "done";

  return (
    <div className="rep">
      <div className="repTag">
        <span>{REP_TITLE}</span>
        <span className="phase">{PHASE_LABEL[phase]}</span>
      </div>

      <div className="repBody">
        <div className={`stage${phase === "idle" ? " dgIdle" : ""}`}>
          {showDiagram ? (
            <>
              <svg width="0" height="0" aria-hidden="true" style={{ position: "absolute" }}>
                <defs>
                  <marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5"
                    markerWidth="7" markerHeight="7" orient="auto-start-reverse">
                    <path d="M0,0 L10,5 L0,10 z" className="dgArrowhead" />
                  </marker>
                </defs>
              </svg>

              <DiagramWide step={step} armed={armed} />
              <DiagramNarrow step={step} armed={armed} />

              <p className="narr" aria-live="polite">
                {phase === "done" ? (
                  <>
                    <span className="n">✓</span> · here it is again. compare it against what you
                    actually wrote.
                  </>
                ) : step >= 1 && step <= STEPS.length ? (
                  <>
                    <span className="n">{step}</span> · {STEPS[step - 1]}
                  </>
                ) : null}
              </p>
            </>
          ) : (
            <div className="locked">
              <div className="big">That’s it. It’s gone.</div>
              <div className="sub">
                no scrolling back. this is the part that does the work. you cannot feel fluent
                about a diagram that isn’t on the screen.
              </div>
            </div>
          )}
        </div>

        {phase === "idle" && (
          <div className="btnRow">
            <button className="btn" onClick={start}>
              watch the rep · 13s
            </button>
            <span className="hint">then it gets locked</span>
          </div>
        )}

        {phase === "watching" && (
          <div className="btnRow">
            <button className="btn" disabled>
              watching…
            </button>
            <span className="hint">don’t take notes. that’s the whole point.</span>
          </div>
        )}

        {phase === "locked" && (
          <div>
            <label className="q" htmlFor="recall">
              Rebuild it. Name every step of the read path, in order, and say what the app is
              responsible for.
            </label>
            <textarea
              id="recall"
              ref={recallRef}
              value={recall}
              onChange={(e) => setRecall(e.target.value)}
              placeholder="Write it the way you’d say it to an interviewer…"
            />
            <div className="btnRow">
              <button className="btn" onClick={() => setPhase("graded")}>
                submit, no going back
              </button>
              <span className="hint">rough and honest beats polished and looked-up</span>
            </div>
          </div>
        )}

        {(phase === "graded" || phase === "done") && (
          <div>
            <div className="score">
              <div className="scoreH">
                recall · {score} of {RUBRIC.length}
              </div>
              <ul>
                {hits.map((h, i) => (
                  <li
                    key={h.label}
                    className={h.ok ? "hit" : "miss"}
                    style={{ "--i": i } as CSSProperties}
                  >
                    <span className="mk">{h.ok ? "✓" : "✕"}</span>
                    <span>{h.label}</span>
                  </li>
                ))}
              </ul>
              <div className="scoreVerdict">
                {verdictFor(score, RUBRIC.length, !recall.trim())}
              </div>
            </div>

            <div className="probe">
              <div className="probeWho">the interviewer, three follow-ups</div>
              {PROBES.map((p, i) => (
                <div key={p.q}>
                  <label className="q" htmlFor={`p${i}`}>
                    {p.q}
                  </label>
                  <textarea id={`p${i}`} rows={3} ref={i === 0 ? probeRef : undefined} />
                  {revealed && (
                    <div className="model">
                      <div className="lbl">what the chapter says</div>
                      <p>{p.a}</p>
                    </div>
                  )}
                  {i < PROBES.length - 1 && <div className="probeGap" />}
                </div>
              ))}

              {!revealed ? (
                <div className="btnRow">
                  <button
                    className="btn"
                    onClick={() => {
                      setRevealed(true);
                      setPhase("done");
                      setStep(STEPS.length);
                      setArmed(STEPS.length);
                    }}
                  >
                    show me what I missed
                  </button>
                </div>
              ) : (
                <>
                  <p className="hint" style={{ marginTop: 18 }}>
                    that was one rep. the sprint is 197 of them in thirty days, one for every
                    diagram in the book, and the diagram is different every time.
                  </p>
                  <div className="btnRow">
                    <a className="btn" href={RESERVE_URL} target="_blank" rel="noopener">
                      reserve a seat for $19
                    </a>
                    <a className="btn ghost" href="/book/">
                      read the book instead, free
                    </a>
                  </div>
                </>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
