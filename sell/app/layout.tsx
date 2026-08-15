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

const TITLE = "System Design Sprint: 30 reps, 30 days";
const DESC =
  "You have read the chapters. The sprint makes you rebuild them from memory, then takes your answer apart. 30 reps, one a day, starting 1 September.";

export const metadata: Metadata = {
  title: TITLE,
  description: DESC,
  openGraph: { title: TITLE, description: DESC, type: "website" },
  twitter: { card: "summary_large_image", title: TITLE, description: DESC },
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
