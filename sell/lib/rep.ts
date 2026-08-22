/* One hand-built rep: the cache-aside read path.
   Source diagram + prose: HLD Gym chapter p1c06, "Caching: Remember, Don't Recompute".
   In the product these follow-ups are generated against the learner's actual
   answer; here they are written in advance, which the page says out loud. */

/* This file has a second copy: playground/rep.py. Python cannot import
   TypeScript, so the voice service's interviewer/coach prompts hand-port
   REP_TITLE, RUBRIC's labels, and PROBES from here. Change one, change
   both, or playground/tests/test_personas.py's TestNoDriftFromTheFrontend
   fails the next time the Python suite runs (there is no CI, so "the next
   time" means "whenever someone remembers to run it" -- see PROGRESS.md). */

/* The chapter id, not "rep 07": a numbered rep implies six others exist, and the
   heading above the panel says there is one. The id is checkable in the book. */
export const REP_TITLE = "p1c06 · cache-aside read path";

/** Narration shown as each step of the diagram draws itself. */
export const STEPS: string[] = [
  "The app asks the cache first. Always the cache first.",
  "Miss. Note what the cache did not do: it did not go and fetch it for you.",
  "Only now does the app pay for the expensive query.",
  "Rows come back to the app, not to the cache.",
  'The app writes the cache itself. That is what "aside" means.',
];

/** How long each narrated step holds before the next one draws. */
export const STEP_MS = 2200;
/** Lead-in before step 1, and the pause after the last step before the lock. */
export const LEAD_MS = 700;
export const LOCK_MS = 400;
/** What the button promises, derived from the same constants that run it. */
export const WATCH_S = Math.round((LEAD_MS + STEPS.length * STEP_MS + LOCK_MS) / 1000);

/** What a correct reconstruction has to contain. Matched against free text —
    deliberately generous, because the point is to find what was forgotten
    entirely, not to grade phrasing. */
type RubricKey = { label: string; re: RegExp };

/* Stems, not exact words. Real answers say "checks", "writes", "queried" —
   matching on \bcheck\b marks a correct answer wrong, which is far worse here
   than being slightly too generous. Boundaries still keep "database" out of
   the \bdata\b key and "dataset" out of the \bset\b key. */
export const RUBRIC: RubricKey[] = [
  {
    label: "GET from the cache first",
    re: /\b(get\w*|read\w*|check\w*|ask\w*|look\w*|hit)\b/i,
  },
  { label: "the miss comes back to the app", re: /\bmiss\w*/i },
  {
    label: "the app queries the database",
    re: /\b(db|database|sql|quer\w*|source of truth|origin|backend)\b/i,
  },
  {
    label: "rows return to the app, not the cache",
    re: /\b(rows?|results?|records?|data|response)\b/i,
  },
  {
    label: "the app writes the cache itself",
    re: /\b(set|sets|writ\w*|fill\w*|populat\w*|puts?|stor\w*|sav\w*)\b/i,
  },
  { label: "a TTL on the write", re: /\b(ttl|expir\w*|time.to.live|300|evict\w*)\b/i },
];

type Probe = { q: string; a: string };

/** The three follow-ups. Each targets something people routinely leave out. */
export const PROBES: Probe[] = [
  {
    q: "Step 2 was a miss. Why didn’t the cache go and fetch it for you?",
    a: "Because cache-aside puts the app in charge, not the cache. The cache is a dumb key-value box that answers hit or miss and nothing else. That is exactly why it is resilient: when the cache dies, reads get slower but they still work, because the fallback path is already the normal path. A read-through cache would have fetched it for you, and taken the database down with it when it failed.",
  },
  {
    q: "Between step 2 and step 5, another server updates that product and deletes the key. What is in your cache after step 5?",
    a: "Stale data, and it sits there wrong until the TTL expires. Your step 5 writes rows that were true at step 2. The delete happened in between, so it deleted nothing, and then you refilled the key with the old value. This is the race at the heart of cache invalidation, and it is why the TTL is not optional decoration: it is the only thing that eventually saves you.",
  },
  {
    q: "Your hit rate is 99%. The cache dies. What happens to the database?",
    a: "It takes 100× its normal read load, instantly, and almost certainly falls over. The better your hit rate, the more catastrophic losing the cache becomes. Success is what created the fragility. A 99% hit rate means the database was only ever sized for 1% of real traffic. This is why you load-test with the cache cold, and why “the cache is just an optimisation” stops being true the moment you depend on it.",
  },
];

export function verdictFor(score: number, blank: boolean): string {
  if (blank)
    return "You left it blank. That is the most honest possible result, and it is exactly why the lock exists.";
  /* No "this is the normal score": nothing has been measured, and a claimed
     norm is the one kind of social proof the page could invent by accident. */
  if (score <= 2)
    return "Two or fewer of the six. That is what reading alone gets you, and it is the whole gap between having read something and knowing it.";
  if (score <= 4)
    return "Most of the shape, missing the parts interviewers actually probe. The follow-ups below are where that shows.";
  return "Strong recall. Now the follow-ups, which is where this usually comes apart.";
}
