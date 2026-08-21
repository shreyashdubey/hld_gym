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

test("an empty board is an empty graph, not a crash", () => {
  assert.deepEqual(extractGraph([]), { nodes: [], edges: [], unreadable: 0 });
});

test("the marker constant is what the layout module will stamp", () => {
  assert.equal(COACH_AUTHOR, "coach");
});
