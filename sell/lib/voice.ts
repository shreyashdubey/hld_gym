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

/** Connect, hand every server message to onMessage. Throws if unreachable —
    callers fall back to the keyboard rather than showing a broken control. */
export async function connectVoice(opts: {
  url?: string;
  mode?: "dictation" | "playground";
  onMessage: (message: unknown) => void;
}): Promise<VoiceSession> {
  const base = opts.url ?? VOICE_URL;
  const mode = opts.mode ?? "dictation";
  const client = new PipecatClient({
    transport: new SmallWebRTCTransport({ connectionUrl: `${base}/api/offer?mode=${mode}` }),
    enableMic: true,
    enableCam: false,
    callbacks: { onServerMessage: opts.onMessage },
  });
  await client.connect();
  return {
    send: (type, data) => client.sendClientMessage(type, data),
    disconnect: () => client.disconnect(),
  };
}
