"use client";

import { useCallback, useEffect, useRef, useState, type CSSProperties } from "react";
import { PROBES, RUBRIC, STEPS, STEP_MS, LEAD_MS, LOCK_MS, WATCH_S, REP_TITLE, verdictFor } from "@/lib/rep";
import { BOOK_URL, PRICE, RESERVE_URL } from "@/lib/links";
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
  const scoreRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const t = timers.current;
    return () => t.forEach(clearTimeout);
  }, []);

  /* No reduced-motion branch. An earlier one jumped straight to the finished
     diagram and locked 1.2s later, which removed the teaching, not the motion:
     the visitor was asked to rebuild a diagram they had seen for one second.
     Under prefers-reduced-motion the CSS already drops the draw transitions, so
     each step pops in complete on the same cadence with its narration line, and
     the button's promise holds. */
  const start = useCallback(() => {
    setPhase("watching");
    setStep(0);

    let t = LEAD_MS;
    STEPS.forEach((_, i) => {
      timers.current.push(
        setTimeout(() => {
          setStep(i + 1);
          timers.current.push(setTimeout(() => setArmed(i + 1), 520));
        }, t),
      );
      t += STEP_MS;
    });
    timers.current.push(setTimeout(() => setPhase("locked"), t + LOCK_MS));
  }, []);

  /* On grade, focus moves to the scorecard, not past it. Focusing the first
     probe textarea scrolled the browser to the probes and the rows ticking in
     above them, which is the whole reward, played off the top of the screen.
     The card takes focus (tabIndex -1) so a screen reader lands on the score
     too, and scroll-margin-top in the CSS keeps it clear of the sticky header. */
  useEffect(() => {
    if (phase === "locked") recallRef.current?.focus();
    if (phase === "graded") {
      const el = scoreRef.current;
      if (!el) return;
      el.focus({ preventScroll: true });
      const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
      el.scrollIntoView({ block: "start", behavior: reduced ? "auto" : "smooth" });
    }
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
              watch the rep · {WATCH_S}s
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
            <div className="score" ref={scoreRef} tabIndex={-1}>
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
            {/* Said where the score is read, not in a footnote: a senior engineer
                will probe the grader within a minute, and finding out on their
                own that it is keyword matching costs every other claim on the
                page. SYSTEM.md §10 has the measured failure cases. */}
            <p className="hint" style={{ marginTop: 10 }}>
              this demo scores by keyword against the chapter&rsquo;s six points. it catches what
              you left out entirely, not a wrong sentence with the right words in it.
            </p>

            <div className="probe">
              <div className="probeWho">the interviewer, three follow-ups</div>
              {/* The disclosure lives where the belief forms, not five screens
                  down in the offer: these three were written for this one
                  diagram, and the textareas below are read by nobody. */}
              <p className="hint" style={{ margin: "0 0 14px" }}>
                written in advance for this one diagram, and nothing you type here is graded:
                compare it against the chapter yourself. in the sprint the follow-ups are generated
                against your answer.
              </p>
              {PROBES.map((p, i) => (
                <div key={p.q}>
                  <label className="q" htmlFor={`p${i}`}>
                    {p.q}
                  </label>
                  <textarea id={`p${i}`} rows={3} />
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
                    show what the chapter says
                  </button>
                </div>
              ) : (
                <>
                  <p className="hint" style={{ marginTop: 18 }}>
                    that was one rep. the sprint is 197 of them in thirty days, one for every
                    diagram in the book, and the diagram is different every time.
                  </p>
                  {/* Sentence case, unlike the rep's own controls: these are the
                      page's two actions, the same ones the hero offers. */}
                  <div className="btnRow">
                    <a className="btn" href={RESERVE_URL} target="_blank" rel="noopener">
                      Reserve a seat for {PRICE}
                    </a>
                    <a className="btn ghost" href={BOOK_URL}>
                      Read the book instead, free
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
