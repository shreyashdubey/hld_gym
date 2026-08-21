import { test } from "node:test";
import assert from "node:assert/strict";
import { layoutTopology } from "./layout.ts";
import { COACH_AUTHOR } from "./board.ts";

const TOPOLOGY = {
  nodes: [
    { id: "app", label: "App" },
    { id: "cache", label: "Cache" },
    { id: "db", label: "DB" },
  ],
  edges: [
    { from: "app", to: "cache", label: "GET" },
    { from: "app", to: "db", label: "query" },
  ],
};

test("every node becomes one skeleton element", () => {
  const els = layoutTopology(TOPOLOGY, 0);
  assert.equal(els.filter((e) => e.type === "rectangle").length, 3);
});

test("every edge becomes one arrow", () => {
  const els = layoutTopology(TOPOLOGY, 0);
  assert.equal(els.filter((e) => e.type === "arrow").length, 2);
});

test("every element is stamped as the coach's", () => {
  // The extractor excludes these. Miss the stamp and the coach reads its own
  // diagram back as the candidate's work.
  const els = layoutTopology(TOPOLOGY, 0);
  assert.ok(els.every((e) => e.customData?.author === COACH_AUTHOR));
});

test("nothing lands left of the offset", () => {
  // The coach draws in its own lane, beside the candidate's work, never on it.
  const els = layoutTopology(TOPOLOGY, 1200);
  assert.ok(els.filter((e) => e.type === "rectangle").every((e) => e.x >= 1200));
});

test("no two boxes overlap", () => {
  const boxes = layoutTopology(TOPOLOGY, 0).filter((e) => e.type === "rectangle");
  for (let i = 0; i < boxes.length; i++) {
    for (let j = i + 1; j < boxes.length; j++) {
      const a = boxes[i], b = boxes[j];
      const apart =
        a.x + a.width! <= b.x || b.x + b.width! <= a.x ||
        a.y + a.height! <= b.y || b.y + b.height! <= a.y;
      assert.ok(apart, `${a.label?.text} overlaps ${b.label?.text}`);
    }
  }
});

test("arrows bind to node ids, not to coordinates", () => {
  const arrows = layoutTopology(TOPOLOGY, 0).filter((e) => e.type === "arrow");
  assert.deepEqual(arrows.map((a) => [a.start?.id, a.end?.id]), [["app", "cache"], ["app", "db"]]);
});

test("an edge referencing a missing node is dropped, not drawn into the void", () => {
  const els = layoutTopology(
    { nodes: [{ id: "a", label: "A" }], edges: [{ from: "a", to: "ghost" }] },
    0,
  );
  assert.equal(els.filter((e) => e.type === "arrow").length, 0);
});

test("an empty topology draws nothing", () => {
  assert.deepEqual(layoutTopology({ nodes: [], edges: [] }, 0), []);
});
