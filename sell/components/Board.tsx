"use client";

import dynamic from "next/dynamic";
import { useCallback, useRef } from "react";
import { extractGraph, graphSignature, type BoardElement, type BoardGraph } from "@/lib/board";
import type { ExcalidrawImperativeAPI } from "@excalidraw/excalidraw/types";
import "@excalidraw/excalidraw/index.css";

/* Excalidraw touches window at module scope, so it cannot be server-rendered.
   ssr:false also keeps its ~1MB out of every other route's bundle. */
const Excalidraw = dynamic(
  async () => (await import("@excalidraw/excalidraw")).Excalidraw,
  { ssr: false, loading: () => <div className="board-loading">loading the board…</div> },
);

const SETTLE_MS = 800;

export default function Board({
  onGraphChange,
  apiRef,
}: {
  onGraphChange: (graph: BoardGraph) => void;
  apiRef: (api: ExcalidrawImperativeAPI) => void;
}) {
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const lastSig = useRef<string>("");

  /* Debounced, and gated on the signature: this is VAD for the board. Sending
     on every stroke would bury the coach in noise and bill for it. */
  const onChange = useCallback(
    (elements: readonly unknown[]) => {
      if (timer.current) clearTimeout(timer.current);
      timer.current = setTimeout(() => {
        const graph = extractGraph(elements as readonly BoardElement[]);
        const sig = graphSignature(graph);
        if (sig === lastSig.current) return;
        lastSig.current = sig;
        onGraphChange(graph);
      }, SETTLE_MS);
    },
    [onGraphChange],
  );

  return (
    <div className="board">
      <Excalidraw onChange={onChange} excalidrawAPI={apiRef} />
    </div>
  );
}
