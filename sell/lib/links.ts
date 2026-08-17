/* The reservation form: four questions, an email, and the payment link comes
   back by hand within 24 hours. Shared because the page and the rep both end in
   the same call to action, and two copies of a URL is one copy that goes stale.

   Read at build time. Vercel runs no build for this repo (SYSTEM.md §8), so an
   env var set in the dashboard is never seen; the fallback below is what ships
   unless the variable is present for `npm run publish:book`. */
export const RESERVE_URL =
  process.env.NEXT_PUBLIC_RESERVE_URL ?? "https://forms.gle/hkf5buMLV6PsAomp8";
