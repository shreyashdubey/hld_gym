import type { MetadataRoute } from "next";

/* Required under output: "export" — a metadata route is a route handler, and
   the build refuses to prerender one without it. */
export const dynamic = "force-static";

/* Enough for "add to home screen" to produce the h mark and the right chrome
   colour, and no more. There is no offline story here and no service worker:
   this is a static page, and a cache that can serve a stale price is a
   liability, not a feature. */
export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "HLD Gym",
    short_name: "HLD Gym",
    description: "System design for senior interviews. The book is free.",
    start_url: "/",
    display: "browser",
    background_color: "#ffffff",
    theme_color: "#ff5c00",
    icons: [
      { src: "/icon.svg", type: "image/svg+xml", sizes: "any", purpose: "any" },
      { src: "/apple-icon.png", type: "image/png", sizes: "180x180" },
    ],
  };
}
