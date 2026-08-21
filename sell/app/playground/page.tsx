"use client";

import { useCallback, useRef, useState } from "react";
import Board from "@/components/Board";
import { connectVoice, type VoiceSession } from "@/lib/voice";
import { extractGraph, type BoardElement, type BoardGraph } from "@/lib/board";
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

  const start = useCallback(async () => {
    setState("connecting");
    try {
      session.current = await connectVoice({
        mode: "playground",
        onMessage: (m) => {
          const msg = m as { type?: string; text?: string };
          if (msg?.type === "transcript" && msg.text) setSaid((s) => [...s, msg.text!]);
        },
      });
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
  }, []);

  return (
    <main className="playground">
      <h1>Playground</h1>
      {state !== "live" && (
        <button type="button" className="btn" onClick={start} disabled={state === "connecting"}>
          {state === "unavailable" ? "voice service unreachable" : "start the round"}
        </button>
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
