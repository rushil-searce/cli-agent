import type { Metadata } from "next";
import { EB_Garamond, IBM_Plex_Mono, IBM_Plex_Sans } from "next/font/google";
import { site } from "@/lib/content";
import "./globals.css";

const garamond = EB_Garamond({
  variable: "--font-garamond",
  subsets: ["latin"],
  display: "swap",
});

const plexSans = IBM_Plex_Sans({
  variable: "--font-plex-sans",
  subsets: ["latin"],
  weight: ["400", "500", "600"],
  display: "swap",
});

const plexMono = IBM_Plex_Mono({
  variable: "--font-plex-mono",
  subsets: ["latin"],
  weight: ["400", "500"],
  display: "swap",
});

export const metadata: Metadata = {
  title: "omega — a terminal coding agent",
  description: site.tagline,
};

/** Nav destinations. Docs, Rant and Lessons are Phase 2 — marked, not faked. */
const NAV = [{ label: "Docs" }, { label: "Rant" }, { label: "Lessons" }] as const;

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body
        className={`${garamond.variable} ${plexSans.variable} ${plexMono.variable} antialiased`}
      >
        {/* Paper grain. feTurbulence rather than a bitmap: a few hundred bytes,
            and it never sits above anything clickable. */}
        <svg
          aria-hidden="true"
          className="pointer-events-none fixed inset-0 z-50 h-full w-full opacity-[0.14] mix-blend-multiply dark:opacity-[0.18] dark:mix-blend-soft-light"
        >
          <filter id="paper-grain">
            <feTurbulence
              type="fractalNoise"
              baseFrequency="0.82"
              numOctaves="4"
              stitchTiles="stitch"
            />
            <feColorMatrix type="saturate" values="0" />
          </filter>
          <rect width="100%" height="100%" filter="url(#paper-grain)" />
        </svg>

        {/* The boundary: two full-height hairlines framing the measure. */}
        <div
          aria-hidden="true"
          className="pointer-events-none fixed inset-y-0 left-1/2 z-0 hidden w-full max-w-6xl -translate-x-1/2 md:block"
        >
          <div className="absolute inset-y-0 left-0 w-px bg-rule" />
          <div className="absolute inset-y-0 right-0 w-px bg-rule" />
        </div>

        <div className="relative z-10 mx-auto w-full max-w-6xl">
          <header className="flex items-center justify-between border-b border-rule px-6 py-5 md:px-12">
            <a href="#top" className="group flex items-baseline gap-2.5 no-underline">
              <span className="font-serif text-2xl leading-none text-oxblood">&#937;</span>
              <span className="label text-ink-muted transition-colors group-hover:text-ink">
                omega
              </span>
            </a>

            <nav aria-label="Primary" className="flex items-center gap-6">
              {NAV.map((item) => (
                <span
                  key={item.label}
                  aria-disabled="true"
                  title="Coming in the next phase"
                  className="label cursor-default text-ink-muted/55"
                >
                  {item.label}
                </span>
              ))}
              <a
                href={site.repo}
                className="label cursor-pointer text-ink underline decoration-rule-strong underline-offset-4 transition-colors hover:text-oxblood hover:decoration-oxblood"
              >
                GitHub
              </a>
            </nav>
          </header>

          <main id="top">{children}</main>

          <footer className="flex flex-col gap-3 border-t border-rule px-6 py-8 text-sm text-ink-muted md:flex-row md:items-center md:justify-between md:px-12">
            <p className="m-0">
              <span className="font-serif text-oxblood">&#937;</span> omega — built in layers, in
              public.
            </p>
            <a
              href={site.repo}
              className="cursor-pointer text-ink underline decoration-rule-strong underline-offset-4 transition-colors hover:text-oxblood hover:decoration-oxblood"
            >
              github.com/rushil-searce/cli-agent
            </a>
          </footer>
        </div>
      </body>
    </html>
  );
}
