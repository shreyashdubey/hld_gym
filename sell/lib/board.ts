/* The coach reads the board as a labelled graph, never as a screenshot. A graph
   is ~200 tokens, exact, and diffable — and "what changed" is the signal a coach
   that unsticks people runs on. A snapshot has no memory of the previous frame. */

export const COACH_AUTHOR = "coach";

export type BoardElement = {
  id: string;
  type: string;
  isDeleted?: boolean;
  text?: string;
  containerId?: string | null;
  customData?: { author?: string } | null;
  startBinding?: { elementId: string } | null;
  endBinding?: { elementId: string } | null;
  boundElements?: { id: string; type: string }[] | null;
};

export type BoardGraph = {
  nodes: { id: string; label: string }[];
  edges: { from: string; to: string; label: string }[];
  unreadable: number;
};

const NODE_TYPES = new Set(["rectangle", "ellipse", "diamond"]);
const EDGE_TYPES = new Set(["arrow", "line"]);

export function extractGraph(elements: readonly BoardElement[]): BoardGraph {
  const live = elements.filter(
    (e) => !e.isDeleted && e.customData?.author !== COACH_AUTHOR,
  );

  /* Excalidraw stores a box's label as a separate text element pointing back at
     its container, so labels are looked up rather than read off the box. */
  const labelOf = new Map<string, string>();
  for (const e of live) {
    if (e.type === "text" && e.containerId && e.text) {
      labelOf.set(e.containerId, e.text.trim());
    }
  }

  const nodes = live
    .filter((e) => NODE_TYPES.has(e.type))
    .map((e) => ({ id: e.id, label: labelOf.get(e.id) ?? "" }));
  const nodeIds = new Set(nodes.map((n) => n.id));

  const edges = live
    .filter((e) => EDGE_TYPES.has(e.type))
    /* An arrow bound to nothing is a stroke the user has not finished placing.
       Dropping it beats inventing an endpoint for it. */
    .filter(
      (e) =>
        e.startBinding?.elementId &&
        e.endBinding?.elementId &&
        nodeIds.has(e.startBinding.elementId) &&
        nodeIds.has(e.endBinding.elementId),
    )
    .map((e) => ({
      from: e.startBinding!.elementId,
      to: e.endBinding!.elementId,
      label: labelOf.get(e.id) ?? "",
    }));

  const unreadable = live.filter((e) => e.type === "freedraw").length;

  return { nodes, edges, unreadable };
}
