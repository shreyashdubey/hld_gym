"use client";

import { useEffect, useRef } from "react";
import { BOOK_URL } from "@/lib/links";

/* The free-book button. It arrives as an outline and fills with accent, left to
   right, once, when it first scrolls into view — then it is finished and never
   moves again.

   This page's motion vocabulary is drawing: the diagram draws itself, the chart
   draws itself. A button that fills itself belongs to that language. A button
   that blinks or shakes belongs to a different, worse one, and looping motion
   in particular reads as desperate rather than confident. */

export default function BookButton({ children }: { children: React.ReactNode }) {
  const ref = useRef<HTMLAnchorElement>(null);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const io = new IntersectionObserver(
      (entries) => {
        if (entries.some((e) => e.isIntersecting)) {
          el.classList.add("bookBtnOn");
          io.disconnect();
        }
      },
      { threshold: 0.6 },
    );
    io.observe(el);
    return () => io.disconnect();
  }, []);

  return (
    <a ref={ref} className="btn bookBtn" href={BOOK_URL}>
      <span>{children}</span>
    </a>
  );
}
