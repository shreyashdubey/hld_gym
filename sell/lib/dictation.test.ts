import { test } from "node:test";
import assert from "node:assert/strict";
import { appendTranscript } from "./dictation.ts";

test("first chunk becomes the whole answer", () => {
  assert.equal(appendTranscript("", "the app checks the cache"), "the app checks the cache");
});

test("later chunks are separated by exactly one space", () => {
  assert.equal(
    appendTranscript("the app checks the cache", "then it queries the database"),
    "the app checks the cache then it queries the database",
  );
});

test("trailing and leading whitespace never doubles up", () => {
  assert.equal(appendTranscript("a cache. ", "  Then the DB"), "a cache. Then the DB");
});

test("an empty chunk changes nothing", () => {
  assert.equal(appendTranscript("a cache", "   "), "a cache");
});

test("typed text the visitor already wrote is preserved verbatim", () => {
  // Dictation lands beside the keyboard, never replacing it.
  assert.equal(appendTranscript("I think it's cache-aside", "yes"), "I think it's cache-aside yes");
});
