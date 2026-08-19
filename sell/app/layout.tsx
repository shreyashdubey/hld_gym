import type { Metadata } from "next";
import { Analytics } from "@vercel/analytics/next";
import { Archivo, Literata, IBM_Plex_Mono } from "next/font/google";
import { PREFS_INIT_SCRIPT } from "@/lib/prefs";
import { SCHEMA } from "@/lib/schema";
import { SITE } from "@/lib/site";
import "./globals.css";

const archivo = Archivo({
  variable: "--font-ui",
  subsets: ["latin"],
  weight: ["400", "600", "700"],
  display: "swap",
});

const literata = Literata({
  variable: "--font-read",
  subsets: ["latin"],
  weight: ["400", "600", "700"],
  style: ["normal", "italic"],
  display: "swap",
});

const plexMono = IBM_Plex_Mono({
  variable: "--font-mono",
  subsets: ["latin"],
  weight: ["400", "600"],
  display: "swap",
});

/* Title and description are read off the page: a tab, a search result, a share
   card. So the brand is in the title, and the description names the book
   rather than presuming the reader has read it. */
const TITLE = "System design sprint: 197 diagrams from memory in 30 days · HLD Gym";
const DESC =
  "Every diagram in the free HLD Gym book, rebuilt from memory while an interviewer pushes back. 197 reps and 450 reels in 30 days from 1 September. $19, refund if late.";

/* The share card is a static PNG rendered by ../reel/og.mjs into public/og.png:
   this is a static export with no server, so there is no route to generate it
   on request. metadataBase turns the relative image and canonical URLs into
   the absolute ones scrapers require. */
export const metadata: Metadata = {
  metadataBase: new URL(SITE),
  title: TITLE,
  description: DESC,
  alternates: { canonical: "/" },
  openGraph: {
    title: TITLE,
    description: DESC,
    type: "website",
    url: "/",
    siteName: "HLD Gym",
    images: [{ url: "/og.png", width: 1200, height: 630, alt: TITLE }],
  },
  twitter: { card: "summary_large_image", title: TITLE, description: DESC, images: ["/og.png"] },
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html
      lang="en"
      className={`${archivo.variable} ${literata.variable} ${plexMono.variable}`}
      suppressHydrationWarning
    >
      <head>
        <script dangerouslySetInnerHTML={{ __html: PREFS_INIT_SCRIPT }} />
        {/* Theme colour follows the OS, because the page does too until the
            reader picks one. A single value would tint the browser chrome the
            wrong way for half of them. */}
        <meta name="theme-color" media="(prefers-color-scheme: light)" content="#ffffff" />
        <meta name="theme-color" media="(prefers-color-scheme: dark)" content="#0d0d0d" />
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(SCHEMA) }}
        />
      </head>
      <body>
        {children}
        {/* Pageviews only, and the reason is the funnel's shape: the sell page
            was live and polished for three days with no counter on it, so a
            zero on the reservation form could not be told apart from a zero on
            the door. Vercel builds nothing for this repo (SYSTEM.md §8), so the
            script is baked in by the local `publish:book` and ships inside the
            committed `dist/` — and it stays silent unless Web Analytics is
            switched on in the project dashboard, which is a click there, not a
            line here. No custom events on the CTAs yet: with an unknown and
            possibly tiny denominator, a click count is noise. Add `track()` on
            the three RESERVE_URL links once pageviews prove there is traffic
            to divide by. */}
        <Analytics />
      </body>
    </html>
  );
}
