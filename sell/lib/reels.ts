/**
 * The reels, named once.
 *
 * Both the feed and the structured data describe the same four files, and a
 * search result that disagrees with the page is worse than no search result.
 * One list, two readers.
 */
export type Reel = {
  id: string;
  kernel: string;
  told: string;
  chapter: string;
  /* What the reel actually shows, for a crawler that cannot watch it. */
  summary: string;
};

export const REELS: Reel[] = [
  {
    id: "01",
    kernel: "A lock is a statement about the past.",
    told: "a hotel keycard",
    chapter: "consensus and fencing",
    summary:
      "Your hotel key still opens the door after checkout, because the front desk " +
      "and the lock are not connected. The same picture is then relabelled: a lease, " +
      "a lock service, and the database that has to check the token itself.",
  },
  {
    id: "02",
    kernel: "The read set and the write set must overlap.",
    told: "three flatmates and a moved dinner",
    chapter: "quorums",
    summary:
      "You tell two of three flatmates the dinner moved. Ask only one and you can " +
      "miss it; ask two and the sets must share a person. That overlap is R + W > N.",
  },
  {
    id: "03",
    kernel: "Queueing is refusing slowly.",
    told: "a coffee counter in a rush",
    chapter: "backpressure",
    summary:
      "Orders pile up, the wait climbs to nine minutes, and the cup being made " +
      "belongs to someone who left four minutes ago. Refusing at the door costs " +
      "almost nothing; queueing costs everything and still loses the customer.",
  },
  {
    id: "04",
    kernel: "The cache is a suggestion.",
    told: "sticky notes and a filing cabinet",
    chapter: "caching",
    summary:
      "Someone clears your desk. Three notes are still in the filing cabinet, so " +
      "that is slower and not wrong. The fourth was only ever on the desk, and that " +
      "one is gone.",
  },
];

/* 45 seconds, every cut. ISO 8601 because schema.org wants a duration, not a
   number. */
export const REEL_DURATION = "PT45S";
/* The date the four were rendered. Not today: uploadDate is a claim about the
   file, and re-stamping it on every build would make it a lie that also churns
   the committed dist/. */
export const REEL_DATE = "2026-08-16";
