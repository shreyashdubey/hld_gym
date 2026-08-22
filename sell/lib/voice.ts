"use client";

import { PipecatClient } from "@pipecat-ai/client-js";
import { SmallWebRTCTransport } from "@pipecat-ai/small-webrtc-transport";

/* Not NEXT_PUBLIC_-prefixed by accident: this is a URL, and only a URL. The
   OpenAI key lives on the service and is never shipped to a browser. */
export const VOICE_URL = process.env.NEXT_PUBLIC_VOICE_URL ?? "http://localhost:7860";

export type VoiceSession = {
  send: (type: string, data?: unknown) => void;
  disconnect: () => Promise<void>;
};

/** Connect, hand every server message to onMessage. Throws if unreachable, or
    if the mic never actually came up — either way callers fall back to the
    keyboard rather than showing a control that claims to be listening while
    hearing nothing. onDisconnect fires at most once, later, if a session that
    connected successfully then ends on its own: a server-initiated teardown
    (the session cap, a clean "closed") or a fatal service error relayed over
    RTVI's own error channel. Never fires for a disconnect the caller asked
    for itself via session.disconnect() — callers react to it exactly as they
    react to connectVoice() throwing, so there is one failure path, not two.

    onDisconnect's reason distinguishes the two: "error" only when RTVI's own
    onError fired first (a relayed ErrorFrame — a bad key, a dead model),
    "ended" for every other server-initiated teardown, which today means the
    session cap's own clean cut. A cap-ended session is not a failure — the
    interviewer already handed over to the coach before it cut — and a caller
    that reported it the same way it reports a real error would be telling a
    visitor a working feature was down. */
export async function connectVoice(opts: {
  url?: string;
  mode?: "dictation" | "playground" | "diagnostic";
  /* Our own session token (see lib/auth.ts), sent as
     "Authorization: Bearer <token>" -- never in the URL: a token in a query
     string leaks into every server log line it passes through. Only
     mode=playground checks it; dictation ignores it even if one is passed,
     see playground/server.py's mode gate -- it stays completely open. */
  token?: string;
  onMessage: (message: unknown) => void;
  onDisconnect: (reason: "ended" | "error") => void;
}): Promise<VoiceSession> {
  const base = opts.url ?? VOICE_URL;
  const mode = opts.mode ?? "dictation";
  // False until a VoiceSession has actually been handed back, and false
  // again from the moment the caller disconnects it itself — so a stale
  // client's own teardown (which fires onDisconnected too) never re-reports
  // a session the caller has already moved on from.
  let live = false;
  // Set by onError, read by onDisconnected -- onError always closes the
  // connection itself (see below), and onDisconnected is what actually
  // notifies the caller, so this is the one place that knows which of the
  // two happened.
  let errored = false;
  const client = new PipecatClient({
    // webrtcRequestParams, not the deprecated connectionUrl -- it's the
    // only shape that carries a header (APIRequest.headers is a Headers
    // instance, per @pipecat-ai/client-js), which is what an Authorization
    // header needs.
    transport: new SmallWebRTCTransport({
      webrtcRequestParams: {
        endpoint: `${base}/api/offer?mode=${mode}`,
        ...(opts.token ? { headers: new Headers({ Authorization: `Bearer ${opts.token}` }) } : {}),
      },
    }),
    enableMic: true,
    enableCam: false,
    callbacks: {
      onServerMessage: opts.onMessage,
      onDisconnected: () => {
        if (!live) return;
        live = false;
        opts.onDisconnect(errored ? "error" : "ended");
      },
      onError: () => {
        // A service error relayed to the client is treated as fatal to this
        // session, full stop — no error taxonomy, because the OpenAI call
        // that produced it (a bad key, a dead model) will only fail the same
        // way again on the next turn, and this app has no retry UX. Close
        // the connection ourselves rather than leave a zombie session
        // burning the rest of the cap on a service already known to be
        // broken; onDisconnected above does the actual notifying once that
        // completes.
        errored = true;
        void client.disconnect().catch(() => {});
      },
    },
  });
  await client.connect();
  // @pipecat-ai/client-js swallows a getUserMedia rejection internally
  // rather than failing connect() — the transport connects fine with no
  // live mic track at all. mediaState.mic is the SDK's own purpose-built
  // signal for this (connect() awaits initDevices() to completion first, so
  // it has already settled to "granted" or an error by the time connect()
  // resolves) — checked here rather than assumed from a successful connect.
  if (client.mediaState.mic.state !== "granted") {
    await client.disconnect().catch(() => {});
    throw new Error("microphone unavailable");
  }
  live = true;
  return {
    send: (type, data) => client.sendClientMessage(type, data),
    disconnect: () => {
      live = false;
      return client.disconnect();
    },
  };
}
