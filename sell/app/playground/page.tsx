"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import Board from "@/components/Board";
import { connectVoice, type VoiceSession } from "@/lib/voice";
import {
  clearToken,
  getStoredToken,
  isTokenLikelyValid,
  loginWithGoogleIdToken,
  renderGoogleSignInButton,
} from "@/lib/auth";
import { extractGraph, type BoardElement, type BoardGraph } from "@/lib/board";
import { layoutTopology, type Topology } from "@/lib/layout";
import type { ExcalidrawImperativeAPI } from "@excalidraw/excalidraw/types";

/* idle/connecting/live plus three distinct terminal states, not one shared
   "unavailable" — a completed cap, a fatal service error, and a denied mic
   are three different things and this repo's first standing rule is never
   to claim the product does something it does not. Collapsing them (the
   bug this replaced) meant a *working* round that ran its full course and
   handed over to the coach reported the same "voice service unreachable"
   as a service that was never reachable at all.
     "denied"      — connectVoice() threw because the mic permission (or
                      device) never came up granted. The board still works.
     "unavailable" — connect failed some other way, or a live session ended
                      via RTVI's onError (a relayed service error) rather
                      than a clean close.
     "ended"       — a live session's connection closed on its own with no
                      error ahead of it — today, only the session cap's own
                      cut, which the interviewer has already handed the
                      coach's walkthrough ahead of. Not a failure. */
type PlaygroundState = "idle" | "connecting" | "live" | "ended" | "unavailable" | "denied";

export default function PlaygroundPage() {
  const [state, setState] = useState<PlaygroundState>("idle");
  const [said, setSaid] = useState<string[]>([]);
  const [backfill, setBackfill] = useState<BoardGraph | null>(null);
  const session = useRef<VoiceSession | null>(null);
  const excalidrawAPI = useRef<ExcalidrawImperativeAPI | null>(null);

  /* Every session bills OpenAI credit by the minute, so /api/offer gates
     mode=playground on our own session token -- see
     playground/server.py and docs/superpowers/specs/2026-08-21-playground-design.md.
     null until the effect below settles it, on purpose: this page is
     server-rendered once during the static export's prerender, where
     `window` (and so localStorage) doesn't exist, so the server's first
     render must show neither the sign-in button nor "start the round" --
     showing either eagerly (tried first as a lazy useState initializer,
     `typeof window === "undefined" ? null : isTokenLikelyValid(...)`)
     produced a real hydration mismatch: the server's tree (always null)
     disagreed with the client's very first render (the real answer,
     already different). isTokenLikelyValid is a client-side shortcut, not
     the real gate -- see lib/auth.ts -- the server checks the actual
     signature on every /api/offer regardless, so a stale token that slips
     past this check simply fails there instead. */
  const [signedIn, setSignedIn] = useState<boolean | null>(null);
  const [authError, setAuthError] = useState<string | null>(null);
  const googleButton = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    // Reading localStorage is a one-time sync with an external system, not
    // a value computed from render -- the case react-hooks' own docs carve
    // out for setState-in-effect. The lint rule's heuristic can't tell the
    // two apart.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setSignedIn(isTokenLikelyValid(getStoredToken()));
  }, []);

  // Renders Google's own button once signed-out is established -- not
  // eagerly at module scope; renderGoogleSignInButton touches `window`, the
  // same constraint Board.tsx's dynamic Excalidraw import exists for.
  useEffect(() => {
    if (signedIn !== false || !googleButton.current) return;
    renderGoogleSignInButton(googleButton.current, (idToken) => {
      loginWithGoogleIdToken(idToken)
        .then(() => {
          setAuthError(null);
          setSignedIn(true);
          /* Back to square one, not to whatever the last attempt left
             behind. A connect failure sets "unavailable" and signs the
             visitor out (see start()'s catch); without this reset the
             button that reappears after they sign back in reads "voice
             service unreachable", and the hint under it claims the service
             isn't reachable — about a service nothing has contacted since.
             Same rule the catch's own comment cites, pointing the other
             way: never claim the product does something it does not. */
          setState("idle");
        })
        .catch(() => setAuthError("Sign-in failed — try again."));
    }).catch(() => setAuthError("Google sign-in isn't available right now."));
  }, [signedIn]);

  const onGraphChange = useCallback((graph: BoardGraph) => {
    session.current?.send("board", { graph });
  }, []);

  /* The coach draws in its own lane, beside the candidate's work, never on top
     of it: offset past the right edge of everything already on the board.

     @excalidraw/excalidraw has a single entry point that touches `window` at
     module scope (see the Board.tsx comment on the dynamic Excalidraw import),
     so convertToExcalidrawElements is loaded here, at call time, rather than
     hoisted to a module-scope import — hoisting it crashes the static export's
     prerender of this page with "window is not defined". */
  const onDraw = useCallback(async (topology: Topology) => {
    const api = excalidrawAPI.current;
    if (!api) return;
    const { convertToExcalidrawElements } = await import("@excalidraw/excalidraw");
    const existing = api.getSceneElements();
    const rightEdge = existing.reduce((max, el) => Math.max(max, el.x + el.width), 0);
    const skeleton = layoutTopology(topology, rightEdge + 160);
    api.updateScene({
      elements: [...existing, ...convertToExcalidrawElements(skeleton as never)],
    });
  }, []);

  /* Voice bills OpenAI credit by the minute, so a session has to end when
     the visitor is done with it, not when the server-side cap notices twelve
     minutes later. There was no stop control at all: the whole button block
     is hidden while state === "live", and nothing tore the session down on
     unmount either, so a visitor who started a round and then navigated away
     client-side left it running and spending. Rep.tsx has had exactly this
     teardown since dictation shipped; this page never got one.

     lib/voice.ts guarantees onDisconnect never fires for a disconnect the
     caller asked for itself, so this sets the terminal state directly --
     "ended", the same state the cap's own clean cut produces, because a
     round the visitor chose to end is not a failure either. */
  const stop = useCallback(() => {
    const opened = session.current;
    session.current = null;
    setState("ended");
    void opened?.disconnect().catch(() => {});
  }, []);

  useEffect(
    () => () => {
      void session.current?.disconnect().catch(() => {});
      session.current = null;
    },
    [],
  );

  const start = useCallback(async () => {
    setState("connecting");
    try {
      const opened = await connectVoice({
        mode: "playground",
        token: getStoredToken() ?? undefined,
        onMessage: (m) => {
          const msg = m as { type?: string; text?: string; topology?: Topology };
          if (msg?.type === "transcript" && msg.text) setSaid((s) => [...s, msg.text!]);
          /* topology is a model tool-call payload, not user input — it arrives
             malformed eventually (missing nodes/edges, wrong types). Catch and
             drop rather than throwing into an unhandled rejection: nothing in
             onDraw mutates the scene before layoutTopology finishes, so a
             failed draw leaves the learner's board untouched. */
          if (msg?.type === "draw" && msg.topology) onDraw(msg.topology).catch(() => {});
        },
        onDisconnect: (reason) => {
          /* Fires later, only if this exact session ends on its own. reason
             distinguishes a fatal service error ("error", RTVI's onError
             fired first — see lib/voice.ts) from a clean server-initiated
             close with no error ahead of it ("ended" -- today, only the
             session cap's own cut, and by the time that fires the
             interviewer has already handed over to the coach). Only the
             former is reported as "unreachable"; a round that ran its
             course and ended on schedule is not a failure and must not
             read as one. */
          if (session.current !== opened) return;
          session.current = null;
          setState(reason === "error" ? "unavailable" : "ended");
        },
      });
      session.current = opened;
      setState("live");
      /* The coach otherwise opens deaf to whatever was drawn before "start" was
         clicked — the natural order for a visitor who draws first, then talks.
         Without this, the gate has already recorded that diagram's signature
         from the drawing itself, so it would never resend it on its own. */
      const elements = excalidrawAPI.current?.getSceneElements() ?? [];
      const graph = extractGraph(elements as readonly BoardElement[]);
      session.current.send("board", { graph });
      setBackfill(graph);
    } catch (err) {
      /* connectVoice() throws a plain Error("microphone unavailable") for
         exactly one reason: mediaState.mic never settled to "granted" --
         permission denied, or no device at all. Any other throw (the
         service unreachable, a bad SDP, connect() itself failing) is the
         generic case. Conflating the two is the bug this replaced: the
         spec requires a denied mic to say so out loud, not report a
         running board as a dead service. */
      const denied = err instanceof Error && err.message === "microphone unavailable";
      if (!denied) {
        /* A token that looked client-side-valid (isTokenLikelyValid, on
           mount) can still be rejected server-side -- a rotated secret,
           clock skew, a forged value. This catch can't tell that apart from
           the service just being down: @pipecat-ai/small-webrtc-transport
           swallows the actual HTTP status internally during its own
           reconnection retries before client.connect() ever rejects (traced
           in the installed package's negotiate()/attemptReconnection() --
           the specific 401 is gone by the time this catch runs, only an
           unhelpful `undefined` rejection reaches here). Clearing the token
           and re-requiring sign-in on *any* non-mic connect failure is the
           honest recovery: a genuinely stale token retried forever with no
           way back to a working state is worse than one extra sign-in click
           on the rarer case where this was actually just the service being
           briefly down.

           setSignedIn(false) below unmounts the entire signedIn===true
           branch this render -- the "voice service unreachable" button
           label and hint live inside it, so without this message the *far
           more common* case (the service is briefly down, the token was
           fine) went completely silent: a valid-token visitor got logged
           out with no explanation at all, in this repo whose first rule is
           never to claim the product does something it does not -- silence
           about a failure is exactly that, by omission. Found by browser
           verification with the service down and a valid token, not by
           reading the diff. */
        clearToken();
        setSignedIn(false);
        setAuthError(
          "The voice service isn't reachable right now — the board below still works. Sign in and try again once it's back.",
        );
      }
      setState(denied ? "denied" : "unavailable");
    }
  }, [onDraw]);

  return (
    <main className="playground">
      <h1>Playground</h1>
      {signedIn === false && (
        <>
          {/* Every session bills OpenAI credit per minute of audio on an
              endpoint anyone could otherwise reach -- see
              sell/PROGRESS.md's entry for why this exists. No account is
              created beyond the email Google verifies; see lib/auth.ts. */}
          <p className="hint">
            Playground is a live voice session, so it asks for a Google
            sign-in first — the board below still works without one.
          </p>
          <div ref={googleButton} />
          {authError && <p className="hint">{authError}</p>}
        </>
      )}
      {signedIn === true && state === "live" && (
        <>
          <button type="button" className="btn" onClick={stop}>
            end the round
          </button>
          <p className="hint">
            Ends the session now rather than waiting for the cap. The board
            below keeps everything on it either way.
          </p>
        </>
      )}
      {signedIn === true && state !== "live" && (
        <>
          <button type="button" className="btn" onClick={start} disabled={state === "connecting"}>
            {state === "denied"
              ? "microphone permission denied"
              : state === "unavailable"
                ? "voice service unreachable"
                : state === "ended"
                  ? "round ended — start another"
                  : "start the round"}
          </button>
          {/* Announced before the session starts, not when the cap bites --
              see playground/server.py's _enforce_cap and the design's "session
              cap, announced up front". No fixed number here: the cap is
              env-configurable (PLAYGROUND_SESSION_CAP_SECS) and this is a
              static export with no way to read that at build time, so the
              honest move is a claim that holds regardless of the configured
              value, not a number that can go stale the moment the env var
              changes -- see sell/PROGRESS.md. */}
          <p className="hint">
            {state === "denied"
              ? "The microphone permission was denied (or no mic is available). Allow it in your browser's site settings and try again — the board below still works either way, nothing will listen or talk until it's granted."
              : state === "unavailable"
                ? "The voice service isn't reachable right now. The board below still works on its own — try the round again once it's back."
                : state === "ended"
                  ? "That round ended — no error, just the connection closing on its own. Start another whenever you're ready."
                  : "Sessions run for a capped length. The interviewer hands over to the coach before time is up, so you always get the walkthrough."}
          </p>
        </>
      )}
      <Board
        onGraphChange={onGraphChange}
        apiRef={(api) => {
          excalidrawAPI.current = api;
        }}
        syncGraph={backfill}
      />
      <ol className="said">{said.map((s, i) => <li key={i}>{s}</li>)}</ol>
    </main>
  );
}
