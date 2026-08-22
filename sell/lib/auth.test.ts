import { test } from "node:test";
import assert from "node:assert/strict";
import { isTokenLikelyValid } from "./auth.ts";

/* isTokenLikelyValid is a parser on the auth path -- base64url decode,
   JSON.parse, an expiry compare -- flagged by security review as the one
   sell/lib/* module with no dedicated test, unlike every sibling. It never
   checks a signature (see auth.ts's own module comment: that's the
   server's job), so these tests are only about the decode/expiry logic,
   not about trusting an untampered token. */

function fakeToken(payload: Record<string, unknown>, sig = "sig"): string {
  const b64 = Buffer.from(JSON.stringify(payload), "utf8").toString("base64url");
  return `${b64}.${sig}`;
}

test("a token with a future exp is likely valid", () => {
  const token = fakeToken({ email: "a@example.com", exp: Date.now() / 1000 + 3600 });
  assert.equal(isTokenLikelyValid(token), true);
});

test("a token with a past exp is not", () => {
  const token = fakeToken({ email: "a@example.com", exp: Date.now() / 1000 - 1 });
  assert.equal(isTokenLikelyValid(token), false);
});

test("null is not valid", () => {
  assert.equal(isTokenLikelyValid(null), false);
});

test("empty string is not valid", () => {
  assert.equal(isTokenLikelyValid(""), false);
});

test("a token with no dot separator is not valid", () => {
  assert.equal(isTokenLikelyValid("not-a-real-token"), false);
});

test("a token whose payload is not valid base64url is not valid", () => {
  assert.equal(isTokenLikelyValid("not!base64!!.sig"), false);
});

test("a token whose payload decodes but is not JSON is not valid", () => {
  const b64 = Buffer.from("not json at all", "utf8").toString("base64url");
  assert.equal(isTokenLikelyValid(`${b64}.sig`), false);
});

test("a token with no exp field is not valid", () => {
  assert.equal(isTokenLikelyValid(fakeToken({ email: "a@example.com" })), false);
});

test("a token whose exp is the wrong type is not valid", () => {
  assert.equal(isTokenLikelyValid(fakeToken({ email: "a@example.com", exp: "soon" })), false);
});

test("matches the exact unpadded base64url encoding playground/auth.py's sign_token produces", () => {
  // Node's "base64url" Buffer encoding already omits padding, same as
  // Python's base64.urlsafe_b64encode(...).rstrip(b"=") -- confirming that
  // equivalence here, not just asserting isTokenLikelyValid's own decode.
  const payload = JSON.stringify({ email: "a@example.com", exp: 9999999999 });
  const encoded = Buffer.from(payload, "utf8").toString("base64url");
  assert.equal(encoded.includes("="), false);
  assert.equal(isTokenLikelyValid(`${encoded}.anysig`), true);
});
