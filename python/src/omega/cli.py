"""A print-based REPL.

Deliberately **not** a terminal UI. At Tier 2 a TUI would still hide more than it
shows; plain `print` keeps every event visible. A real UI arrives at Tier 3, and
it will subscribe to exactly the events this file already reads — that is the
test of whether the vocabulary was designed for a renderer or for a printer.

`--fake` runs the whole agent against scripted responses — no key, no network,
no credits. It exercises the same loop, the same tools, and the same streaming
path as the real thing.
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from omega.builtin_tools import DEFAULT_TOOLS
from omega.harness import Harness
from omega.loop import DEFAULT_MAX_TURNS
from omega.provider import ModelProvider
from omega.providers.anthropic import DEFAULT_MODEL, AnthropicProvider
from omega.providers.fake import FakeProvider, text_turn, tool_turn

SYSTEM_PROMPT = """You are omega, a terminal coding agent. Use the tools to inspect and edit files.

When asked to perform a coding task:
1. Inspect the codebase before changing it.
2. Make the change with write_file, or run commands with run_shell.
3. Verify your work before reporting that you are done."""

_ARG_PREVIEW = 80
_RESULT_PREVIEW = 100


def _fake_provider() -> FakeProvider:
    """A canned two-turn scenario, repeated for each prompt.

    Shows the whole path: a tool call, a real tool execution, and a final answer.
    """
    scenario = [
        tool_turn(
            "run_shell",
            {"command": "echo 'hello from omega'"},
            text="Let me check something first.",
        ),
        text_turn("That worked — the shell tool ran and returned its output."),
    ]
    return FakeProvider([scenario[i % 2] for i in range(40)])


def _clip(text: str, limit: int) -> str:
    return text if len(text) <= limit else text[: limit - 3] + "..."


async def _run_turn(harness: Harness, prompt: str) -> None:
    """One user prompt, run to completion, printed as it happens.

    Worth comparing against the Tier 1 version. That one had to watch the
    transcript list grow to notice tool results, because no event described them,
    and it tracked a `streaming_text` flag by hand to know when to emit a
    newline. Both of those were symptoms of reading a vocabulary built for the
    layer below. Every branch here is driven by an event that means what it says.
    """
    async for event in harness.run(prompt):
        if event.type == "message_update":
            # The twelve still travel; this is where they arrive.
            raw = event.stream_event
            if raw.type == "text_delta":
                print(raw.delta, end="", flush=True)
            elif raw.type == "text_end":
                print()

        elif event.type == "tool_execution_start":
            call = event.tool_call
            print(f"  → {call.name}({_clip(str(call.arguments), _ARG_PREVIEW)})")

        elif event.type == "tool_execution_end":
            result = event.result
            marker = "x" if result.is_error else "<"
            first_line = result.text.splitlines()[0] if result.text else ""
            print(f"  {marker} {_clip(first_line, _RESULT_PREVIEW)}")

        elif event.type == "agent_end" and event.reason != "stop":
            # `stop` is the only success. The other three all mean "unfinished",
            # and a user should be told which one it was.
            print(f"\n[{event.reason}] {event.error_message or ''}", file=sys.stderr)


def main() -> None:
    parser = argparse.ArgumentParser(prog="omega", description="A terminal coding agent (Tier 2).")
    parser.add_argument(
        "--fake",
        action="store_true",
        help="Use scripted responses instead of a real provider. No API key needed.",
    )
    parser.add_argument("--model", default=DEFAULT_MODEL, help="Model id.")
    parser.add_argument(
        "--max-turns", type=int, default=DEFAULT_MAX_TURNS, help="Loop iteration cap."
    )
    args = parser.parse_args()

    provider: ModelProvider
    if args.fake:
        provider = _fake_provider()
        print("omega (fake provider - scripted responses, nothing is sent anywhere)")
    else:
        # .env lives at the repo root, one level above this package.
        load_dotenv(Path(__file__).resolve().parents[3] / ".env", override=True)
        if not os.environ.get("ANTHROPIC_API_KEY"):
            sys.exit(
                "ANTHROPIC_API_KEY not set - add it to .env (see .env.sample), "
                "or run `omega --fake` to try omega without a key."
            )
        provider = AnthropicProvider()
        print(f"omega ({args.model})")

    print("Type 'exit' to quit.\n")

    # One harness for the whole session: it owns the transcript, so successive
    # prompts are a conversation rather than a series of unrelated questions.
    harness = Harness(
        provider=provider,
        model=args.model,
        system=SYSTEM_PROMPT,
        tools=DEFAULT_TOOLS,
        max_turns=args.max_turns,
    )

    while True:
        try:
            prompt = input("You: ")
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if prompt.strip().lower() in {"exit", "quit"}:
            break
        if not prompt.strip():
            continue

        try:
            asyncio.run(_run_turn(harness, prompt))
        except KeyboardInterrupt:
            # Still true at Step 1: nothing creates a cancellation token yet, so
            # an interrupt ends the turn abruptly and may leave a tool call
            # unanswered. Step 2 fixes this properly; until then, say so rather
            # than pretending.
            print(
                "\n[interrupted - the transcript may now contain an unanswered "
                "tool call; restart if the next turn fails]",
                file=sys.stderr,
            )
        print()


if __name__ == "__main__":
    main()
