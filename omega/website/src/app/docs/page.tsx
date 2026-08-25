import type { Metadata } from "next";
import { Reveal } from "@/components/site/interactive";
import { site } from "@/lib/content";

export const metadata: Metadata = {
  title: "Docs — omega",
  description: "The reading order for omega's design notes, and what each one is for.",
};

const BLOB = `${site.repo}/blob/main`;

/**
 * The docs live in the repo as Markdown. Rather than duplicate them here and
 * let the copies drift, this page is the reading order — which is the part a
 * directory listing cannot tell you.
 */
const PATH = [
  {
    step: "Start",
    items: [
      {
        name: "How a coding agent works",
        file: "dev-notes/03-architecture/01-plain.md",
        note: "No jargon. The whole shape in fifteen minutes.",
      },
      {
        name: "The beginner architecture",
        file: "dev-notes/03-architecture/02-beginner.md",
        note: "Seventy lines that work, and the nine ways they break.",
      },
    ],
  },
  {
    step: "Then",
    items: [
      {
        name: "The production architecture",
        file: "dev-notes/03-architecture/03-production.md",
        note: "The same system with all nine fixed, and the vocabulary for each.",
      },
      {
        name: "Boundaries and layout",
        file: "dev-notes/03-architecture/04-boundaries-and-layout.md",
        note: "The stack diagram and the four boundaries, in plainer terms.",
      },
      {
        name: "Folder trees",
        file: "dev-notes/04-folder-trees.md",
        note: "How the architecture maps onto directories.",
      },
    ],
  },
  {
    step: "Build",
    items: [
      {
        name: "Tier 1 — the loop works",
        file: "omega/TIER-1.md",
        note: "What it has, what it lacks, and where Tier 2 puts each gap.",
      },
      {
        name: "Tier 2 — safe on a real repository",
        file: "omega/TIER-2.md",
        note: "Written as a contract before the code, kept honest afterwards.",
      },
    ],
  },
  {
    step: "Reference",
    items: [
      {
        name: "Anatomy",
        file: "dev-notes/00-concepts/anatomy.md",
        note: "Forty-two components, tiered. Read the summary table only.",
      },
      {
        name: "Security",
        file: "dev-notes/00-concepts/security.md",
        note: "Because it runs shell commands.",
      },
      {
        name: "Teardown",
        file: "dev-notes/01-teardown",
        note: "Six files, one per layer. Read one when you build that layer — not before.",
      },
      {
        name: "Glossary",
        file: "dev-notes/04-glossary.md",
        note: "Look terms up as you hit them.",
      },
    ],
  },
] as const;

export default function DocsPage() {
  return (
    <section className="px-6 py-16 md:px-12 md:py-20">
      <Reveal>
        <p className="label m-0 mb-6 text-ink-muted">docs</p>
        <h1 className="m-0 max-w-[20ch] text-4xl leading-[1.1] md:text-5xl">
          Read them in this order.
        </h1>
        <p className="mt-6 max-w-[54ch] text-lg text-ink-muted">
          The notes live in the repository as Markdown, so they cannot drift from the code. What a
          file listing cannot tell you is the order — that is what this page is for.
        </p>
      </Reveal>

      <div className="mt-16 grid gap-x-12 gap-y-14">
        {PATH.map((group, gi) => (
          <Reveal key={group.step} delay={gi * 60}>
            <div className="grid gap-x-12 gap-y-6 border-t border-rule-strong pt-7 md:grid-cols-12">
              <h2 className="label m-0 text-oxblood md:col-span-3">{group.step}</h2>
              <ul className="m-0 grid list-none gap-6 p-0 md:col-span-9">
                {group.items.map((item) => (
                  <li key={item.file}>
                    <a
                      href={`${BLOB}/${item.file}`}
                      className="group inline-block cursor-pointer no-underline"
                    >
                      <h3 className="m-0 text-xl transition-colors duration-200 group-hover:text-oxblood">
                        {item.name}
                        <span
                          aria-hidden="true"
                          className="ml-1.5 align-[0.15em] text-[0.6em] text-ink-muted transition-colors duration-200 group-hover:text-oxblood"
                        >
                          &#8599;
                        </span>
                      </h3>
                    </a>
                    <p className="m-0 mt-1 max-w-[58ch] text-ink-muted">{item.note}</p>
                    <p className="m-0 mt-1 font-mono text-xs text-ink-muted/70">{item.file}</p>
                  </li>
                ))}
              </ul>
            </div>
          </Reveal>
        ))}
      </div>
    </section>
  );
}
