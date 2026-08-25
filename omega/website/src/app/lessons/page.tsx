import type { Metadata } from "next";
import { Reveal } from "@/components/site/interactive";

export const metadata: Metadata = {
  title: "Lessons — omega",
  description: "What building omega in tiers actually taught, one note per thing.",
};

/**
 * Tau's dev-notes are the model: one short note per thing learned, written
 * after it happened, kept honest. Every figure here is measured — the sources
 * are TIER-1.md and TIER-2.md.
 */
const LESSONS = [
  {
    title: "Every estimate ran low. Three times.",
    body: "Tier 1 was predicted at ~700 lines and came in at 1,577. Tier 2 predicted 3,400–3,800 and came in at 4,654. The direction never varied, so it stopped being noise and became a correction factor: assume any estimate in these notes is 1.3–2× low.",
  },
  {
    title: "The tripwire fired, and it was right.",
    body: "The rule was that loop.py must not pass ~250 lines. Adding the between-turns queues took it to 249. Rather than raise the limit, tool dispatch moved to its own file and the loop came back to 190. The rule did not block the feature — it identified which part of the file had stopped being the loop.",
  },
  {
    title: "Tests grew almost three times faster than source.",
    body: "Source ×3.0, tests ×8.5. Most of the difference is adversarial: symlinked parents, `..` smuggled back through a rebuilt path, indented secrets, a failure arriving after output. Each is three lines of fix behind twenty lines of test proving the fix matters.",
  },
  {
    title: "The second provider was the exam, not a feature.",
    body: "Chat Completions is a genuinely different wire format. Adding it changed no file above Layer 1. That is the only real evidence the abstraction was worth having — before that it was a claim.",
  },
  {
    title: "An unanswered tool call is permanent.",
    body: "Interrupt while a tool runs and the transcript holds a request with no reply. Providers reject that conversation outright, every time, forever. It costs nothing while sessions live in memory and becomes data corruption the day you persist them — which is why cancellation and persistence had to ship in the same tier.",
  },
  {
    title: "Write the fake before the real adapter.",
    body: "A fake provider is not a testing convenience, it is a design check. If it is hard to write, the interface is too big. Writing it first is also why the whole suite runs offline — 289 tests, no key, no network, 1.7 seconds.",
  },
] as const;

export default function LessonsPage() {
  return (
    <section className="px-6 py-16 md:px-12 md:py-20">
      <Reveal>
        <p className="label m-0 mb-6 text-ink-muted">lessons</p>
        <h1 className="m-0 max-w-[18ch] text-4xl leading-[1.1] md:text-5xl">
          What it actually taught.
        </h1>
        <p className="mt-6 max-w-[54ch] text-lg text-ink-muted">
          Written after the fact, kept honest. Where a number appears it was measured — including
          the ones that made the plan look wrong.
        </p>
      </Reveal>

      <ol className="m-0 mt-16 grid list-none gap-0 p-0">
        {LESSONS.map((lesson, i) => (
          <Reveal key={lesson.title} delay={i * 50}>
            <li className="grid gap-x-12 gap-y-3 border-t border-rule py-8 md:grid-cols-12">
              <span className="tnum label m-0 text-oxblood md:col-span-2">
                {String(i + 1).padStart(2, "0")}
              </span>
              <h2 className="m-0 max-w-[22ch] text-2xl leading-snug md:col-span-4">
                {lesson.title}
              </h2>
              <p className="m-0 max-w-[58ch] text-ink-muted md:col-span-6">{lesson.body}</p>
            </li>
          </Reveal>
        ))}
      </ol>
    </section>
  );
}
