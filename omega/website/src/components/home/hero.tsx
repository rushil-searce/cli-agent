import { CopyCommand, Reveal } from "@/components/site/interactive";
import { GUTTER } from "@/components/site/primitives";
import { Terminal, TerminalCommand } from "@/components/site/terminal";
import { commands, site } from "@/lib/content";

/** Graph paper across the hero, easing off only at the very end. */
function GridPaper() {
  return (
    <div
      aria-hidden="true"
      className="pointer-events-none absolute inset-0 [mask-image:linear-gradient(to_bottom,black_0%,black_72%,transparent_100%)]"
      style={{
        backgroundImage:
          "linear-gradient(to right, var(--rule) 1px, transparent 1px), linear-gradient(to bottom, var(--rule) 1px, transparent 1px)",
        backgroundSize: "64px 64px",
      }}
    />
  );
}

/** The one split layout on the site. Every other section has its own shape. */
export function Hero() {
  return (
    <section className={`relative overflow-hidden border-b border-rule py-16 md:py-20 ${GUTTER}`}>
      <GridPaper />

      <Reveal className="relative">
        <div className="grid items-center gap-x-12 gap-y-12 md:grid-cols-12">
          <div className="md:col-span-6">
            {/* Name only — the header carries the mark. */}
            <p className="label m-0 mb-7 text-ink">omega</p>

            <h1 className="m-0 max-w-[16ch] text-4xl leading-[1.08] md:text-[3.25rem]">
              {site.tagline}
            </h1>

            <p className="mt-7 max-w-[42ch] text-lg text-ink-muted">
              <span className="text-ink">{site.headline}</span> {site.headlineRest}
            </p>

            <div className="mt-9 flex flex-wrap items-center gap-3">
              <code className="border border-rule bg-paper-raised px-3.5 py-2 font-mono text-[13px]">
                git clone {site.repo.replace("https://", "")}
              </code>
              <CopyCommand value={`git clone ${site.repo}.git`} />
              <a
                href={site.repo}
                className="label cursor-pointer border-b border-rule-strong pb-0.5 text-ink transition-colors duration-200 hover:border-oxblood hover:text-oxblood"
              >
                GitHub
              </a>
            </div>

            <p className="mt-5 text-sm text-ink-muted">
              No package to install. Clone it and run it.
            </p>
          </div>

          <div className="md:col-span-6">
            <Terminal>
              {commands.map((c) => (
                <TerminalCommand key={c.cmd} cmd={c.cmd} note={c.note} />
              ))}
              <div className="mt-3 whitespace-pre border-t border-rule pt-3">
                <span className="text-oxblood">$ </span>
                <span>uv run pytest -q</span>
                {"\n"}
                <span className="text-forest">{"  "}289 passed</span>
                <span className="text-ink-muted"> in 1.7s</span>
              </div>
            </Terminal>
          </div>
        </div>
      </Reveal>
    </section>
  );
}
