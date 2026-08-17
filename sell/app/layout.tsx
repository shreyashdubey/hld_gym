import type { Metadata } from "next";
import { Archivo, Literata, IBM_Plex_Mono } from "next/font/google";
import { PREFS_INIT_SCRIPT } from "@/lib/prefs";
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
const SITE = "https://hld-gym.vercel.app";

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
      </head>
      <body>{children}</body>
    </html>
  );
}
