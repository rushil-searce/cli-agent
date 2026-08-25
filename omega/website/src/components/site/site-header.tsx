import Link from "next/link";
import { site } from "@/lib/content";
import { NAV } from "@/lib/nav";
import { GUTTER } from "@/components/site/primitives";

/**
 * Sticky, on a solid paper ground rather than a blur — the design is opaque
 * paper and glass would fight it.
 *
 * That opacity hides the fixed boundary rails behind it, so the header draws
 * its own `border-x`. Its edges are the container's edges, so the lines
 * continue exactly where the rails stop.
 */
export function SiteHeader() {
  return (
    <header
      className={`sticky top-0 z-30 flex items-center justify-between border-b border-rule bg-paper py-5 md:border-x ${GUTTER}`}
    >
      {/* Mark and name here; the hero carries the name alone. */}
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
  );
}
