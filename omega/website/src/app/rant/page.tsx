import type { Metadata } from "next";
import { Reveal } from "@/components/site/interactive";

export const metadata: Metadata = {
  title: "Rant — omega",
  description: "Why omega exists, and what building one from scratch is actually for.",
};

/**
 * Draft voice. The arguments come from the project's own design notes — the
 * tier contracts, the nine failures, the layering rules. Rewrite it in your
 * own words; none of this should stay in mine.
 */
const SECTIONS = [
  {
    heading: "You cannot learn from a binary.",
    body: [
      "Coding agents went from novelty to daily tool in about a year, and almost all of them are closed. You can watch one work. You cannot watch it decide. The interesting part — what happens between your prompt and the diff — is exactly the part nobody ships.",
      "So the only way to understand it is to build one. Not a demo. One that runs shell commands on a real repository and has to be safe about it.",
    ],
  },
  {
    heading: "The loop is easy. Everything else is the work.",
    body: [
      "Ask a model, run what it asks for, report back, repeat. Seventy lines and it genuinely works. That version is worth writing and then worth throwing away, because the moment you point it at something real it fails in nine specific ways — context fills, output floods, Ctrl-C corrupts the transcript, a rate limit kills twenty turns of progress.",
      "Not one of those fixes belongs in the loop. That is the whole architectural argument, and you only believe it after you have felt the failures yourself.",
    ],
  },
  {
    heading: "Write the contract before the code.",
    body: [
      "Each tier was specified before it was built — what would have to be true when it closed — so the work could be checked against a commitment instead of described after the fact. The file was then updated in place wherever reality disagreed with the plan.",
      "That is why the notes still record the estimates that were wrong. Three times running they were 1.3–2× low. A document that only remembers its correct predictions is marketing.",
    ],
  },
  {
    heading: "Small is a constraint, not a virtue.",
    body: [
      "loop.py must not pass 250 lines. It hit 249, and the response was not to raise the limit — it was to notice that tool dispatch had stopped being the loop, and move it out.",
      "A rule you are willing to enforce against your own convenience is worth having. One you quietly relax is decoration.",
    ],
  },
] as const;

export default function RantPage() {
  return (
    <section className="px-6 py-16 md:px-12 md:py-20">
      <Reveal>
        <p className="label m-0 mb-6 text-ink-muted">rant</p>
        <h1 className="m-0 max-w-[16ch] text-4xl leading-[1.1] md:text-5xl">
          Why build one at all?
        </h1>
        <p className="mt-6 max-w-[52ch] text-lg text-ink-muted">
          There are better agents than this one. That was never the point.
        </p>
      </Reveal>

      <div className="mt-16 grid gap-14">
        {SECTIONS.map((s, i) => (
          <Reveal key={s.heading} delay={i * 60}>
            <article className="grid gap-x-12 gap-y-4 border-t border-rule-strong pt-7 md:grid-cols-12">
              <h2 className="m-0 max-w-[20ch] text-2xl leading-snug md:col-span-5">{s.heading}</h2>
              <div className="grid gap-4 md:col-span-7">
                {s.body.map((p) => (
                  <p key={p.slice(0, 24)} className="m-0 max-w-[62ch] text-ink-muted">
                    {p}
                  </p>
                ))}
              </div>
            </article>
          </Reveal>
        ))}
      </div>
    </section>
  );
}
