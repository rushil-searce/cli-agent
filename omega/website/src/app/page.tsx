import { CopyCommand, Reveal } from "@/components/site/interactive";
import {
  claims,
  commands,
  layers,
  providers,
  site,
  thesis,
  timeline,
  upcoming,
} from "@/lib/content";

const PAD = "px-6 md:px-12";

function Heading({ children }: { children: React.ReactNode }) {
  return <p className="label m-0 mb-6 text-ink-muted">{children}</p>;
}

/**
 * One engraved plate, not scattered glyphs: a radian construction on the unit
 * circle, drawn in hairlines the way a textbook figure is. Decorative — it sits
 * behind the hero and never competes with the text.
 */
function Construction() {
  return (
    <svg
      aria-hidden="true"
      viewBox="0 0 200 200"
      className="pointer-events-none absolute -right-16 -top-10 h-[26rem] w-[26rem] text-oxblood/[0.09] md:right-0 md:h-[34rem] md:w-[34rem] dark:text-oxblood/[0.13]"
      fill="none"
      stroke="currentColor"
      strokeWidth="0.5"
    >
      <circle cx="100" cy="100" r="72" />
      <circle cx="100" cy="100" r="52" strokeDasharray="2 3" />
      <line x1="14" y1="100" x2="186" y2="100" />
      <line x1="100" y1="14" x2="100" y2="186" />
      {/* the radius at one radian, and the arc it subtends */}
      <line x1="100" y1="100" x2="138.9" y2="39.4" />
      <path d="M 172 100 A 72 72 0 0 0 138.9 39.4" strokeWidth="1.1" />
      <path d="M 124 100 A 24 24 0 0 0 113 79.8" strokeWidth="0.5" />
      <circle cx="138.9" cy="39.4" r="1.8" fill="currentColor" stroke="none" />
      <circle cx="100" cy="100" r="1.8" fill="currentColor" stroke="none" />
      {/* inscribed square — the compass-and-straightedge tell */}
      <path d="M 100 28 L 172 100 L 100 172 L 28 100 Z" strokeDasharray="1 4" />
    </svg>
  );
}

export default function Home() {
  return (
    <>
      {/* ── Hero ─────────────────────────────────────────────── */}
      <section className={`relative overflow-hidden border-b border-rule ${PAD} py-16 md:py-20`}>
        <Construction />

        <Reveal>
          <div className="grid items-center gap-x-12 gap-y-12 md:grid-cols-12">
            <div className="md:col-span-6">
              <div className="mb-7 flex items-baseline gap-3">
                <span className="font-serif text-4xl leading-none text-oxblood">&#937;</span>
                <span className="label text-ink-muted">{site.eyebrow}</span>
              </div>

              <h1 className="m-0 text-4xl leading-[1.06] md:text-[3.35rem]">
                {site.headline}
                <span className="block text-ink-muted">{site.headlineRest}</span>
              </h1>

              <p className="mt-6 max-w-[46ch] text-lg text-ink-muted">{thesis}</p>

              <div className="mt-9 flex flex-wrap items-center gap-3">
                <code className="border border-rule bg-paper-raised px-3.5 py-2 font-mono text-[13px]">
                  git clone {site.repo.replace("https://", "")}
                </code>
                <CopyCommand value={`git clone ${site.repo}.git`} />
                <a
                  href={site.repo}
                  className="label cursor-pointer border-b border-rule-strong pb-0.5 text-ink transition-colors hover:border-oxblood hover:text-oxblood"
                >
                  GitHub &#8599;
                </a>
              </div>

              <p className="mt-5 max-w-[44ch] text-sm text-ink-muted">
                Nothing is published to PyPI or npm, and nothing will be until it earns it. Clone
                it, run it, send a pull request — new providers especially.
              </p>
            </div>

            <div className="md:col-span-6">
              <div className="border border-rule bg-term font-mono text-[13px] leading-relaxed">
                <div className="flex items-center gap-1.5 border-b border-rule px-4 py-2.5">
                  <span className="h-2 w-2 rounded-full bg-oxblood/40" />
                  <span className="h-2 w-2 rounded-full bg-forest/40" />
                  <span className="h-2 w-2 rounded-full bg-ink-muted/30" />
                  <span className="label ml-2 text-ink-muted">omega</span>
                </div>
                <div className="overflow-x-auto px-4 py-4">
                  {commands.map((c) => (
                    <div key={c.cmd} className="whitespace-pre pb-2.5 last:pb-0">
                      <span className="text-oxblood">$ </span>
                      <span>{c.cmd}</span>
                      {"\n"}
                      <span className="text-ink-muted">
                        {"  "}
                        {c.note}
                      </span>
                    </div>
                  ))}
                  <div className="mt-3 whitespace-pre border-t border-rule pt-3">
                    <span className="text-oxblood">$ </span>
                    <span>uv run pytest -q</span>
                    {"\n"}
                    <span className="text-forest">{"  "}289 passed</span>
                    <span className="text-ink-muted"> in 1.7s</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </Reveal>
      </section>

      {/* ── the loop ─────────────────────────────────────────── */}
      <section className={`border-b border-rule ${PAD} py-16`}>
        <Reveal>
          <Heading>the loop</Heading>
          <div className="grid gap-x-12 gap-y-10 md:grid-cols-12">
            <h2 className="m-0 text-3xl md:col-span-5">
              Ask, run what it asks for, report back, repeat.
            </h2>
            <p className="m-0 max-w-[60ch] text-lg text-ink-muted md:col-span-7">
              That is the entire idea, and it is why the loop file is short. Everything hard —
              budgets, approvals, retries, persistence — lives <em>around</em> it, reached through
              callbacks. The loop asks; it never decides.
            </p>
          </div>

          <ul className="m-0 mt-14 grid list-none gap-x-10 gap-y-9 p-0 md:grid-cols-3">
            {claims.map((c) => (
              <li key={c.title} className="border-t border-rule-strong pt-5">
                <h3 className="m-0 text-xl leading-snug">{c.title}</h3>
                <p className="m-0 mt-3 text-ink-muted">{c.body}</p>
              </li>
            ))}
          </ul>
        </Reveal>
      </section>

      {/* ── the stack ────────────────────────────────────────── */}
      <section className={`border-b border-rule ${PAD} py-16`}>
        <Reveal>
          <Heading>the stack</Heading>
          <div className="grid gap-x-12 gap-y-8 md:grid-cols-12">
            <div className="md:col-span-5">
              <h2 className="mt-0 text-3xl">Dependencies point one way.</h2>
              <p className="mt-4 text-ink-muted">
                An arrow means <em>this layer knows the other exists</em> — knowledge, not data.
                Data moves both ways; knowledge only downward.
              </p>
              <p className="mt-4 text-ink-muted">
                Nothing above Layer&nbsp;2 can reach in and change the loop, which is the only
                reason it stayed small while the system around it reached 4,654 lines.
              </p>
            </div>

            <ol className="m-0 list-none p-0 md:col-span-7">
              {layers.map((layer, i) => (
                <li key={layer.n}>
                  <div className="grid grid-cols-[auto_1fr_auto] items-baseline gap-4 border border-rule bg-paper-raised px-5 py-4">
                    <span className="tnum label text-oxblood">L{layer.n}</span>
                    <div>
                      <h3 className="m-0 text-xl">{layer.name}</h3>
                      <p className="m-0 mt-1 text-sm text-ink-muted">{layer.detail}</p>
                    </div>
                    <span
                      className={`label ${
                        layer.state === "built" ? "text-forest" : "text-ink-muted"
                      }`}
                    >
                      {layer.state}
                    </span>
                  </div>
                  {i < layers.length - 1 && (
                    <div aria-hidden="true" className="flex justify-center py-1.5">
                      <svg width="11" height="20" viewBox="0 0 11 20" className="text-rule-strong">
                        <line
                          x1="5.5"
                          y1="0"
                          x2="5.5"
                          y2="14"
                          stroke="currentColor"
                          strokeWidth="1"
                        />
                        <path
                          d="M1.5 12 L5.5 18 L9.5 12"
                          fill="none"
                          stroke="currentColor"
                          strokeWidth="1"
                        />
                      </svg>
                    </div>
                  )}
                </li>
              ))}
            </ol>
          </div>
        </Reveal>
      </section>

      {/* ── two providers ────────────────────────────────────── */}
      <section className={`border-b border-rule ${PAD} py-16`}>
        <Reveal>
          <Heading>two providers, one interface</Heading>
          <div className="grid gap-10 md:grid-cols-2">
            {providers.map((p) => (
              <article key={p.name} className="border-t-2 border-oxblood pt-5">
                <h3 className="m-0 text-2xl">{p.name}</h3>
                <p className="m-0 mt-1 font-mono text-xs text-ink-muted">{p.file}</p>
                <p className="mt-4 text-ink-muted">{p.detail}</p>
              </article>
            ))}
          </div>
        </Reveal>
      </section>

      {/* ── where it is ──────────────────────────────────────── */}
      <section className={`${PAD} py-16 pb-20`}>
        <Reveal>
          <Heading>where it is</Heading>
          <div>
            {timeline.map((t, i) => (
              <div
                key={t.tier}
                className={`grid gap-x-8 gap-y-2 py-7 md:grid-cols-12 ${
                  i < timeline.length - 1 ? "border-b border-rule" : ""
                }`}
              >
                <div className="flex items-baseline gap-3 md:col-span-3">
                  <h3 className="m-0 font-serif text-2xl">{t.tier}</h3>
                  <span
                    className={`label ${t.status === "closed" ? "text-forest" : "text-oxblood"}`}
                  >
                    {t.status}
                  </span>
                </div>
                <div className="md:col-span-9">
                  <p className="m-0 text-xl">{t.headline}</p>
                  <p className="m-0 mt-2 max-w-[64ch] text-ink-muted">{t.body}</p>
                </div>
              </div>
            ))}
          </div>

          <div className="mt-12 grid gap-x-12 gap-y-8 border-t border-rule-strong pt-10 md:grid-cols-12">
            <div className="md:col-span-4">
              <h3 className="m-0 text-xl">What Tier 3 adds</h3>
              <p className="mt-3 text-sm text-ink-muted">
                Every one plugs into a seam that already exists. None requires moving the loop.
              </p>
            </div>
            <ul className="m-0 grid list-none gap-x-8 gap-y-4 p-0 md:col-span-8 md:grid-cols-2">
              {upcoming.map((u) => (
                <li key={u.name}>
                  <p className="m-0 font-medium">{u.name}</p>
                  <p className="m-0 mt-0.5 text-sm text-ink-muted">{u.seam}</p>
                </li>
              ))}
            </ul>
          </div>
        </Reveal>
      </section>

    </>
  );
}
