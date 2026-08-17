"use client";

import { useEffect, useRef } from "react";
import { BOOK_URL } from "@/lib/links";

/* A floating route to the free book, phones only.

   It slides up once and then holds still. An earlier version blinked and shook
   every few seconds and it looked cheap: a solid accent block on a white page
   is already the loudest thing in the viewport, and moving it only makes it
   look unsure of that. The label carries a number rather than an adjective,
   because "51 chapters" is a reason where "free" is only a claim.

   It is shown between two boundaries, not from the top of the page:

   - not until the hero has left, because up there the hero already offers the
     book twice and a floater over that is clutter;
   - never while any other accent fill is on screen: the price box, the rep
     (its tag strip and every one of its buttons), and the book's own filled
     button. Two accent fills in one viewport leave the eye with no primary
     action (DESIGN-SYSTEM §2.2), and on a phone the floater was also sitting on
     top of the probe textareas while the visitor typed.

   Class toggling happens on the DOM rather than in React state, so no setState
   runs in an effect and the button costs nothing until an observer fires. */

export default function FreeBookFab() {
  const ref = useRef<HTMLAnchorElement>(null);

  useEffect(() => {
    const el = ref.current;
    const hero = document.querySelector(".hero");
    if (!el || !hero) return;

    let heroGone = false;
    const rivalsShowing = new Set<Element>();
    const apply = () =>
      el.classList.toggle("fabOn", heroGone && rivalsShowing.size === 0);

    const heroIo = new IntersectionObserver(
      ([e]) => {
        heroGone = !e.isIntersecting;
        apply();
      },
      { threshold: 0 },
    );
    heroIo.observe(hero);

    const rivalIo = new IntersectionObserver(
      (entries) => {
        for (const e of entries) {
          if (e.isIntersecting) rivalsShowing.add(e.target);
          else rivalsShowing.delete(e.target);
        }
        apply();
      },
      { threshold: 0 },
    );
    document.querySelectorAll(".pricebox, .rep, .bookBtn").forEach((r) => rivalIo.observe(r));

    return () => {
      heroIo.disconnect();
      rivalIo.disconnect();
    };
  }, []);

  return (
    <a ref={ref} className="fab" href={BOOK_URL}>
      <span className="fabInner">
        <span className="fabNum">51</span>
        <span>chapters, free</span>
      </span>
    </a>
  );
}
