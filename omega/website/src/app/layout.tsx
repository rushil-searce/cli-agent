import type { Metadata } from "next";
import Link from "next/link";
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

const NAV = [
  { label: "Docs", href: "/docs" },
  { label: "Rant", href: "/rant" },
  { label: "Lessons", href: "/lessons" },
  { label: "Roadmap", href: "/roadmap" },
] as const;

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body
        className={`${garamond.variable} ${plexSans.variable} ${plexMono.variable} antialiased`}
      >
        {/* Paper grain. feTurbulence rather than a bitmap: a few hundred bytes,
            and pointer-events:none so it never sits above anything clickable. */}
        <svg
          aria-hidden="true"
          className="pointer-events-none fixed inset-0 z-50 h-full w-full opacity-[0.13] mix-blend-multiply dark:opacity-[0.17] dark:mix-blend-soft-light"
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

        <div className="relative z-10 mx-auto flex min-h-dvh w-full max-w-6xl flex-col">
          <header className="flex items-center justify-between border-b border-rule px-6 py-5 md:px-12">
            <Link href="/" className="group flex items-baseline gap-2.5 no-underline">
              <span className="font-serif text-2xl leading-none text-oxblood">&#937;</span>
              <span className="label text-ink transition-colors duration-200 group-hover:text-oxblood">
                omega
              </span>
            </Link>

            <nav aria-label="Primary" className="flex items-center gap-5 sm:gap-7">
              {NAV.map((item) => (
                <Link
                  key={item.label}
                  href={item.href}
                  className="label cursor-pointer text-ink-muted transition-colors duration-200 hover:text-oxblood"
                >
                  {item.label}
                </Link>
              ))}
              <a
                href={site.repo}
                className="label cursor-pointer text-ink underline decoration-rule-strong underline-offset-4 transition-colors duration-200 hover:text-oxblood hover:decoration-oxblood"
              >
                GitHub
              </a>
            </nav>
          </header>

          <main className="flex-1">{children}</main>

          {/* Footer: the wordmark at full voice, the way Tau closes its page. */}
          <footer className="border-t border-rule px-6 pb-10 pt-16 md:px-12">
            <div className="grid gap-10 md:grid-cols-12">
              <div className="md:col-span-7">
                <p
                  aria-hidden="true"
                  className="m-0 select-none font-serif text-[5.5rem] leading-[0.8] text-oxblood sm:text-[8rem] md:text-[10rem]"
                >
                  &#937;
                </p>
                <p className="m-0 mt-5 max-w-[38ch] text-lg text-ink-muted">
                  Built in layers, in public. Read it end to end — that was the point.
                </p>
              </div>

              <div className="flex flex-col gap-3 md:col-span-5 md:items-end md:justify-end">
                {NAV.map((item) => (
                  <Link
                    key={item.label}
                    href={item.href}
                    className="label cursor-pointer text-ink-muted transition-colors duration-200 hover:text-oxblood"
                  >
                    {item.label}
                  </Link>
                ))}
                <a
                  href={site.repo}
                  className="label cursor-pointer text-ink-muted transition-colors duration-200 hover:text-oxblood"
                >
                  GitHub
                </a>
                <p className="m-0 mt-4 text-sm text-ink-muted/80">MIT &middot; pull requests welcome</p>
              </div>
            </div>
          </footer>
        </div>
      </body>
    </html>
  );
}
