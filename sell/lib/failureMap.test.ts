import { test } from "node:test";
import assert from "node:assert/strict";
import { parseFailureMap } from "./failureMap.ts";

const MOMENT = {
  quote: "we'll just shard it",
  probe: "the shard key",
  gap: "no key named",
  chapter: "/book/#ch/p1c06",
};

test("a well-formed map parses", () => {
  const got = parseFailureMap({ type: "failure_map", moments: [MOMENT] });
  assert.deepEqual(got, { moments: [MOMENT] });
});

test("null moments survive as the lost-map signal", () => {
  assert.deepEqual(parseFailureMap({ type: "failure_map", moments: null }), {
    moments: null,
  });
});

test("other messages are not failure maps", () => {
  assert.equal(parseFailureMap({ type: "transcript", text: "hi" }), null);
  assert.equal(parseFailureMap("junk"), null);
  assert.equal(parseFailureMap(undefined), null);
});

test("malformed moments are dropped, not rendered", () => {
  const got = parseFailureMap({
    type: "failure_map",
    moments: [MOMENT, { quote: "" }, 42, { ...MOMENT, chapter: "https://evil.example" }],
  });
  assert.deepEqual(got, { moments: [MOMENT] });
});

test("at most three moments", () => {
  const got = parseFailureMap({ type: "failure_map", moments: [MOMENT, MOMENT, MOMENT, MOMENT] });
  assert.equal(got?.moments?.length, 3);
});

test("a moments field of the wrong shape reads as lost, not as a crash", () => {
  assert.deepEqual(parseFailureMap({ type: "failure_map", moments: "x" }), {
    moments: null,
  });
});
