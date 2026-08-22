import type { MetadataRoute } from "next";
import { SITE } from "@/lib/site";
/* Required under output: "export". A metadata route is a route handler, and the
   build refuses to prerender one without this, with:
   'export const dynamic = "force-static" not configured on route ... with
   "output: export"'. */
export const dynamic = "force-static";


/* Two URLs, because the site has two pages. /book/ is a static file written by
 * a different pipeline, which Next knows nothing about, so it is listed by hand
 * rather than discovered.
 *
 * No lastModified: it would be re-stamped on every build and show up as a diff
 * in the committed dist/ whether or not anything changed. An untrue lastmod is
 * worse than none, and Google discounts the field anyway. */
export default function sitemap(): MetadataRoute.Sitemap {
  return [{ url: `${SITE}/` }, { url: `${SITE}/book/` }, { url: `${SITE}/origins/` }];
}
