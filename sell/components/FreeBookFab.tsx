"use client";

import { useEffect, useRef } from "react";

/* A floating route to the free book, phones only.

   It slides up once and then holds still. An earlier version blinked and shook
   every few seconds and it looked cheap: a solid accent block on a white page
   is already the loudest thing in the viewport, and moving it only makes it
   look unsure of that. The label carries a number rather than an adjective,
   because "51 chapters" is a reason where "free" is only a claim.

   It is shown between two boundaries, not from the top of the page:

   - not until the hero has left, because up there the hero already offers the
     book twice and a floater over that is clutter;
   - never while the price box is on screen, because that is an accent fill and
     two accent fills in one viewport leave the eye with no primary action
     (DESIGN-SYSTEM §2.2). When the buy button is visible, it wins.

   Class toggling happens on the DOM rather than in React state, so no setState
   runs in an effect and the button costs nothing until an observer fires. */

export default function FreeBookFab() {
  const ref = useRef<HTMLAnchorElement>(null);

  useEffect(() => {
    const el = ref.current;
    const hero = document.querySelector(".hero");
    const offer = document.querySelector(".pricebox");
    if (!el || !hero) return;

    let heroGone = false;
    let offerShowing = false;
    const apply = () => el.classList.toggle("fabOn", heroGone && !offerShowing);

    const heroIo = new IntersectionObserver(
      ([e]) => {
        heroGone = !e.isIntersecting;
        apply();
      },
      { threshold: 0 },
    );
    heroIo.observe(hero);

    const offerIo = offer
      ? new IntersectionObserver(
          ([e]) => {
            offerShowing = e.isIntersecting;
            apply();
          },
          { threshold: 0 },
        )
      : undefined;
    offerIo?.observe(offer!);

    return () => {
      heroIo.disconnect();
      offerIo?.disconnect();
    };
  }, []);

  return (
    <a ref={ref} className="fab" href="/book/">
      <span className="fabInner">
        <span className="fabNum">51</span>
        <span>chapters, free</span>
      </span>
    </a>
  );
}
