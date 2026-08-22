"use client";

/* Deliberately not `import { VOICE_URL } from "./voice.ts"` -- voice.ts
   pulls in @pipecat-ai/client-js and @pipecat-ai/small-webrtc-transport,
   both meant for a bundler (Next/Turbopack), not Node's own ESM loader.
   `npm test` runs this file's tests directly under Node
   (--experimental-strip-types), and importing voice.ts made even the pure
   parser tests below fail to load at all (confirmed: Node's loader choked
   resolving small-webrtc-transport's own `lodash/cloneDeep` import, which
   only a bundler tolerates). Same default, same env var, restated in one
   line rather than shared. */
const VOICE_URL = process.env.NEXT_PUBLIC_VOICE_URL ?? "http://localhost:7860";

/* Playground's own session token -- never Google's. Google issues an ID
   token that expires in about an hour; the voice service
   (playground/auth.py) verifies it once, at POST /api/login, and mints its
   own, longer-lived token (PLAYGROUND_SESSION_TTL_SECS, 7 days by default).
   Google's token is never stored here -- it is spent at /api/login and then
   forgotten.

   The token is opaque to this file except for its embedded `exp`, decoded
   by isTokenLikelyValid() below purely to decide, instantly and without a
   network round trip, whether to show "start the round" or the sign-in
   button. That decode never checks the signature (only the server holds
   PLAYGROUND_TOKEN_SECRET to do that) -- it is a UX shortcut, not the
   security boundary. A token that looks valid here and is actually
   expired, rotated, or forged still meets the server's own check on every
   /api/offer, the real gate. */

const STORAGE_KEY = "playground_session_token";

/* Baked in at build time (sell/.env.local -> NEXT_PUBLIC_PLAYGROUND_GOOGLE_CLIENT_ID)
   -- see playground/README.md. Public by design: it identifies this app to
   Google, the same way any OAuth client ID does; it authorizes nothing by
   itself. */
const GOOGLE_CLIENT_ID = process.env.NEXT_PUBLIC_PLAYGROUND_GOOGLE_CLIENT_ID ?? "";

export function getStoredToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(STORAGE_KEY);
}

export function storeToken(token: string): void {
  window.localStorage.setItem(STORAGE_KEY, token);
}

export function clearToken(): void {
  window.localStorage.removeItem(STORAGE_KEY);
}

function base64UrlDecode(s: string): string {
  const b64 = s.replace(/-/g, "+").replace(/_/g, "/");
  const padded = b64 + "=".repeat((4 - (b64.length % 4)) % 4);
  return atob(padded);
}

/** True only for a token whose embedded expiry is still in the future. See
    the module comment: this is a client-side shortcut, not verification. */
export function isTokenLikelyValid(token: string | null): boolean {
  if (!token) return false;
  const [payloadPart] = token.split(".");
  if (!payloadPart) return false;
  try {
    const payload = JSON.parse(base64UrlDecode(payloadPart)) as { exp?: number };
    return typeof payload.exp === "number" && payload.exp > Date.now() / 1000;
  } catch {
    return false;
  }
}

/** Exchanges a Google ID token for our own session token via POST
    /api/login, and stores it on success. Throws on any failure -- a
    rejected Google credential, a client ID mismatch, the service being
    down -- callers must not treat a failed exchange as a sign-in. */
export async function loginWithGoogleIdToken(idToken: string): Promise<string> {
  const res = await fetch(`${VOICE_URL}/api/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ id_token: idToken }),
  });
  if (!res.ok) throw new Error("sign-in failed");
  const data = (await res.json()) as { token: string; email: string };
  storeToken(data.token);
  return data.email;
}

type GoogleCredentialResponse = { credential: string };
type GoogleAccountsId = {
  initialize: (config: {
    client_id: string;
    callback: (response: GoogleCredentialResponse) => void;
  }) => void;
  renderButton: (
    parent: HTMLElement,
    options: { theme?: string; size?: string; text?: string },
  ) => void;
};

declare global {
  interface Window {
    google?: { accounts: { id: GoogleAccountsId } };
  }
}

let gsiScript: Promise<void> | null = null;

/* Google Identity Services touches `window` the moment it loads, so this
   must only ever run from an effect, never at module scope -- the same
   constraint that keeps @excalidraw/excalidraw's import out of module scope
   in Board.tsx, for the same reason: it would crash the static export's
   prerender ("window is not defined"). Cached in a module-level promise so
   calling this from more than one mount never injects the script twice. */
function loadGoogleIdentityScript(): Promise<void> {
  if (typeof window === "undefined") return Promise.reject(new Error("no window"));
  if (window.google?.accounts?.id) return Promise.resolve();
  if (gsiScript) return gsiScript;
  gsiScript = new Promise((resolve, reject) => {
    const script = document.createElement("script");
    script.src = "https://accounts.google.com/gsi/client";
    script.async = true;
    script.defer = true;
    script.onload = () => resolve();
    script.onerror = () => reject(new Error("failed to load Google Identity Services"));
    document.head.appendChild(script);
  });
  return gsiScript;
}

/** Renders Google's own "Sign in with Google" button into `container`.
    onIdToken fires with the raw Google ID token -- exchanging it for our
    own session token (loginWithGoogleIdToken, above) is the caller's job;
    this function only talks to Google, never to our own backend. Throws if
    the client ID is unconfigured or the script fails to load, so a caller
    can show that as plainly as any other sign-in failure. */
export async function renderGoogleSignInButton(
  container: HTMLElement,
  onIdToken: (idToken: string) => void,
): Promise<void> {
  if (!GOOGLE_CLIENT_ID) throw new Error("Google sign-in is not configured");
  await loadGoogleIdentityScript();
  const id = window.google?.accounts.id;
  if (!id) throw new Error("Google Identity Services failed to load");
  id.initialize({
    client_id: GOOGLE_CLIENT_ID,
    callback: (response) => onIdToken(response.credential),
  });
  id.renderButton(container, { theme: "outline", size: "large", text: "signin_with" });
}
