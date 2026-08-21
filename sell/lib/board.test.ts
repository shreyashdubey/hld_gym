import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { extractGraph, COACH_AUTHOR, type BoardElement } from "./board.ts";

const scene = JSON.parse(
  readFileSync(new URL("./fixtures/board-sample.json", import.meta.url), "utf8"),
) as BoardElement[];

test("labelled boxes become nodes", () => {
  const g = extractGraph(scene);
  assert.deepEqual(g.nodes.map((n) => n.label).sort(), ["App", "Cache"]);
});

test("a bound arrow becomes an edge between those nodes", () => {
  const g = extractGraph(scene);
  const app = g.nodes.find((n) => n.label === "App")!;
  const cache = g.nodes.find((n) => n.label === "Cache")!;
  assert.deepEqual(g.edges, [{ from: app.id, to: cache.id, label: "GET" }]);
});

test("freehand strokes are counted, not guessed at", () => {
  assert.equal(extractGraph(scene).unreadable, 1);
});

test("coach-drawn elements are excluded", () => {
  // Otherwise the coach reads its own diagram back and congratulates the user.
  const g = extractGraph(scene);
  assert.equal(g.nodes.some((n) => n.id === "coach-box-1"), false);
});

test("deleted elements are excluded", () => {
  const withDeleted = [...scene, { id: "gone", type: "rectangle", isDeleted: true } as BoardElement];
  assert.deepEqual(extractGraph(withDeleted).nodes, extractGraph(scene).nodes);
});

test("an unbound arrow is dropped rather than invented", () => {
  const loose = [...scene, { id: "loose", type: "arrow" } as BoardElement];
  assert.equal(extractGraph(loose).edges.length, 1);
});

test("a half-placed arrow (dragged off one node, never dropped on a target) is dropped", () => {
  // startBinding set, endBinding absent — the scenario the drop-don't-invent
  // rule actually exists for, not just a fully unbound stroke.
  const app = extractGraph(scene).nodes.find((n) => n.label === "App")!;
  const halfStart = [
    ...scene,
    { id: "half-start", type: "arrow", startBinding: { elementId: app.id } } as BoardElement,
  ];
  assert.equal(extractGraph(halfStart).edges.length, 1);
});

test("the mirror case — endBinding set, startBinding absent — is also dropped", () => {
  const cache = extractGraph(scene).nodes.find((n) => n.label === "Cache")!;
  const halfEnd = [
    ...scene,
    { id: "half-end", type: "arrow", endBinding: { elementId: cache.id } } as BoardElement,
  ];
  assert.equal(extractGraph(halfEnd).edges.length, 1);
});

test("an empty board is an empty graph, not a crash", () => {
  assert.deepEqual(extractGraph([]), { nodes: [], edges: [], unreadable: 0 });
});

test("the marker constant is what the layout module will stamp", () => {
  assert.equal(COACH_AUTHOR, "coach");
});

import { graphSignature } from "./board.ts";

test("the same graph signs the same", () => {
  const g = { nodes: [{ id: "a", label: "App" }], edges: [], unreadable: 0 };
  assert.equal(graphSignature(g), graphSignature(structuredClone(g)));
});

test("dragging a box produces an identical graph", () => {
  // Not a signature test — extractGraph is what makes this hold. BoardElement
  // carries no position field, so a moved element differs from the original
  // only in a property extractGraph never reads, and the two graphs come out
  // byte-identical, in the same order. This test cannot fail against any
  // graphSignature; it can only fail once BoardGraph grows a coordinate and
  // extractGraph starts emitting it — at which point it forces a deliberate
  // choice about whether dragging should wake the coach.
  const a = extractGraph(scene);
  const moved = extractGraph(scene.map((e) => ({ ...e, x: 999 } as BoardElement)));
  assert.equal(graphSignature(a), graphSignature(moved));
});

test("adding an edge changes the signature", () => {
  const a = { nodes: [{ id: "a", label: "App" }], edges: [], unreadable: 0 };
  const b = { ...a, edges: [{ from: "a", to: "a", label: "" }] };
  assert.notEqual(graphSignature(a), graphSignature(b));
});

test("renaming a node changes the signature", () => {
  const a = { nodes: [{ id: "a", label: "App" }], edges: [], unreadable: 0 };
  const b = { nodes: [{ id: "a", label: "Cache" }], edges: [], unreadable: 0 };
  assert.notEqual(graphSignature(a), graphSignature(b));
});

test("element order does not change the signature", () => {
  const a = { nodes: [{ id: "a", label: "A" }, { id: "b", label: "B" }], edges: [], unreadable: 0 };
  const b = { nodes: [{ id: "b", label: "B" }, { id: "a", label: "A" }], edges: [], unreadable: 0 };
  assert.equal(graphSignature(a), graphSignature(b));
});

test("edge order does not change the signature", () => {
  // Needs two edges: with only one, dropping the edge .sort() is unobservable.
  const a = {
    nodes: [],
    edges: [{ from: "a", to: "b", label: "x" }, { from: "b", to: "c", label: "y" }],
    unreadable: 0,
  };
  const b = {
    nodes: [],
    edges: [{ from: "b", to: "c", label: "y" }, { from: "a", to: "b", label: "x" }],
    unreadable: 0,
  };
  assert.equal(graphSignature(a), graphSignature(b));
});

test("relabelling an edge changes the signature", () => {
  // Renaming an arrow from GET to write is a real change to the diagram.
  const a = { nodes: [], edges: [{ from: "a", to: "b", label: "GET" }], unreadable: 0 };
  const b = { nodes: [], edges: [{ from: "a", to: "b", label: "write" }], unreadable: 0 };
  assert.notEqual(graphSignature(a), graphSignature(b));
});

test("a new scribble changes the signature", () => {
  // A freehand mark the extractor can't read is still a change worth a "what's that?".
  const a = { nodes: [], edges: [], unreadable: 0 };
  const b = { nodes: [], edges: [], unreadable: 1 };
  assert.notEqual(graphSignature(a), graphSignature(b));
});
