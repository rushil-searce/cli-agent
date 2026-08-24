"""How full is the context window — anatomy.md #22.

This **measures** beginner failure #1; it does not fix it. Compaction is Tier 3.
What this buys now is the ability to watch the wall approach instead of hitting
it, which is also what makes the Tier 3 work possible to tune.

**A cheap estimate, not a token count.** `anatomy.md:282` is explicit that exact
counts are not the goal: "You don't need exact counts, just a cheap estimate
that never wildly under-reports." Characters divided by four is that estimate.
Calling a real tokenizer would mean a dependency, per-model vocabularies, and
milliseconds on every turn, to improve a number that only ever drives a
threshold.

The part people forget is **tool schemas**. They are re-sent on every single
request and they are not small — four tools with descriptions and JSON Schema is
easily a thousand tokens of every turn. An estimator that measures only messages
will under-report by a constant, which is the one direction that matters.
"""

from __future__ import annotations

import json
from dataclasses import dataclass

from omega.tools import Tool
from omega.types import AgentMessage, AssistantMessage, ToolResultMessage, UserMessage

#: The classic rule of thumb for English and code. Wrong in both directions for
#: any given string, close enough over a whole conversation.
CHARS_PER_TOKEN = 4

#: Used when a model is not in the table below. Deliberately the *smaller*
#: common window: over-reporting how full you are is safe, under-reporting is not.
DEFAULT_CONTEXT_WINDOW = 200_000

#: Matched as a prefix, so `claude-opus-5[1m]` and dated variants resolve without
#: an entry each.
MODEL_WINDOWS: dict[str, int] = {
    "claude-opus-5[1m]": 1_000_000,
    "claude-sonnet-5[1m]": 1_000_000,
}


def window_for(model: str) -> int:
    """The context window for a model, or a conservative default."""
    for prefix, window in MODEL_WINDOWS.items():
        if model.startswith(prefix):
            return window
    return DEFAULT_CONTEXT_WINDOW


def estimate_tokens(text: str) -> int:
    return len(text) // CHARS_PER_TOKEN


def _message_text(message: AgentMessage) -> str:
    """Everything in a message that costs tokens.

    Tool call *arguments* are included: a call carrying a whole file's contents
    as a `content` argument is expensive, and it is exactly the kind of message
    that fills a window.
    """
    if isinstance(message, UserMessage):
        return message.content
    if isinstance(message, ToolResultMessage):
        return message.text
    if isinstance(message, AssistantMessage):
        parts = [message.text]
        parts.extend(json.dumps(call.arguments) for call in message.tool_calls)
        return "\n".join(parts)
    return ""


def estimate_request_tokens(
    *, system: str, messages: list[AgentMessage], tools: list[Tool]
) -> int:
    """What the next request will roughly cost, schemas included."""
    total = estimate_tokens(system)
    total += sum(estimate_tokens(_message_text(message)) for message in messages)
    for tool in tools:
        total += estimate_tokens(tool.name)
        total += estimate_tokens(tool.description)
        total += estimate_tokens(json.dumps(tool.parameters))
    return total


@dataclass(frozen=True, slots=True)
class ContextUsage:
    """A reading, ready to render."""

    estimated_tokens: int
    window: int

    @property
    def fraction(self) -> float:
        if self.window <= 0:
            return 0.0
        return self.estimated_tokens / self.window

    @property
    def percent(self) -> int:
        return int(self.fraction * 100)

    def __str__(self) -> str:
        return f"~{self.estimated_tokens:,}/{self.window:,} tokens ({self.percent}%)"


def measure(
    *, model: str, system: str, messages: list[AgentMessage], tools: list[Tool]
) -> ContextUsage:
    return ContextUsage(
        estimated_tokens=estimate_request_tokens(
            system=system, messages=messages, tools=tools
        ),
        window=window_for(model),
    )
