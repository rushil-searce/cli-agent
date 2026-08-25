import { CopyCommand, Reveal } from "@/components/site/interactive";
import { claims, commands, layers, providers, site, timeline } from "@/lib/content";

const PAD = "px-6 md:px-12";

function Heading({ children }: { children: React.ReactNode }) {
  return <p className="label m-0 mb-6 text-ink-muted">{children}</p>;
}

/**
 * The loop, shown as the loop.
 *
 * Two earlier attempts drew it — a circle with mis-plotted stations, then a
 * railed card whose border and arrow read as vague. Both were illustrations of
 * something that is already legible in eight lines. The subject of this section
 * is that the mechanism is small; the most direct way to show that is the
 * mechanism.
 *
 * Condensed from omega_agent/loop.py — real lines, inner detail elided.
 */
const LOOP_SOURCE: { text: string; tone?: "kw" | "dim" | "stop" }[][] = [
  [{ text: "for", tone: "kw" }, { text: " turn " }, { text: "in", tone: "kw" }, { text: " range(max_turns):" }],
  [{ text: "    assistant = " }, { text: "await", tone: "kw" }, { text: " stream(provider, messages, tools)" }],
  [],
  [{ text: "    calls = assistant.tool_calls" }],
  [{ text: "    # content, not stop_reason", tone: "dim" }],
  [],
  [{ text: "    " }, { text: "if not", tone: "kw" }, { text: " calls:" }],
  [{ text: "        " }, { text: "return", tone: "stop" }, { text: "  # the run is over", tone: "dim" }],
  [],
  [{ text: "    " }, { text: "for", tone: "kw" }, { text: " call " }, { text: "in", tone: "kw" }, { text: " calls:" }],
  [{ text: "        messages.append(" }, { text: "await", tone: "kw" }, { text: " run_tool(call))" }],
];

const TONE = {
  kw: "text-oxblood",
  dim: "text-ink-muted",
  stop: "text-forest",
} as const;

function LoopSource() {
  return (
    <figure className="m-0 w-full border border-rule bg-term">
      <figcaption className="flex items-baseline justify-between border-b border-rule px-5 py-3">
        <span className="label text-ink-muted">omega_agent/loop.py</span>
        <span className="label text-ink-muted">190 lines</span>
      </figcaption>
      <pre className="m-0 overflow-x-auto px-5 py-5 font-mono text-[13px] leading-[1.85]">
        <code>
          {LOOP_SOURCE.map((line, i) => (
            <span key={i} className="block min-h-[1.85em]">
              {line.map((part, j) => (
                <span key={j} className={part.tone ? TONE[part.tone] : undefined}>
                  {part.text}
                </span>
              ))}
            </span>
          ))}
        </code>
      </pre>
    </figure>
  );
}

export default function Home() {
  return (
    <>
      {/* ── Hero ─────────────────────────────────────────────── */}
      <section className={`relative overflow-hidden border-b border-rule ${PAD} py-16 md:py-20`}>
        {/* Graph paper across the whole hero, easing off only at the very end. */}
        <div
          aria-hidden="true"
          className="pointer-events-none absolute inset-0 [mask-image:linear-gradient(to_bottom,black_0%,black_72%,transparent_100%)]"
          style={{
            backgroundImage:
              "linear-gradient(to right, var(--rule) 1px, transparent 1px), linear-gradient(to bottom, var(--rule) 1px, transparent 1px)",
            backgroundSize: "64px 64px",
          }}
        />

        <Reveal className="relative">
          <div className="grid items-center gap-x-12 gap-y-12 md:grid-cols-12">
            <div className="md:col-span-6">
              <div className="mb-7 flex items-baseline gap-3">
                <span className="font-serif text-4xl leading-none text-oxblood">&#937;</span>
                <span className="label text-ink">omega</span>
              </div>

              <h1 className="m-0 max-w-[16ch] text-4xl font-normal leading-[1.08] md:text-[3.25rem]">
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
            <div className="md:col-span-5">
              <h2 className="m-0 max-w-[16ch] text-3xl">
                Ask, run what it asks for, report back, repeat.
              </h2>
              <p className="mt-5 max-w-[38ch] text-ink-muted">
                The loop asks. It never decides — every policy is somebody else&rsquo;s callback.
              </p>

              <ul className="m-0 mt-9 grid list-none gap-0 p-0">
                {claims.map((c) => (
                  <li
                    key={c.title}
                    className="border-t border-rule py-3.5 text-[15px] leading-snug last:border-b"
                  >
                    {c.title}
                  </li>
                ))}
              </ul>
            </div>

            <div className="md:col-span-7">
              <LoopSource />
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
          <a
            href="/roadmap"
            className="label mt-8 inline-block cursor-pointer border-b border-rule-strong pb-0.5 text-ink transition-colors duration-200 hover:border-oxblood hover:text-oxblood"
          >
            The full roadmap
          </a>
        </Reveal>
      </section>
    </>
  );
}
