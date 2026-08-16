"use client";

import { useEffect, useRef, useState, useSyncExternalStore } from "react";

/**
 * The reel feed. Swipe one, get the next, the way a phone feed works, because
 * that is the habit this is borrowing.
 *
 * The video is the object. It arrives already framed, already captioned, with
 * its own title card, so it gets one hairline and nothing else around it. An
 * earlier version put it inside a bordered slide inside a bordered rail, which
 * boxed a box twice over and squeezed the video down to 300px, where the
 * burned-in captions rendered at about 9px and could not be read at any text
 * size. The text-size control cannot help here: those captions are pixels in a
 * file, so the only lever is how big the video is drawn.
 *
 * The caption sits OUTSIDE the rail and follows the active reel, so the video
 * gets the full column instead of splitting it.
 */

type Reel = {
  id: string;
  kernel: string;
  told: string;
  chapter: string;
};

const REELS: Reel[] = [
  { id: "01", kernel: "A lock is a statement about the past.",
    told: "a hotel keycard", chapter: "consensus and fencing" },
  { id: "02", kernel: "The read set and the write set must overlap.",
    told: "three flatmates and a moved dinner", chapter: "quorums" },
  { id: "03", kernel: "Queueing is refusing slowly.",
    told: "a coffee counter in a rush", chapter: "backpressure" },
  { id: "04", kernel: "The cache is a suggestion.",
    told: "sticky notes and a filing cabinet", chapter: "caching" },
];

/* The videos are rendered files, not pages, so they cannot adapt to the reader
   the way the rest of the site does: each palette is its own encode. Manim
   falls back to the dark cut, since it is a dark palette and a third set of
   files is not worth the megabytes. */
function cutFor(theme: string | null) {
  return theme === "light" ? "paper" : "dark";
}

/* Same shape as Toggles.tsx: the theme lives on <html> before React runs, so
   React reads the DOM rather than owning the value. */
function subscribe(cb: () => void) {
  const ob = new MutationObserver(cb);
  ob.observe(document.documentElement, { attributes: true, attributeFilter: ["data-theme"] });
  return () => ob.disconnect();
}
const getTheme = () => document.documentElement.getAttribute("data-theme");

export default function Reels() {
  const theme = useSyncExternalStore(subscribe, getTheme, () => null);
  const cut = cutFor(theme);
  const railRef = useRef<HTMLDivElement>(null);
  const [active, setActive] = useState(0);

  /* One observer over all the slides. Whichever is most on screen plays; every
     other one pauses, and any reel fully off screen rewinds, so coming back to
     it starts the story rather than dropping you into the middle. */
  useEffect(() => {
    const rail = railRef.current;
    if (!rail) return;
    const io = new IntersectionObserver(
      (entries) => {
        for (const e of entries) {
          const video = e.target.querySelector("video");
          if (!video) continue;
          if (e.isIntersecting && e.intersectionRatio > 0.6) {
            setActive(Number((e.target as HTMLElement).dataset.slide));
            void video.play().catch(() => {});
          } else {
            video.pause();
            if (e.intersectionRatio === 0) video.currentTime = 0;
          }
        }
      },
      { root: rail, threshold: [0, 0.6] },
    );
    rail.querySelectorAll<HTMLElement>("[data-slide]").forEach((s) => io.observe(s));
    return () => io.disconnect();
  }, []);

  const goTo = (i: number) =>
    railRef.current
      ?.querySelector<HTMLElement>(`[data-slide="${i}"]`)
      ?.scrollIntoView({ behavior: "smooth", block: "nearest" });

  const current = REELS[active];

  return (
    <div className="reels">
      <div className="reelRail" ref={railRef} tabIndex={0} aria-label="Reel feed">
        {REELS.map((r, i) => (
          <div className="reelSlide" data-slide={i} key={r.id}>
            <video
              /* keyed on the cut: swapping src alone leaves the previous
                 decoded frame on screen until the new file buffers, which
                 reads as the theme toggle being broken */
              key={cut}
              src={`/reels/reel${r.id}-${cut}.mp4`}
              muted
              loop
              playsInline
              preload={i === 0 ? "auto" : "none"}
              aria-label={`Reel ${r.id}: ${r.kernel}`}
              onClick={(e) => {
                const v = e.currentTarget;
                if (v.paused) void v.play();
                else v.pause();
              }}
            />
          </div>
        ))}
      </div>

      <div className="reelSide">
        <p className="reelNum">
          reel {current.id} <span>·</span> {current.chapter}
        </p>
        <p className="reelKernel">{current.kernel}</p>
        <p className="reelTold">Told as {current.told}.</p>

        <nav className="reelDots" aria-label="Jump to a reel">
          {REELS.map((r, i) => (
            <button
              key={r.id}
              className="reelDot"
              aria-current={i === active}
              aria-label={`Reel ${r.id}: ${r.kernel}`}
              onClick={() => goTo(i)}
            >
              {r.id}
            </button>
          ))}
        </nav>
        <p className="reelHint">Scroll the reel for the next one. Click it to pause.</p>
      </div>
    </div>
  );
}
