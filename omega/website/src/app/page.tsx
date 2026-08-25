import { CopyCommand, Reveal } from "@/components/site/interactive";
import { claims, commands, layers, providers, site, timeline } from "@/lib/content";

const PAD = "px-6 md:px-12";

function Heading({ children }: { children: React.ReactNode }) {
  return <p className="label m-0 mb-6 text-ink-muted">{children}</p>;
}

/**
 * The loop as a full-width band, not another split.
 *
 * Three earlier attempts all failed the same way: a circle, a railed card, then
 * the source itself — each one a two-column split with a panel on the right,
 * which is exactly the hero's shape. Four equal cells read left to right in one
 * pass, and repeat nothing.
 */
const STEPS = [
  { label: "Ask", detail: "the transcript, the tools, the standing instructions" },
  { label: "It asks back", detail: "read this file, run this command" },
  { label: "Do it", detail: "checked, budgeted, approved if it matters" },
  { label: "Report", detail: "worked or failed — both are just text" },
] as const;

/** src/ — the three packages, and what each is forbidden to know. */
const PARTS = [
  {
    role: "the brain",
    pkg: "omega_agent",
    line: "The loop and the harness. Has never heard of a file or a terminal.",
  },
  {
    role: "the environment",
    pkg: "omega_coding",
    line: "Tools, approvals, path confinement, sessions. Everything that touches your machine.",
  },
  {
    role: "the voice",
    pkg: "omega_ai",
    line: "Talks to models. Two adapters, one interface, and no opinions above it.",
  },
] as const;

function LoopBand() {
  return (
    <div className="mt-10">
      <ol className="m-0 grid list-none border border-rule bg-paper-raised p-0 md:grid-cols-4">
        {STEPS.map((s, i) => (
          <li
            key={s.label}
            className="border-b border-rule px-6 py-7 last:border-b-0 md:border-b-0 md:border-r md:last:border-r-0"
          >
            <span className="tnum label text-oxblood">{String(i + 1).padStart(2, "0")}</span>
            <h3 className="m-0 mt-3 text-xl">{s.label}</h3>
            <p className="m-0 mt-1.5 text-sm text-ink-muted">{s.detail}</p>
          </li>
        ))}
      </ol>

      <div className="flex flex-col gap-2 border-x border-b border-rule px-6 py-4 sm:flex-row sm:items-center sm:justify-between">
        <span className="flex items-baseline gap-2.5 text-sm text-ink-muted">
          <span aria-hidden="true" className="text-oxblood">
            &#8635;
          </span>
          Repeat for as long as it keeps asking.
        </span>
        <span className="flex items-baseline gap-2.5 text-sm">
          <span className="label text-forest">stop</span>
          <span className="text-ink-muted">it stops asking</span>
        </span>
      </div>
    </div>
  );
}

export default function Home() {
  return (
    <>
      {/* ── Hero ─── split ──────────────────────────────────── */}
      <section className={`relative overflow-hidden border-b border-rule ${PAD} py-16 md:py-20`}>
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

      {/* ── the loop ─── full-width band ─────────────────────── */}
      <section className={`border-b border-rule ${PAD} py-16`}>
        <Reveal>
          <Heading>the loop</Heading>
          <h2 className="m-0 max-w-[24ch] text-3xl md:text-[2.5rem] md:leading-[1.15]">
            Four steps, on repeat. That is the entire agent.
          </h2>
          <LoopBand />
        </Reveal>
      </section>

      {/* ── the boundary ─── three roles + a tree ────────────── */}
      <section className={`border-b border-rule ${PAD} py-16`}>
        <Reveal>
          <Heading>the boundary</Heading>
          <h2 className="m-0 max-w-[26ch] text-3xl md:text-[2.5rem] md:leading-[1.15]">
            Separate the brain, the environment, and the face.
          </h2>
          <p className="mt-5 max-w-[56ch] text-lg text-ink-muted">
            Each one is a package, and each is defined as much by what it is forbidden to know.
          </p>

          <div className="mt-10 grid gap-x-10 gap-y-8 md:grid-cols-3">
            {PARTS.map((p) => (
              <div key={p.pkg} className="border-t-2 border-oxblood pt-5">
                <h3 className="m-0 font-serif text-2xl">{p.role}</h3>
                <p className="m-0 mt-1 font-mono text-xs text-ink-muted">{p.pkg}</p>
                <p className="m-0 mt-4 text-ink-muted">{p.line}</p>
              </div>
            ))}
          </div>

          <div className="mt-10 overflow-x-auto border border-rule bg-term px-5 py-5">
            <pre className="m-0 font-mono text-[13px] leading-[1.9] text-ink">
              <code>
                {`src/
├── omega_ai/       `}
                <span className="text-ink-muted">the voice — providers, retry, streaming</span>
                {`
├── omega_agent/    `}
                <span className="text-ink-muted">the brain — the loop, the harness, the hooks</span>
                {`
└── omega_coding/   `}
                <span className="text-ink-muted">the environment and the face</span>
              </code>
            </pre>
          </div>
        </Reveal>
      </section>

      {/* ── what it bought ─── three cards ───────────────────── */}
      <section className={`border-b border-rule ${PAD} py-16`}>
        <Reveal>
          <Heading>what the layering bought</Heading>
          <ul className="m-0 grid list-none gap-x-10 gap-y-9 p-0 md:grid-cols-3">
            {claims.map((c, i) => (
              <li key={c.title} className="border-t border-rule-strong pt-5">
                <span className="tnum label text-ink-muted">{String(i + 1).padStart(2, "0")}</span>
                <h3 className="m-0 mt-3 text-xl leading-snug">{c.title}</h3>
                <p className="m-0 mt-3 text-sm text-ink-muted">{c.body}</p>
              </li>
            ))}
          </ul>
        </Reveal>
      </section>

      {/* ── the stack ─── split, as before ───────────────────── */}
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

      {/* ── two providers ─── two cards ──────────────────────── */}
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

      {/* ── where it is ─── stacked rows ─────────────────────── */}
      <section className={`border-b border-rule ${PAD} py-16`}>
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

      {/* ── the origin ─── credits ───────────────────────────── */}
      <section className={`${PAD} py-16 pb-20`}>
        <Reveal>
          <Heading>the origin</Heading>
          <h2 className="m-0 max-w-[26ch] text-3xl md:text-[2.5rem] md:leading-[1.15]">
            Inspired by Pi and Tau, written as a Python learning path.
          </h2>
          <p className="mt-6 max-w-[58ch] text-lg text-ink-muted">
            Pi is the exemplar and Tau is the Python mirror. Omega shares no code with either — it
            was read, then rebuilt from scratch, because the only way to understand a coding agent
            is to write one.
          </p>

          <div className="mt-10 grid gap-x-10 gap-y-8 sm:grid-cols-2">
            <a
              href="https://pi.dev"
              className="group cursor-pointer border-t-2 border-rule-strong pt-5 no-underline transition-colors duration-200 hover:border-oxblood"
            >
              <h3 className="m-0 font-serif text-2xl transition-colors duration-200 group-hover:text-oxblood">
                Pi
              </h3>
              <p className="m-0 mt-2 text-ink-muted">
                TypeScript. The exemplar — a minimal agent harness you adapt to your workflow.
              </p>
              <span className="label mt-3 inline-block text-ink-muted">pi.dev</span>
            </a>

            <a
              href="https://twotimespi.dev"
              className="group cursor-pointer border-t-2 border-rule-strong pt-5 no-underline transition-colors duration-200 hover:border-oxblood"
            >
              <h3 className="m-0 font-serif text-2xl transition-colors duration-200 group-hover:text-oxblood">
                Tau
              </h3>
              <p className="m-0 mt-2 text-ink-muted">
                Python. A coding agent small enough to read like a textbook, with the reasoning kept
                in the open.
              </p>
              <span className="label mt-3 inline-block text-ink-muted">twotimespi.dev</span>
            </a>
          </div>
        </Reveal>
      </section>
    </>
  );
}
