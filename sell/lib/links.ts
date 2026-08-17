/* The reservation form: five questions, an email, and the payment link comes
   back by hand within 24 hours. Shared because the page and the rep both end in
   the same call to action, and two copies of a URL is one copy that goes stale.

   Read at build time. Vercel runs no build for this repo (SYSTEM.md §8), so an
   env var set in the dashboard is never seen; the fallback below is what ships
   unless the variable is present for `npm run publish:book`. */
export const RESERVE_URL =
  process.env.NEXT_PUBLIC_RESERVE_URL ?? "https://forms.gle/hkf5buMLV6PsAomp8";

/* Same origin: the sprint owns the site root, the book sits at /book. Plain <a>
   everywhere it is used, because the book is a static file another pipeline
   builds, not a page Next knows about. */
export const BOOK_URL = "/book/";

/* The price, as the buttons print it. It has changed once already ($39 to $19)
   and the CTAs in the rep and on the page shipped out of step. */
export const PRICE = "$19";
