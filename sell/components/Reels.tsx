"use client";

import { useCallback, useEffect, useRef, useState, useSyncExternalStore } from "react";

/**
 * The reel feed. Swipe one, get the next, the way a phone feed works, because
 * that is the habit this is borrowing.
 *
 * The video is the object. It arrives already framed, already captioned, with
 * its own title card, so it gets one hairline and nothing else around it. An
 * earlier version put it inside a bordered slide inside a bordered rail, which
 * boxed a box twice over and squeezed the video down to 300px, where the
 * burned-in captions rendered at about 9px. The text-size control cannot help
 * there: those captions are pixels in a file, so the only lever is how large
 * the video is drawn.
 *
 * The column beside it carries the whole playlist rather than the active reel
 * alone. Four kernels in a row is the fastest possible argument for what the
 * product is, and it fills a column that a 9:16 video otherwise leaves half
 * empty.
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

/* Fullscreen is browser state too, so it is read the same way the theme is
   rather than mirrored into React with an effect. Both subscribe functions are
   module-level constants: a new function identity on every render makes
   useSyncExternalStore resubscribe on every render. */
const NEVER = () => () => {};
/* iOS Safari allows fullscreen only on a <video>, never on a container, so
   there the button would be a dead control and is not rendered at all. */
const getCanFull = () => Boolean(document.fullscreenEnabled);

function subFullscreen(cb: () => void) {
  document.addEventListener("fullscreenchange", cb);
  return () => document.removeEventListener("fullscreenchange", cb);
}
const getFull = () => document.fullscreenElement !== null;

export default function Reels() {
  const theme = useSyncExternalStore(subscribe, getTheme, () => null);
  const cut = cutFor(theme);
  const railRef = useRef<HTMLDivElement>(null);
  const [active, setActive] = useState(0);
  const canFull = useSyncExternalStore(NEVER, getCanFull, () => false);
  const full = useSyncExternalStore(subFullscreen, getFull, () => false);

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

  const goTo = useCallback((i: number) => {
    railRef.current
      ?.querySelector<HTMLElement>(`[data-slide="${i}"]`)
      ?.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }, []);

  const enterFull = () => void railRef.current?.requestFullscreen().catch(() => {});
  const exitFull = () => void document.exitFullscreen().catch(() => {});

  /* Arrow keys move between reels while the rail has focus. Scroll-snap already
     does this with a wheel; a keyboard user needs the same thing said out loud. */
  const onKey = (e: React.KeyboardEvent) => {
    if (e.key === "ArrowDown" || e.key === "ArrowRight") {
      e.preventDefault();
      goTo(Math.min(active + 1, REELS.length - 1));
    }
    if (e.key === "ArrowUp" || e.key === "ArrowLeft") {
      e.preventDefault();
      goTo(Math.max(active - 1, 0));
    }
  };

  const current = REELS[active];

  return (
    <div className="reels">
      <div
        className="reelRail"
        ref={railRef}
        tabIndex={0}
        onKeyDown={onKey}
        aria-label="Reel feed"
        data-full={full || undefined}
      >
        {REELS.map((r, i) => (
          <div
            className="reelSlide"
            data-slide={i}
            key={r.id}
            /* In fullscreen the slide is the letterbox around a 9:16 video on a
               16:9 screen, so a click here is a click outside the reel and
               dismisses it. On the page the slide is exactly the video and this
               never fires on its own. */
            onClick={full ? exitFull : undefined}
          >
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
                e.stopPropagation();       /* never reach the letterbox handler */
                if (!full && canFull) {
                  enterFull();
                  return;
                }
                const v = e.currentTarget;
                if (v.paused) void v.play();
                else v.pause();
              }}
            />
          </div>
        ))}
        {full && (
          <button className="reelClose" onClick={exitFull} aria-label="Exit fullscreen">
            &#215;
          </button>
        )}
      </div>

      <div className="reelSide">
        <p className="reelNum">
          now playing <span>·</span> {current.chapter}
        </p>
        <p className="reelKernel">{current.kernel}</p>
        <p className="reelTold">Told as {current.told}.</p>

        <p className="reelHint">
          {canFull
            ? "Click the reel for fullscreen. Scroll it for the next one."
            : "Click the reel to pause. Scroll it for the next one."}
        </p>

        <ol className="reelList" aria-label="All reels">
          {REELS.map((r, i) => (
            <li key={r.id}>
              <button
                className="reelRow"
                aria-current={i === active}
                onClick={() => goTo(i)}
              >
                <span className="rowN">{r.id}</span>
                <span className="rowK">{r.kernel}</span>
                <span className="rowC">{r.chapter}</span>
              </button>
            </li>
          ))}
        </ol>

        <p className="reelFoot">
          Four built. Ten a day on your current topic from 1 September, plus reels from topics
          you have already finished.
        </p>
      </div>
    </div>
  );
}
