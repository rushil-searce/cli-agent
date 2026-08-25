import { CopyCommand, Reveal } from "@/components/site/interactive";
import { claims, commands, layers, providers, site, timeline, upcoming } from "@/lib/content";

const PAD = "px-6 md:px-12";

function Heading({ children }: { children: React.ReactNode }) {
  return <p className="label m-0 mb-6 text-ink-muted">{children}</p>;
}

/**
 * The loop, drawn. Four stations and the exit — this is the mechanism the whole
 * project is about, so it earns a figure rather than a decorative glyph.
 *
 * It occupies its own grid cell. Nothing is layered behind anything else, which
 * is the only reliable way to guarantee a diagram never collides with text.
 */
function LoopFigure() {
  const stations = [
    { x: 100, y: 26, label: "ask" },
    { x: 174, y: 100, label: "requests a tool" },
    { x: 100, y: 174, label: "run it" },
    { x: 26, y: 100, label: "report back" },
  ];

  return (
    <figure className="m-0">
      <svg
        viewBox="0 0 200 200"
        role="img"
        aria-label="The agent loop: ask, the model requests a tool, run it, report back, repeat until no tool is requested."
        className="h-auto w-full max-w-[22rem] text-rule-strong"
        fill="none"
        stroke="currentColor"
      >
        {/* the cycle */}
        <circle cx="100" cy="100" r="58" strokeWidth="1" strokeDasharray="3 4" />

        {/* direction arrows on the cycle */}
        {[
          "M 148 72 L 152 82 L 142 84",
          "M 128 152 L 118 156 L 116 146",
          "M 52 128 L 48 118 L 58 116",
          "M 72 48 L 82 44 L 84 54",
        ].map((d) => (
          <path key={d} d={d} strokeWidth="1.2" className="text-oxblood" />
        ))}

        {stations.map((s) => (
          <g key={s.label}>
            <circle cx={s.x} cy={s.y} r="4.5" className="fill-paper text-oxblood" strokeWidth="1.4" />
          </g>
        ))}

        {/* the exit: no tool requested, the run ends */}
        <line x1="100" y1="158" x2="100" y2="192" strokeWidth="1" className="text-forest" />
        <path d="M 95 185 L 100 194 L 105 185" strokeWidth="1.2" className="text-forest" />
      </svg>

      <figcaption className="mt-5 grid gap-1.5">
        {["ask", "it requests a tool", "run it", "report back"].map((step, i) => (
          <span key={step} className="flex items-baseline gap-3 text-sm">
            <span className="tnum label text-oxblood">{i + 1}</span>
            <span className="text-ink-muted">{step}</span>
          </span>
        ))}
        <span className="mt-2 flex items-baseline gap-3 border-t border-rule pt-2.5 text-sm">
          <span className="label text-forest">stop</span>
          <span className="text-ink-muted">no tool requested</span>
        </span>
      </figcaption>
    </figure>
  );
}

export default function Home() {
  return (
    <>
      {/* ── Hero ─────────────────────────────────────────────── */}
      <section className={`border-b border-rule ${PAD} py-16 md:py-20`}>
        <Reveal>
          <div className="grid items-center gap-x-12 gap-y-12 md:grid-cols-12">
            <div className="md:col-span-6">
              <div className="mb-7 flex items-baseline gap-3">
                <span className="font-serif text-4xl leading-none text-oxblood">&#937;</span>
                <span className="label text-ink">omega</span>
              </div>

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
                  GitHub &#8599;
                </a>
              </div>

              <p className="mt-5 text-sm text-ink-muted">
                No package to install. Clone it and run it.
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
          <div className="grid gap-x-12 gap-y-12 md:grid-cols-12">
            <div className="md:col-span-7">
              <h2 className="m-0 max-w-[18ch] text-3xl">
                Ask, run what it asks for, report back, repeat.
              </h2>
              <p className="mt-5 max-w-[52ch] text-lg text-ink-muted">
                That is the whole mechanism. Everything hard — budgets, approvals, retries,
                persistence — lives <em>around</em> it, reached through callbacks. The loop asks; it
                never decides.
              </p>

              <ul className="m-0 mt-10 grid list-none gap-x-10 gap-y-7 p-0 sm:grid-cols-2">
                {claims.map((c) => (
                  <li key={c.title} className="border-t border-rule-strong pt-4">
                    <h3 className="m-0 text-lg leading-snug">{c.title}</h3>
                  </li>
                ))}
              </ul>
            </div>

            <div className="flex justify-center md:col-span-5 md:justify-end">
              <LoopFigure />
            </div>
          </div>
        </Reveal>
      </section>

      {/* ── the stack ────────────────────────────────────────── */}
      <section className={`border-b border-rule ${PAD} py-16`}>
        <Reveal>
          <Heading>the stack</Heading>
          <div className="grid gap-x-12 gap-y-8 md:grid-cols-12">
            <div className="md:col-span-5">
              <h2 className="mt-0 text-3xl">Dependencies point one way.</h2>
              <p className="mt-5 max-w-[42ch] text-ink-muted">
                An arrow means <em>this layer knows the other exists</em> — knowledge, not data.
                Nothing above Layer&nbsp;2 can reach in and change the loop.
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
                <p className="mt-4 max-w-[46ch] text-ink-muted">{p.detail}</p>
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
                className={`grid gap-x-8 gap-y-2 py-6 md:grid-cols-12 ${
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
                <p className="m-0 text-xl md:col-span-9">{t.headline}</p>
              </div>
            ))}
          </div>

          <div className="mt-12 grid gap-x-12 gap-y-6 border-t border-rule-strong pt-10 md:grid-cols-12">
            <h3 className="m-0 text-xl md:col-span-4">Next, in Tier 3</h3>
            <ul className="m-0 grid list-none gap-x-8 gap-y-3 p-0 md:col-span-8 md:grid-cols-2">
              {upcoming.map((u) => (
                <li key={u.name} className="text-ink-muted">
                  {u.name}
                </li>
              ))}
            </ul>
          </div>
        </Reveal>
      </section>
    </>
  );
}
