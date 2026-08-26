/**
 * Single source of truth for everything the page claims.
 *
 * Every number here is measured and every quote is attributable. Figures come
 * from omega/TIER-1.md and omega/TIER-2.md; commands come from omega/README.md.
 * If a claim is not in one of those files, it does not appear on the site.
 */

export const site = {
  name: "omega",
  eyebrow: "A terminal coding agent",
  /** The argument, not the description. Both numbers are measured. */
  headline: "The loop is 190 lines.",
  headlineRest: "Everything else grew around it.",
  tagline: "A terminal coding agent, built from scratch in layers.",
  /**
   * Name-first, so a first-time visitor learns what omega *is* before
   * anything else on the page. Condensed from `thesis` below
   * (dev-notes/03-architecture/01-plain.md); the loop figure is the measured
   * one from TIER-2.md. Nothing here is a claim those files do not make.
   */
  definition:
    "is a Python coding agent small enough to read end to end. It asks a model for help, runs what it asks for, reports back, and repeats — until it says it is finished.",
  repo: "https://github.com/rushil-searce/cli-agent",
  x: "https://x.com/rushil_jariwala",
} as const;

/** dev-notes/03-architecture/01-plain.md — the one-sentence version. */
export const thesis =
  "A coding agent is a program that asks a model for help, does what the model asks for, tells it what happened, and repeats until it says it is finished.";

/** README.md, lines 23-26. */
export const commands = [
  { cmd: "uv run omega --fake", note: "scripted responses — no key, no network, no credits" },
  { cmd: "uv run omega", note: "Anthropic Messages" },
  { cmd: "uv run omega --provider openai", note: "OpenAI Chat Completions" },
  { cmd: "uv run omega --resume", note: "continue the most recent session here" },
] as const;

/** 03-production.md §1, 04-boundaries-and-layout.md §2. */
export const layers = [
  {
    n: 4,
    name: "Terminal UI",
    detail: "Print output today. The 10 agent events are already the contract a real TUI would use.",
    state: "partial",
  },
  {
    n: 3,
    name: "Coding app",
    detail: "Tools, approvals, path confinement, secret redaction, sessions.",
    state: "built",
  },
  {
    n: 2,
    name: "Agent core",
    detail: "The loop, the harness, the hook bundle, the between-turns queues.",
    state: "built",
  },
  {
    n: 1,
    name: "Provider",
    detail: "One interface, 12 stream events, retry swallowed below the boundary.",
    state: "built",
  },
] as const;

/** TIER-2.md, the comparison table at lines 14-19. */
export const measured = [
  { label: "Source lines", tier1: "1,577", tier2: "4,654" },
  { label: "Test lines", tier1: "499", tier2: "4,257" },
  { label: "Tests", tier1: "45", tier2: "289" },
  { label: "loop.py", tier1: "151", tier2: "190" },
] as const;

export const providers = [
  {
    name: "Anthropic Messages",
    file: "providers/anthropic.py",
    detail:
      "Content blocks, thinking blocks with signatures that must return verbatim, and tool-use ids that must be answered exactly once.",
  },
  {
    name: "OpenAI Chat Completions",
    file: "providers/openai.py",
    detail:
      "Not a feature — the exam. A genuinely different wire format, and the same adapter reaches Groq, Together, Ollama and vLLM. The format is the unit, not the vendor.",
  },
] as const;

/** TIER-1.md and TIER-2.md — "The one-line summary" of each. */
export const timeline = [
  {
    tier: "Tier 1",
    status: "closed" as const,
    headline: "A working agent with real layers.",
    body: "It streams, it calls tools, it stops correctly, and its provider is swappable. Not safe, not persistent, not interruptible — and each of those is a Tier 2 addition to a seam that already existed, not a rewrite.",
  },
  {
    tier: "Tier 2",
    status: "closed" as const,
    headline: "Safe to point at a real repository.",
    body: "It can be interrupted without corruption, it remembers, it asks before it destroys, and the provider abstraction is no longer a claim but a measured result.",
  },
  {
    tier: "Tier 3",
    status: "next" as const,
    headline: "Survives a task long enough to fill the context window.",
    body: "That is the whole of Tier 3 — and the two beginner failures still standing are the two it fixes.",
  },
] as const;

/** TIER-2.md Part 2 — "Things Tier 3 adds next". Each seam already exists. */
export const upcoming = [
  { name: "Session branching", seam: "parent_id is already on every entry" },
  { name: "Search tools", seam: "truncate_output() and paths.py both exist" },
  { name: "A real TUI", seam: "the 10 agent events are the UI contract" },
  { name: "Structured logging", seam: "a second listener on the same event stream" },
  { name: "Image reading", seam: "content blocks are a discriminated union" },
  { name: "Subagents or plan mode", seam: "a subagent is the headless driver, called from a tool" },
] as const;

/** What the layering bought, stated as claims rather than adjectives. */
export const claims = [
  {
    title: "Adding OpenAI changed nothing above Layer 1",
    body: "Not a feature — the exam. Chat Completions is a genuinely different wire format, and the provider interface did not move. If it had, Tier 1 was wrong.",
  },
  {
    title: "The loop holds at 190 lines",
    body: "It hit 249 while the between-turns queues went in. Rather than let it grow, tool dispatch was extracted to its own file. The tripwire fired and did its job.",
  },
  {
    title: "289 tests, none touching the network",
    body: "Every provider call is faked at the interface boundary, which is why providers/fake.py was written before the real adapter. The suite runs in 1.7 seconds with no key.",
  },
] as const;
