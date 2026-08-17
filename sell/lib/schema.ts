import { SITE } from "@/lib/site";
import { REELS, REEL_DATE, REEL_DURATION } from "@/lib/reels";

/**
 * JSON-LD for the site root.
 *
 * Every claim here has to be true, for the same reason the visible copy does:
 * structured data is a statement to a machine that will repeat it in a search
 * result, where nobody can see the caveat next to it.
 *
 * So there is deliberately **no `aggregateRating` and no `review`**. Nobody has
 * bought this yet, so there is nothing to average. Those two properties are the
 * most commonly faked in the format and the easiest to get a manual penalty for.
 *
 * The offer says `PreOrder`, not `InStock`, because it is a presale and the
 * product ships on 1 September. That is the same thing the page says twice in
 * words, and the machine-readable version must not quietly say something
 * stronger.
 */
export const SCHEMA = {
  "@context": "https://schema.org",
  "@graph": [
    /* One VideoObject per reel actually on the page. Four, not the 450 the
       sprint promises: structured data describes what is here now. */
    ...REELS.map((r) => ({
      "@type": "VideoObject",
      "@id": `${SITE}/#reel${r.id}`,
      name: r.kernel,
      description: r.summary,
      thumbnailUrl: `${SITE}/reels/reel${r.id}-dark.jpg`,
      contentUrl: `${SITE}/reels/reel${r.id}-dark.mp4`,
      uploadDate: REEL_DATE,
      duration: REEL_DURATION,
      inLanguage: "en",
      isFamilyFriendly: true,
      publisher: { "@id": `${SITE}/#org` },
    })),
    {
      "@type": "Organization",
      "@id": `${SITE}/#org`,
      name: "HLD Gym",
      url: `${SITE}/`,
      logo: `${SITE}/icon.svg`,
    },
    {
      "@type": "WebSite",
      "@id": `${SITE}/#website`,
      url: `${SITE}/`,
      name: "HLD Gym",
      inLanguage: "en",
      publisher: { "@id": `${SITE}/#org` },
    },
    {
      /* The book is the distribution and the thing worth ranking: 51 chapters
         of the exact phrases people search for, free and with no signup. */
      "@type": "Book",
      "@id": `${SITE}/book/#book`,
      name: "HLD Gym: system design for senior interviews",
      url: `${SITE}/book/`,
      inLanguage: "en",
      isAccessibleForFree: true,
      bookFormat: "https://schema.org/EBook",
      numberOfPages: 51,
      publisher: { "@id": `${SITE}/#org` },
      author: { "@id": `${SITE}/#org` },
      about: [
        "System design interview",
        "Distributed systems",
        "Software architecture",
      ],
    },
    {
      "@type": "Product",
      "@id": `${SITE}/#sprint`,
      name: "30-day system design sprint",
      url: `${SITE}/`,
      description:
        "Thirty days of reps. A diagram teaches itself, then it is taken away and " +
        "you rebuild it from memory while an interviewer pushes back on what you said.",
      brand: { "@id": `${SITE}/#org` },
      image: `${SITE}/og.png`,
      offers: {
        "@type": "Offer",
        price: "19",
        priceCurrency: "USD",
        /* Presale. The product does not exist yet and the page says so. */
        availability: "https://schema.org/PreOrder",
        availabilityStarts: "2026-09-01",
        url: `${SITE}/`,
        seller: { "@id": `${SITE}/#org` },
      },
    },
  ],
};
