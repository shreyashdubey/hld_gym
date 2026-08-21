"use client";

import { useCallback, useRef, useState } from "react";
import Board from "@/components/Board";
import { connectVoice, type VoiceSession } from "@/lib/voice";
import { extractGraph, type BoardElement, type BoardGraph } from "@/lib/board";
import { layoutTopology, type Topology } from "@/lib/layout";
import type { ExcalidrawImperativeAPI } from "@excalidraw/excalidraw/types";

export default function PlaygroundPage() {
  const [state, setState] = useState<"idle" | "connecting" | "live" | "unavailable">("idle");
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
        onDisconnect: () => {
          /* Fires later, only if this exact session ends on its own -- a
             server-initiated teardown (the session cap) or a fatal service
             error. A live-looking session that is already dead is exactly
             the failure this exists to close: drop back to the same honest
             "unreachable" state a failed connect shows, so the button and
             the cap-note reappear and typing is still the fallback. */
          if (session.current !== opened) return;
          session.current = null;
          setState("unavailable");
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
    } catch {
      setState("unavailable");
    }
  }, [onDraw]);

  return (
    <main className="playground">
      <h1>Playground</h1>
      {state !== "live" && (
        <>
          <button type="button" className="btn" onClick={start} disabled={state === "connecting"}>
            {state === "unavailable" ? "voice service unreachable" : "start the round"}
          </button>
          {/* Announced before the session starts, not when the cap bites --
              see playground/server.py's _enforce_cap and the design's "session
              cap, announced up front". .hint, not a new .cap-note rule: same
              muted mono note the rest of the page already uses (task 5). */}
          <p className="hint">
            Sessions run up to 12 minutes. The interviewer hands over to the coach before
            time is up, so you always get the walkthrough.
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
