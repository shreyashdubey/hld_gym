"use client";

import { useCallback, useEffect, useRef, useState, type CSSProperties } from "react";
import { PROBES, RUBRIC, STEPS, STEP_MS, LEAD_MS, LOCK_MS, WATCH_S, REP_TITLE, verdictFor } from "@/lib/rep";
import { BOOK_URL, PRICE, RESERVE_URL } from "@/lib/links";
import { appendTranscript } from "@/lib/dictation";
import { connectVoice, type VoiceSession } from "@/lib/voice";
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
  /* off/connecting/on/unavailable, not a boolean: "unavailable" carries its
     own honest copy (below), and collapsing it into "off" would let the
     control quietly imply the mic just hasn't been tried yet. */
  const [mic, setMic] = useState<"off" | "connecting" | "on" | "unavailable">("off");
  const [revealed, setRevealed] = useState(false);

  const timers = useRef<ReturnType<typeof setTimeout>[]>([]);
  const session = useRef<VoiceSession | null>(null);
  /* A generation counter, not a boolean: WATCH_S (~14s) is shorter than a
     connect can take to fail (measured ~15s against nothing listening), so a
     visitor can leave "locked", finish an entire second rep, and re-enter
     "locked" — rearming a boolean cancel flag back to false — before rep 1's
     stale connect settles. toggleMic captures the generation it started
     under; only a match after the await means the promise still belongs to
     the rep that opened it. Incremented on every entry to "locked" *and* on
     every teardown, so both a fresh rep and a mid-rep exit invalidate
     whatever was in flight before them. */
  const micGen = useRef(0);
  const recallRef = useRef<HTMLTextAreaElement>(null);
  const scoreRef = useRef<HTMLDivElement>(null);
  const stageRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const t = timers.current;
    return () => t.forEach(clearTimeout);
  }, []);

  /* The mic's lifetime is the "locked" phase, not the component's — Rep never
     unmounts. Entering locked arms a fresh connect; leaving it (submit, "run
     this one again", or an unmount that in practice never happens) tears down
     whatever is open or in flight. Without this a session left open after
     "submit, no going back" keeps calling setRecall, and hits/score below are
     recomputed from recall on every render, not snapshotted at grade time —
     so the score would keep changing after the one thing the lock promises is
     that it can't. A session left open across "run this one again" would
     silently pre-fill the next attempt's answer instead. */
  useEffect(() => {
    if (phase !== "locked") return;
    micGen.current++;
    return () => {
      // micGen is a plain counter, not a ref to a rendered DOM node — the
      // rule's stale-ref concern (and its "copy to a variable" fix) doesn't
      // apply, and nothing but this effect ever writes to it.
      // eslint-disable-next-line react-hooks/exhaustive-deps
      micGen.current++;
      if (session.current) {
        void session.current.disconnect().catch(() => {});
        session.current = null;
      }
      setMic("off");
    };
  }, [phase]);

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

  /* A second click always retries. A visitor whose service was slow to start,
     or who denied the mic prompt and changed their mind, is not left stuck on
     "unavailable" with no route back but a reload — see the disabled guard on
     the button below, which only locks out mid-connect. */
  const toggleMic = useCallback(async () => {
    if (session.current) {
      // Local state resets first, unconditionally: a hung or rejected
      // disconnect must not strand the toggle "on" with no way back.
      const live = session.current;
      session.current = null;
      setMic("off");
      void live.disconnect().catch(() => {});
      return;
    }
    setMic("connecting");
    const startedAs = micGen.current;
    try {
      const opened = await connectVoice({
        onMessage: (m) => {
          const msg = m as { type?: string; text?: string };
          if (msg?.type === "transcript" && msg.text) {
            setRecall((prev) => appendTranscript(prev, msg.text as string));
          }
        },
      });
      if (micGen.current !== startedAs) {
        /* This promise belongs to a rep that is no longer current — either
           the same "locked" was left mid-connect, or a whole second rep ran
           and re-entered "locked" before this one settled. Either way, close
           what just opened and touch nothing that belongs to the rep on
           screen now: no session.current, no setMic. */
        void opened.disconnect().catch(() => {});
        return;
      }
      session.current = opened;
      setMic("on");
    } catch {
      /* Mic denied, or the service is not running. Either way the keyboard is
         right there and still works — say so, do not show a dead control.
         Same generation check: a late failure from an abandoned rep must not
         paint "unavailable" over a rep the visitor never touched the mic in. */
      if (micGen.current === startedAs) setMic("unavailable");
    }
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
  const reduced = () =>
    typeof window !== "undefined" && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  /* Reveal: the diagram returns at the top of the panel, so the panel scrolls
     back to it. Without this the redraw and its "compare it against what you
     wrote" line played 1,000px above the viewport, and nobody saw the one
     moment the demo exists for. */
  const reveal = () => {
    setRevealed(true);
    setPhase("done");
    setStep(STEPS.length);
    setArmed(STEPS.length);
    stageRef.current?.scrollIntoView({ block: "start", behavior: reduced() ? "auto" : "smooth" });
  };

  /* Back to idle, same rep. A second attempt after reading the answers is the
     Roediger section's whole thesis, and there was no route to it but reload. */
  const again = (e: React.MouseEvent) => {
    e.preventDefault();
    timers.current.forEach(clearTimeout);
    timers.current.length = 0;   /* in place: the unmount cleanup holds this array */
    setRevealed(false);
    setRecall("");
    setArmed(-1);
    setStep(0);
    setPhase("idle");
    stageRef.current?.scrollIntoView({ block: "start", behavior: reduced() ? "auto" : "smooth" });
  };

  return (
    <div className="rep">
      <div className="repTag">
        <span>{REP_TITLE}</span>
        <span className="phase">{PHASE_LABEL[phase]}</span>
      </div>

      <div className="repBody">
        <div className={`stage${phase === "idle" ? " dgIdle" : ""}`} ref={stageRef}>
          {showDiagram ? (
            <>
              {/* width/height in the style too: .stage svg { width: 100% } beats
                  the attributes and stretched this to the page width. */}
              <svg width="0" height="0" aria-hidden="true" style={{ position: "absolute", width: 0, height: 0 }}>
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

        {/* The answer stays on the page after submit, read-only: the reveal
            is "the diagram beside what you wrote", and unmounting the textarea
            on grade left nothing to compare against. */}
        {phase !== "idle" && phase !== "watching" && (
          <div>
            <label className="q" htmlFor="recall">
              {phase === "locked"
                ? "Rebuild it. Name every step of the read path, in order, and say what the app is responsible for."
                : "What you wrote"}
            </label>
            <textarea
              id="recall"
              ref={recallRef}
              value={recall}
              readOnly={phase !== "locked"}
              onChange={(e) => setRecall(e.target.value)}
              placeholder={
                phase === "locked" ? "Write it the way you’d say it to an interviewer…" : "(left blank)"
              }
            />
            {phase === "locked" && (
              <div className="btnRow">
                <button
                  type="button"
                  className="dictate-btn"
                  onClick={toggleMic}
                  disabled={mic === "connecting"}
                  aria-pressed={mic === "on"}
                >
                  {mic === "on" ? "◉ listening" : mic === "connecting" ? "connecting…" : "◎ speak it"}
                </button>
                <span className="hint">
                  {mic === "unavailable"
                    ? "Voice is unavailable right now — type it instead, the scoring is identical."
                    : "Or type it. Both are graded the same way."}
                </span>
              </div>
            )}
            {phase === "locked" && (
              <div className="btnRow">
                <button className="btn" onClick={() => setPhase("graded")}>
                  submit, no going back
                </button>
                <span className="hint">rough and honest beats polished and looked-up</span>
              </div>
            )}
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
                  <button className="btn" onClick={reveal}>
                    show the diagram again, and what the chapter says
                  </button>
                </div>
              ) : (
                <>
                  {/* Score-aware, and consistent with step 06: a failed diagram
                      comes back in days, a nailed one in weeks. It used to say
                      "the diagram is different every time", which contradicted
                      the one thing the page says a chat window cannot do. */}
                  <p className="hint" style={{ marginTop: 18 }}>
                    that was one rep: {score} of {RUBRIC.length}. in the sprint{" "}
                    {score <= 4
                      ? "a score like that brings this diagram back within days"
                      : "a score like that sends this diagram weeks out"}
                    , and the next rep is a different diagram. 197 of them in thirty days, one for
                    every diagram in the book.{" "}
                    <a href="#rep" onClick={again}>
                      run this one again
                    </a>
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
