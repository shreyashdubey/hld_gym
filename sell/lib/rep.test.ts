/* Run: npm test
   The rubric is the only real logic on the landing page, and a false negative
   makes the grader look broken to a stranger who is deciding whether to pay.
   These cases are the inflected forms people actually write. */

import { test } from "node:test";
import assert from "node:assert/strict";
import { RUBRIC, verdictFor } from "./rep.ts";

const score = (text: string) => RUBRIC.filter((k) => k.re.test(text)).length;
const hit = (label: string, text: string) =>
  RUBRIC.find((k) => k.label === label)!.re.test(text);

test("inflected verbs still count", () => {
  assert.ok(hit("GET from the cache first", "App checks the cache first"));
  assert.ok(hit("GET from the cache first", "the app gets it from redis"));
  assert.ok(hit("GET from the cache first", "we read from the cache"));
  assert.ok(hit("the app writes the cache itself", "the app writes the cache"));
  assert.ok(hit("the app writes the cache itself", "then it populates the key"));
  assert.ok(hit("the app queries the database", "it queried postgres"));
  assert.ok(hit("the miss comes back to the app", "on a miss it falls through"));
});

test("word boundaries keep the loose keys honest", () => {
  // "database" must not satisfy the "rows come back" key via \bdata\b
  assert.equal(hit("rows return to the app, not the cache", "database"), false);
  // "dataset" must not satisfy the write key via \bset\b
  assert.equal(hit("the app writes the cache itself", "a dataset"), false);
});

test("a full correct answer scores every key", () => {
  const good =
    "The app checks the cache first. On a miss the cache just says miss — " +
    "it does not fetch anything. The app then queries the database, gets the " +
    "rows back, and writes them into the cache itself with a TTL of 300s.";
  assert.equal(score(good), RUBRIC.length);
});

test("a partial answer loses exactly the parts it omitted", () => {
  const partial =
    "App checks the cache first. If it misses, the app goes to the database " +
    "and runs the query, gets rows back.";
  assert.equal(score(partial), 4); // no write-back, no TTL
  assert.equal(hit("the app writes the cache itself", partial), false);
  assert.equal(hit("a TTL on the write", partial), false);
});

test("an empty answer scores nothing and gets the blank verdict", () => {
  assert.equal(score(""), 0);
  assert.match(verdictFor(0, RUBRIC.length, true), /left it blank/);
  assert.match(verdictFor(6, RUBRIC.length, false), /Strong recall/);
});
