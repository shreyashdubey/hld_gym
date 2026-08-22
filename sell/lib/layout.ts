/* The model emits topology and never coordinates. A model placing shapes by
   hand produces a tangle, so layout lives here where it can be tested. */

import dagre from "@dagrejs/dagre";
import { COACH_AUTHOR } from "./board.ts";

export type Topology = {
  nodes: { id: string; label: string }[];
  edges: { from: string; to: string; label?: string }[];
};

type ExcalidrawSkeleton = {
  type: string;
  id?: string;
  x: number;
  y: number;
  width?: number;
  height?: number;
  label?: { text: string };
  start?: { id: string };
  end?: { id: string };
  customData?: { author: string };
};

const W = 160;
const H = 70;

export function layoutTopology(topology: Topology, offsetX: number): ExcalidrawSkeleton[] {
  if (!topology.nodes.length) return [];

  const g = new dagre.graphlib.Graph();
  g.setGraph({ rankdir: "LR", nodesep: 60, ranksep: 110 });
  g.setDefaultEdgeLabel(() => ({}));
  for (const n of topology.nodes) g.setNode(n.id, { width: W, height: H });

  const ids = new Set(topology.nodes.map((n) => n.id));
  /* An edge to a node the model never declared is a hallucinated endpoint.
     Dropping it beats drawing an arrow into empty space. */
  const edges = topology.edges.filter((e) => ids.has(e.from) && ids.has(e.to));
  for (const e of edges) g.setEdge(e.from, e.to);

  dagre.layout(g);

  /* label.text below makes convertToExcalidrawElements auto-generate a bound
     text child for each box (and each labelled arrow) — that child does not
     inherit customData.author from its container; only the box/arrow itself
     carries the coach tag. Harmless today only because extractGraph never
     walks text elements directly for exclusion — it filters nodes/edges by
     type first, and a label is looked up by containerId only for an id
     already in that filtered, coach-excluded set. If the extractor is ever
     widened to read text elements on their own, this reopens the exact bug
     the tagging exists to prevent: the coach reading its own diagram back as
     the learner's. */
  const boxes: ExcalidrawSkeleton[] = topology.nodes.map((n) => {
    const { x, y } = g.node(n.id);
    return {
      type: "rectangle",
      id: n.id,
      x: offsetX + x - W / 2,
      y: y - H / 2,
      width: W,
      height: H,
      label: { text: n.label },
      customData: { author: COACH_AUTHOR },
    };
  });

  const arrows: ExcalidrawSkeleton[] = edges.map((e) => ({
    type: "arrow",
    x: 0,
    y: 0,
    start: { id: e.from },
    end: { id: e.to },
    ...(e.label ? { label: { text: e.label } } : {}),
    customData: { author: COACH_AUTHOR },
  }));

  return [...boxes, ...arrows];
}
