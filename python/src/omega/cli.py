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
import signal
import sys
from collections.abc import Callable
from pathlib import Path

from dotenv import load_dotenv

from omega.agent_events import AgentEvent
from omega.builtin_tools import build_tools
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
    interrupt = _install_interrupt_handler(harness)

    try:
        async for event in harness.run(prompt):
            _render(event)
    finally:
        interrupt()


def _install_interrupt_handler(harness: Harness) -> Callable[[], None]:
    """Point SIGINT at the harness for the duration of a turn.

    Tier 1 let Ctrl-C kill the process. That was not just abrupt — it could
    leave a tool call unanswered, which makes the transcript **permanently**
    invalid. Now the interrupt cancels the turn, the turn ends properly, and the
    next prompt heals whatever was half-finished.

    Returns the function that removes the handler again, so the default
    behaviour is back in place while sitting at the prompt: a Ctrl-C there
    should quit, not be swallowed.
    """
    try:
        loop = asyncio.get_running_loop()
        loop.add_signal_handler(signal.SIGINT, harness.cancel)
    except NotImplementedError:
        # add_signal_handler is Unix-only. Elsewhere the KeyboardInterrupt path
        # in main() is the fallback, which is abrupt but at least says so.
        return lambda: None

    def restore() -> None:
        loop.remove_signal_handler(signal.SIGINT)

    return restore


def _render(event: AgentEvent) -> None:
    """Print one agent event.

    A separate function from the loop that drives it, because this is exactly
    what a Tier 3 TUI replaces: same events in, widgets out instead of lines.
    Keeping it standalone means that swap touches one function.
    """
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

    elif event.type == "agent_end" and event.reason == "aborted":
        # Not a failure - the user asked for it. Said plainly, because a
        # stack-trace-shaped message for "I pressed Ctrl-C" is noise.
        print("\n[cancelled]", file=sys.stderr)

    elif event.type == "agent_end" and event.reason != "stop":
        # `stop` is the only success. The rest mean "unfinished", and a user
        # should be told which one it was.
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
        # Rooted at the directory omega was started in: that is the fence.
        tools=build_tools(Path.cwd()),
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
            # Only reachable where add_signal_handler is unavailable. The
            # transcript may now hold an unanswered tool call - the next run()
            # repairs it before sending anything, so this is a report, not a
            # warning to act on.
            print("\n[interrupted]", file=sys.stderr)
        print()


if __name__ == "__main__":
    main()
