import type { MetadataRoute } from "next";
import { SITE } from "@/lib/site";
/* Required under output: "export". A metadata route is a route handler, and the
   build refuses to prerender one without this, with:
   'export const dynamic = "force-static" not configured on route ... with
   "output: export"'. */
export const dynamic = "force-static";


/* Static export emits this as /robots.txt at build time; there is no server to
   answer for it at request time.
 *
 * Everything is crawlable. The book is 284,000 words of the thing people are
 * searching for, and it is free on purpose: it is the distribution. There is
 * nothing here worth hiding from a crawler and no private area to protect. */
export default function robots(): MetadataRoute.Robots {
  return {
    rules: { userAgent: "*", allow: "/" },
    sitemap: `${SITE}/sitemap.xml`,
  };
}
