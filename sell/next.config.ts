import type { NextConfig } from "next";

/* The sprint is the site root; the book lives at /book. Both are static files
   inside the book repo's existing Vercel project, so there is one deployment.

   output: "export" is possible because the page uses no server features: it is
   prerendered static and all its JavaScript is client-side. No basePath — this
   app owns "/". */
const nextConfig: NextConfig = {
  output: "export",
  trailingSlash: true,
  images: { unoptimized: true },
};

/* Dev only. `next dev` serves public/ but does no directory-index resolution,
   so the symlinked public/book/index.html answers /book/index.html and 404s on
   /book/ — which is the URL every link on the page uses. In production the
   static host resolves the directory itself, so this rewrite is neither needed
   nor included: `output: "export"` drops rewrites at build time. */
if (process.env.NODE_ENV === "development") {
  nextConfig.rewrites = async () => [
    { source: "/book", destination: "/book/index.html" },
    { source: "/book/", destination: "/book/index.html" },
  ];
}

export default nextConfig;
