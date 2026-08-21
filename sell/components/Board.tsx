"use client";

import dynamic from "next/dynamic";
import { useCallback, useEffect, useRef } from "react";
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

/* The gate starts truthful: an untouched board really does sign as the empty
   graph, not as "". With SETTLE_MS-scale debounce and a connect that can in
   principle resolve faster than that, starting the ref at a value no real
   graph produces risks a spurious empty-graph send racing the cold-start
   timer. */
const EMPTY_SIG = graphSignature({ nodes: [], edges: [], unreadable: 0 });

export default function Board({
  onGraphChange,
  apiRef,
  syncGraph,
}: {
  onGraphChange: (graph: BoardGraph) => void;
  apiRef: (api: ExcalidrawImperativeAPI) => void;
  /** A graph the caller has already sent by some other path (the connect-time
      backfill in the page). Adopting its signature here stops the next
      debounce tick from re-sending it as if it were a fresh change. */
  syncGraph?: BoardGraph | null;
}) {
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const lastSig = useRef<string>(EMPTY_SIG);

  useEffect(() => {
    if (syncGraph) lastSig.current = graphSignature(syncGraph);
  }, [syncGraph]);

  // Otherwise a pending debounce outlives the component and fires into a
  // handler for a page that is no longer showing the board.
  useEffect(() => () => {
    if (timer.current) clearTimeout(timer.current);
  }, []);

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
