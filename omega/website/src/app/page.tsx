import { CopyCommand, Reveal } from "@/components/site/interactive";
import {
  commands,
  layers,
  measured,
  providers,
  quotes,
  site,
  thesis,
  timeline,
  upcoming,
} from "@/lib/content";

const PAD = "px-6 md:px-12";

function Label({ children }: { children: React.ReactNode }) {
  return <p className="label m-0 mb-5 text-ink-muted">{children}</p>;
}

/**
 * Faint engraved marginalia. Decorative only — real mathematics, set in the
 * display face at low opacity, the way a textbook plate sits under the text.
 */
function Plate({ children, className }: { children: string; className: string }) {
  return (
    <span
      aria-hidden="true"
      className={`pointer-events-none absolute select-none font-serif italic text-oxblood/[0.07] dark:text-oxblood/[0.10] ${className}`}
    >
      {children}
    </span>
  );
}

export default function Home() {
  return (
    <>
      {/* ── Hero ─────────────────────────────────────────────── */}
      <section className={`relative overflow-hidden border-b border-rule ${PAD} py-20 md:py-28`}>
        <Plate className="right-4 top-6 text-7xl md:right-14 md:text-8xl">
          e&#8535;&#960; + 1 = 0
        </Plate>
        <Plate className="-left-2 bottom-8 text-6xl md:left-6">&#8747;</Plate>

        <Reveal>
          <div className="grid gap-x-12 md:grid-cols-12">
            <div className="md:col-span-8">
              <p className="m-0 font-serif text-[5.5rem] leading-[0.85] text-oxblood md:text-[7rem]">
                &#937;
              </p>
              <h1 className="mt-6 max-w-[18ch] text-4xl leading-[1.08] md:text-6xl">
                {site.tagline}
              </h1>
              <p className="mt-6 max-w-[52ch] text-lg text-ink-muted">{thesis}</p>
            </div>

            <dl className="mt-10 flex gap-10 self-end md:col-span-4 md:mt-0 md:flex-col md:gap-5">
              {measured.slice(0, 3).map((m) => (
                <div key={m.label} className="border-l border-rule-strong pl-4">
                  <dt className="label m-0 text-ink-muted">{m.label}</dt>
                  <dd className="tnum m-0 font-serif text-3xl">{m.tier2}</dd>
                </div>
              ))}
            </dl>
          </div>
        </Reveal>
      </section>

      {/* ── Run it ───────────────────────────────────────────── */}
      <section className={`border-b border-rule ${PAD} py-16`}>
        <Reveal>
          <Label>Run it</Label>
          <div className="grid gap-10 md:grid-cols-12">
            <div className="md:col-span-7">
              <div className="border border-rule bg-term font-mono text-[13px] leading-relaxed">
                <div className="flex items-center gap-1.5 border-b border-rule px-4 py-2.5">
                  <span className="h-2 w-2 rounded-full bg-oxblood/40" />
                  <span className="h-2 w-2 rounded-full bg-forest/40" />
                  <span className="h-2 w-2 rounded-full bg-ink-muted/30" />
                  <span className="label ml-2 text-ink-muted">omega</span>
                </div>
                <div className="overflow-x-auto px-4 py-4">
                  {commands.map((c) => (
                    <div key={c.cmd} className="whitespace-pre pb-2 last:pb-0">
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

            <div className="md:col-span-5">
              <h2 className="mt-0 text-2xl">No package to install.</h2>
              <p className="mt-3 text-ink-muted">
                Clone it and run it. There is nothing published to PyPI or npm, and there will not
                be until it earns it. Pull requests are welcome — new providers especially.
              </p>
              <div className="mt-6 flex flex-wrap items-center gap-3">
                <code className="border border-rule bg-paper-raised px-3 py-1.5 font-mono text-[13px]">
                  git clone {site.repo.replace("https://", "")}
                </code>
                <CopyCommand value={`git clone ${site.repo}.git`} />
              </div>
            </div>
          </div>
        </Reveal>
      </section>

      {/* ── The stack ────────────────────────────────────────── */}
      <section className={`relative overflow-hidden border-b border-rule ${PAD} py-16`}>
        <Plate className="-right-3 top-1/3 text-8xl md:right-8">&#8721;</Plate>

        <Reveal>
          <Label>The stack</Label>
          <div className="grid gap-x-12 gap-y-8 md:grid-cols-12">
            <div className="md:col-span-5">
              <h2 className="mt-0 text-3xl">Dependencies point one way.</h2>
              <p className="mt-4 text-ink-muted">
                An arrow means <em>this layer knows the other exists</em> — knowledge, not data.
                Data moves both ways; knowledge only downward. That single rule is why{" "}
                <code className="font-mono text-[0.9em]">loop.py</code> is still 190 lines while the
                system around it reached 4,654.
              </p>
            </div>

            <ol className="m-0 list-none space-y-0 p-0 md:col-span-7">
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

      {/* ── Providers ────────────────────────────────────────── */}
      <section className={`border-b border-rule ${PAD} py-16`}>
        <Reveal>
          <Label>Two providers, one interface</Label>
          <div className="grid gap-8 md:grid-cols-2">
            {providers.map((p) => (
              <article key={p.name} className="border-t-2 border-oxblood pt-5">
                <h3 className="m-0 text-2xl">{p.name}</h3>
                <p className="m-0 mt-1 font-mono text-xs text-ink-muted">{p.file}</p>
                <p className="mt-4 text-ink-muted">{p.detail}</p>
              </article>
            ))}
          </div>
          <p className="mt-10 max-w-[62ch] border-l-2 border-rule-strong pl-5 text-ink-muted">
            Adding the second adapter changed no file above Layer 1. That was the test — if the
            interface had needed to move, Tier 1 would have been wrong.
          </p>
        </Reveal>
      </section>

      {/* ── Roadmap ──────────────────────────────────────────── */}
      <section className={`relative overflow-hidden border-b border-rule ${PAD} py-16`}>
        <Plate className="-left-4 top-10 text-7xl md:left-4">&#8706;x</Plate>

        <Reveal>
          <Label>Where it is</Label>
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
                Every one of these plugs into a seam that already exists. None requires moving the
                loop.
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

      {/* ── Measured ─────────────────────────────────────────── */}
      <section className={`border-b border-rule ${PAD} py-16`}>
        <Reveal>
          <Label>Measured, not estimated</Label>
          <div className="overflow-x-auto">
            <table className="w-full border-collapse text-left">
              <thead>
                <tr className="border-b border-rule-strong">
                  <th className="label py-3 pr-6 font-medium text-ink-muted">&nbsp;</th>
                  <th className="label py-3 pr-6 font-medium text-ink-muted">Tier 1</th>
                  <th className="label py-3 font-medium text-ink-muted">Tier 2</th>
                </tr>
              </thead>
              <tbody>
                {measured.map((m) => (
                  <tr key={m.label} className="border-b border-rule">
                    <td className="py-3 pr-6">{m.label}</td>
                    <td className="tnum py-3 pr-6 font-mono text-sm text-ink-muted">{m.tier1}</td>
                    <td className="tnum py-3 font-mono text-sm">{m.tier2}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="mt-6 max-w-[64ch] text-sm text-ink-muted">
            Every estimate in the design notes ran low — Tier 1 was predicted at ~700 lines and came
            in at 1,577. The pattern is consistent enough to use: assume any estimate here is
            roughly 1.3–2× low.
          </p>
        </Reveal>
      </section>

      {/* ── Quotes ───────────────────────────────────────────── */}
      <section className={`relative overflow-hidden ${PAD} py-20`}>
        <Plate className="bottom-6 right-2 text-8xl md:right-10">&#960;</Plate>

        <Reveal>
          <ul className="m-0 grid list-none gap-10 p-0 md:grid-cols-3">
            {quotes.map((q) => (
              <li key={q.who}>
                <blockquote className="m-0 border-t border-rule-strong pt-5">
                  <p className="m-0 font-serif text-xl italic leading-snug">
                    &ldquo;{q.text}&rdquo;
                  </p>
                  <footer className="mt-4 text-sm not-italic text-ink-muted">
                    {q.who}
                    {q.src && <span className="block text-xs">{q.src}</span>}
                  </footer>
                </blockquote>
              </li>
            ))}
          </ul>
        </Reveal>
      </section>
    </>
  );
}
