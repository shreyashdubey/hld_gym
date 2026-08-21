/* Spoken answers land in the same textarea as typed ones, so the regex rubric
   in rep.ts grades both through exactly one path. */

/** Append one finalized transcript chunk to what is already in the box. */
export function appendTranscript(prev: string, chunk: string): string {
  const next = chunk.trim();
  if (!next) return prev;
  const base = prev.trimEnd();
  return base ? `${base} ${next}` : next;
}
