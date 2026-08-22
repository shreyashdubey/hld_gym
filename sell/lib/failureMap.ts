/* The failure map is the diagnostic round's whole output, and it renders on
   a page that asks for money -- so nothing from the wire is trusted. The
   server already substring-checks quotes against the transcript; this end
   checks shapes: every field a non-empty string, at most three moments, and
   chapter links only ever into the free book. */

export type FailureMoment = {
  quote: string;
  probe: string;
  gap: string;
  chapter: string;
};

const isMoment = (m: unknown): m is FailureMoment => {
  if (typeof m !== "object" || m === null) return false;
  const c = m as Record<string, unknown>;
  return (
    [c.quote, c.probe, c.gap, c.chapter].every(
      (v) => typeof v === "string" && v.trim() !== "",
    ) && (c.chapter as string).startsWith("/book/")
  );
};

/* null: not a failure-map message. { moments: null }: the round ended but
   the grader failed -- the lost-map line. { moments: [...] }: the map. */
export function parseFailureMap(
  message: unknown,
): { moments: FailureMoment[] | null } | null {
  if (typeof message !== "object" || message === null) return null;
  const m = message as { type?: unknown; moments?: unknown };
  if (m.type !== "failure_map") return null;
  if (!Array.isArray(m.moments)) return { moments: null };
  return { moments: m.moments.filter(isMoment).slice(0, 3) };
}
