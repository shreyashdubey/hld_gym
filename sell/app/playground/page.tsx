"use client";

import { useCallback, useRef, useState } from "react";
import Board from "@/components/Board";
import { connectVoice, type VoiceSession } from "@/lib/voice";
import { extractGraph, type BoardElement, type BoardGraph } from "@/lib/board";
import { layoutTopology, type Topology } from "@/lib/layout";
import type { ExcalidrawImperativeAPI } from "@excalidraw/excalidraw/types";

/* idle/connecting/live plus three distinct terminal states, not one shared
   "unavailable" — a completed cap, a fatal service error, and a denied mic
   are three different things and this repo's first standing rule is never
   to claim the product does something it does not. Collapsing them (the
   bug this replaced) meant a *working* round that ran its full course and
   handed over to the coach reported the same "voice service unreachable"
   as a service that was never reachable at all.
     "denied"      — connectVoice() threw because the mic permission (or
                      device) never came up granted. The board still works.
     "unavailable" — connect failed some other way, or a live session ended
                      via RTVI's onError (a relayed service error) rather
                      than a clean close.
     "ended"       — a live session's connection closed on its own with no
                      error ahead of it — today, only the session cap's own
                      cut, which the interviewer has already handed the
                      coach's walkthrough ahead of. Not a failure. */
type PlaygroundState = "idle" | "connecting" | "live" | "ended" | "unavailable" | "denied";

export default function PlaygroundPage() {
  const [state, setState] = useState<PlaygroundState>("idle");
  const [said, setSaid] = useState<string[]>([]);
  const [backfill, setBackfill] = useState<BoardGraph | null>(null);
  const session = useRef<VoiceSession | null>(null);
  const excalidrawAPI = useRef<ExcalidrawImperativeAPI | null>(null);

  const onGraphChange = useCallback((graph: BoardGraph) => {
    session.current?.send("board", { graph });
  }, []);

  /* The coach draws in its own lane, beside the candidate's work, never on top
     of it: offset past the right edge of everything already on the board.

     @excalidraw/excalidraw has a single entry point that touches `window` at
     module scope (see the Board.tsx comment on the dynamic Excalidraw import),
     so convertToExcalidrawElements is loaded here, at call time, rather than
     hoisted to a module-scope import — hoisting it crashes the static export's
     prerender of this page with "window is not defined". */
  const onDraw = useCallback(async (topology: Topology) => {
    const api = excalidrawAPI.current;
    if (!api) return;
    const { convertToExcalidrawElements } = await import("@excalidraw/excalidraw");
    const existing = api.getSceneElements();
    const rightEdge = existing.reduce((max, el) => Math.max(max, el.x + el.width), 0);
    const skeleton = layoutTopology(topology, rightEdge + 160);
    api.updateScene({
      elements: [...existing, ...convertToExcalidrawElements(skeleton as never)],
    });
  }, []);

  const start = useCallback(async () => {
    setState("connecting");
    try {
      const opened = await connectVoice({
        mode: "playground",
        onMessage: (m) => {
          const msg = m as { type?: string; text?: string; topology?: Topology };
          if (msg?.type === "transcript" && msg.text) setSaid((s) => [...s, msg.text!]);
          /* topology is a model tool-call payload, not user input — it arrives
             malformed eventually (missing nodes/edges, wrong types). Catch and
             drop rather than throwing into an unhandled rejection: nothing in
             onDraw mutates the scene before layoutTopology finishes, so a
             failed draw leaves the learner's board untouched. */
          if (msg?.type === "draw" && msg.topology) onDraw(msg.topology).catch(() => {});
        },
        onDisconnect: (reason) => {
          /* Fires later, only if this exact session ends on its own. reason
             distinguishes a fatal service error ("error", RTVI's onError
             fired first — see lib/voice.ts) from a clean server-initiated
             close with no error ahead of it ("ended" -- today, only the
             session cap's own cut, and by the time that fires the
             interviewer has already handed over to the coach). Only the
             former is reported as "unreachable"; a round that ran its
             course and ended on schedule is not a failure and must not
             read as one. */
          if (session.current !== opened) return;
          session.current = null;
          setState(reason === "error" ? "unavailable" : "ended");
        },
      });
      session.current = opened;
      setState("live");
      /* The coach otherwise opens deaf to whatever was drawn before "start" was
         clicked — the natural order for a visitor who draws first, then talks.
         Without this, the gate has already recorded that diagram's signature
         from the drawing itself, so it would never resend it on its own. */
      const elements = excalidrawAPI.current?.getSceneElements() ?? [];
      const graph = extractGraph(elements as readonly BoardElement[]);
      session.current.send("board", { graph });
      setBackfill(graph);
    } catch (err) {
      /* connectVoice() throws a plain Error("microphone unavailable") for
         exactly one reason: mediaState.mic never settled to "granted" --
         permission denied, or no device at all. Any other throw (the
         service unreachable, a bad SDP, connect() itself failing) is the
         generic case. Conflating the two is the bug this replaced: the
         spec requires a denied mic to say so out loud, not report a
         running board as a dead service. */
      const denied = err instanceof Error && err.message === "microphone unavailable";
      setState(denied ? "denied" : "unavailable");
    }
  }, [onDraw]);

  return (
    <main className="playground">
      <h1>Playground</h1>
      {state !== "live" && (
        <>
          <button type="button" className="btn" onClick={start} disabled={state === "connecting"}>
            {state === "denied"
              ? "microphone permission denied"
              : state === "unavailable"
                ? "voice service unreachable"
                : state === "ended"
                  ? "round ended — start another"
                  : "start the round"}
          </button>
          {/* Announced before the session starts, not when the cap bites --
              see playground/server.py's _enforce_cap and the design's "session
              cap, announced up front". No fixed number here: the cap is
              env-configurable (PLAYGROUND_SESSION_CAP_SECS) and this is a
              static export with no way to read that at build time, so the
              honest move is a claim that holds regardless of the configured
              value, not a number that can go stale the moment the env var
              changes -- see sell/PROGRESS.md. */}
          <p className="hint">
            {state === "denied"
              ? "The microphone permission was denied (or no mic is available). Allow it in your browser's site settings and try again — the board below still works either way, nothing will listen or talk until it's granted."
              : state === "unavailable"
                ? "The voice service isn't reachable right now. The board below still works on its own — try the round again once it's back."
                : state === "ended"
                  ? "That round ended — no error, just the connection closing on its own. Start another whenever you're ready."
                  : "Sessions run for a capped length. The interviewer hands over to the coach before time is up, so you always get the walkthrough."}
          </p>
        </>
      )}
      <Board
        onGraphChange={onGraphChange}
        apiRef={(api) => {
          excalidrawAPI.current = api;
        }}
        syncGraph={backfill}
      />
      <ol className="said">{said.map((s, i) => <li key={i}>{s}</li>)}</ol>
    </main>
  );
}
