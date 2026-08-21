"use client";

import { useCallback, useRef, useState } from "react";
import Board from "@/components/Board";
import { connectVoice, type VoiceSession } from "@/lib/voice";
import type { BoardGraph } from "@/lib/board";
import type { ExcalidrawImperativeAPI } from "@excalidraw/excalidraw/types";

export default function PlaygroundPage() {
  const [state, setState] = useState<"idle" | "connecting" | "live" | "unavailable">("idle");
  const [said, setSaid] = useState<string[]>([]);
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
      />
      <ol className="said">{said.map((s, i) => <li key={i}>{s}</li>)}</ol>
    </main>
  );
}
