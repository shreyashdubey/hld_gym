"use client";

import { useEffect, useRef, useState, useSyncExternalStore } from "react";

/**
 * The reel feed — swipe one, get the next, exactly the way a phone feed works,
 * because that is the habit this is borrowing.
 *
 * Everything here is deliberate about NOT being an autoplaying wall of video:
 * one reel plays at a time, the one you are actually looking at, and it stops
 * the moment it leaves. Nothing plays until you scroll to it.
 */

type Reel = {
  id: string;
  kernel: string;
  told: string;
  chapter: string;
};

const REELS: Reel[] = [
  { id: "01", kernel: "A lock is a statement about the past.",
    told: "a hotel keycard", chapter: "consensus & fencing" },
  { id: "02", kernel: "The read set and the write set must overlap.",
    told: "three flatmates and a moved dinner", chapter: "quorums" },
  { id: "03", kernel: "Queueing is refusing slowly.",
    told: "a coffee counter in a rush", chapter: "backpressure" },
  { id: "04", kernel: "The cache is a suggestion.",
    told: "sticky notes and a filing cabinet", chapter: "caching" },
];

/* The videos are rendered files, not pages, so they cannot adapt to the reader
   the way the rest of the site does — each palette is its own encode. Manim
   falls back to the dark cut: it is a dark palette, and cutting a third set of
   files to serve one toggle is not worth the megabytes. */
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
     other one pauses and rewinds, so returning to a reel starts it over rather
     than dropping you into the middle of a story. */
  useEffect(() => {
    const rail = railRef.current;
    if (!rail) return;
    const slides = Array.from(rail.querySelectorAll<HTMLElement>("[data-slide]"));

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
    slides.forEach((s) => io.observe(s));
    return () => io.disconnect();
  }, []);

  const goTo = (i: number) => {
    const rail = railRef.current;
    const slide = rail?.querySelector<HTMLElement>(`[data-slide="${i}"]`);
    slide?.scrollIntoView({ behavior: "smooth", block: "nearest" });
  };

  return (
    <div className="reels">
      <div className="reelRail" ref={railRef} tabIndex={0} aria-label="Reel feed">
        {REELS.map((r, i) => (
          <article className="reelSlide" data-slide={i} key={r.id}>
            <div className="reelFrame">
              <video
                /* key on the cut: swapping src alone leaves the old decoded
                   frame on screen until the new one buffers, which looks like
                   the theme toggle broke. */
                key={cut}
                src={`/reels/reel${r.id}-${cut}.mp4`}
                muted
                loop
                playsInline
                preload={i === 0 ? "auto" : "none"}
                onClick={(e) => {
                  const v = e.currentTarget;
                  if (v.paused) void v.play();
                  else v.pause();
                }}
              />
            </div>
            <div className="reelMeta">
              <p className="reelNum">
                reel {r.id} <span>·</span> {r.chapter}
              </p>
              <p className="reelKernel">{r.kernel}</p>
              <p className="reelTold">Told as {r.told}.</p>
            </div>
          </article>
        ))}
      </div>

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
    </div>
  );
}
