"""The seams — how the coding app installs policy into the loop.

This file is why `loop.py` does not have to grow. It is the boundary that felt
backwards in `docs/03-architecture/04-boundaries-and-layout.md` §3, Boundary B:
Layer 3 hands Layer 2 a bundle of functions once, at startup, and the loop calls
them later at the right moments.

> **The loop asks, never decides.**

Every one of these is a *decision* — may I run this? what should be sent? — and
decisions belong to the caller. The mechanism (ask model, run tools, repeat) is
all that stays in the loop. Pi's 880-line compaction subsystem plugs into
exactly one of these callbacks, and its loop contains zero lines of compaction.

Pi has nine hooks and Tau six. Tier 2 fills these:

| Hook | When | What fills it |
|---|---|---|
| `before_tool_call` | before running a tool | approvals — Step 4 |
| `after_tool_call` | after a tool returns | secret redaction — Step 4 |
| `convert_to_llm` | before every request | drop UI-only messages |
| `transform_context` | before every request | **compaction, at Tier 3** |
| `get_steering_messages` | between turns | text typed while it worked |
| `get_follow_up_messages` | between turns | the next queued task |

**`get_api_key` is deliberately not here.** Pi makes it a loop hook; omega makes
it a resolver passed to the provider instead, because the loop has no business
knowing that credentials exist. Same capability — a token can still refresh
mid-session — one layer lower, where auth belongs.

The two remaining Pi hooks, `should_stop_after_turn` and `prepare_next_turn`,
are not needed yet. Adding them is adding a field to this dataclass.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from omega.tools import ToolResult
from omega.types import AgentMessage, ToolCall


@dataclass(frozen=True, slots=True)
class ToolCallDecision:
    """The gate's answer. A denial must carry a reason.

    The reason is not decoration: it becomes the tool result the model reads, so
    "denied by policy: writes outside the project are refused" lets the model
    adapt, where a bare refusal makes it retry the same thing.
    """

    allowed: bool
    reason: str | None = None


#: The permissive answer, so a caller that only blocks some calls can return a
#: shared constant for the rest.
ALLOW = ToolCallDecision(allowed=True)


#: Consulted before a tool runs. Denying it still produces a tool result — an
#: unanswered tool call is a permanent API error, so refusal cannot be silence.
BeforeToolCall = Callable[[ToolCall], Awaitable[ToolCallDecision]]

#: Consulted after a tool returns, and may rewrite the result. Truncation and
#: redaction live here: the model reads the returned value, not the original.
AfterToolCall = Callable[[ToolCall, ToolResult], Awaitable[ToolResult]]

#: Rewrites the conversation on its way to the provider. Takes what the harness
#: holds, returns what gets sent — **the harness's own transcript is untouched.**
#: That is the "two views of history" split, and it is what stops a failed turn
#: from poisoning later requests.
ContextTransform = Callable[[list[AgentMessage]], Awaitable[list[AgentMessage]]]

#: Supplies messages between turns. Returning an empty list means "nothing to add".
MessageSource = Callable[[], Awaitable[list[AgentMessage]]]


@dataclass(frozen=True, slots=True)
class AgentHooks:
    """The bundle. Every field optional; the empty bundle changes nothing.

    Frozen, because the loop reads these while running and a hook set that could
    change mid-turn would make behaviour depend on timing.
    """

    before_tool_call: BeforeToolCall | None = None
    after_tool_call: AfterToolCall | None = None
    # convert_to_llm runs first, then transform_context: normalise, then compact.
    # Order recorded here because nothing in the type system enforces it.
    convert_to_llm: ContextTransform | None = None
    transform_context: ContextTransform | None = None
    get_steering_messages: MessageSource | None = None
    get_follow_up_messages: MessageSource | None = None
