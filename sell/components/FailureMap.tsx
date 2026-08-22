import { BOOK_URL, PRICE, RESERVE_URL } from "@/lib/links";
import type { FailureMoment } from "@/lib/failureMap";

/* The diagnostic round's output. Three variants, all honest:
   - moments === null: the round ended but the map was lost (grader failed
     twice, or the connection died first). One line, the free book, no CTA.
   - moments === []: not enough of a round to grade. Same posture.
   - otherwise: up to three moments, the disclosure, and the one buy CTA.
   The map is the sales argument, so the standing rule bites hardest here:
   nothing renders that the transcript does not support. */
export default function FailureMap({ moments }: { moments: FailureMoment[] | null }) {
  if (moments === null) {
    return (
      <div className="failureMap">
        <p>
          The round ended before your report could be delivered. The{" "}
          <a href={BOOK_URL}>free book</a> covers everything the round probes.
        </p>
      </div>
    );
  }
  if (moments.length === 0) {
    return (
      <div className="failureMap">
        <p>
          Not enough of a round to grade. Sit a longer one, or start with the{" "}
          <a href={BOOK_URL}>free chapter</a> it draws from.
        </p>
      </div>
    );
  }
  return (
    <div className="failureMap">
      <h2>Where you would have been cut</h2>
      <ol>
        {moments.map((m, i) => (
          <li key={i}>
            <blockquote>&ldquo;{m.quote}&rdquo;</blockquote>
            <p>{m.probe}</p>
            <p>
              <strong>{m.gap}</strong>
            </p>
            <a href={m.chapter}>the free chapter that covers it</a>
          </li>
        ))}
      </ol>
      <p className="hint">
        Graded by a model against the chapter, so it can be wrong. The quotes
        are from your transcript.
      </p>
      <a className="btn" href={RESERVE_URL} target="_blank" rel="noopener">
        close these gaps in 30 days · {PRICE}
      </a>
    </div>
  );
}
