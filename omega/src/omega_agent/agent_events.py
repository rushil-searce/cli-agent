"""The ten agent events — Layer 2's vocabulary.

Tier 1 had one event vocabulary and the loop handed it straight upward. That was
honest for a tier whose only consumer was a `print` statement, but it has a cost
the CLI made visible: **tool results had no event at all.** `cli.py` reported them
by watching the transcript list grow, after the fact.

So there are two vocabularies, and the split is the point:

| | the **12** (`events.py`) | the **10** (this file) |
|---|---|---|
| about | one model response arriving | the whole run's progress |
| granularity | one token | "a tool started" |
| audience | Layer 2 | Layer 4 — a UI |

They nest four deep: **agent ▸ turn ▸ message ▸ tool execution.** A renderer can
indent on that structure without tracking any state of its own.

Nothing is lost by moving up a level. Every one of the twelve is carried by
exactly one of these ten, on the `stream_event` field of the three `message_*`
events — so a consumer that wants token deltas still gets them, and a consumer
that only wants "what is happening" can ignore them.

Pi and Tau converged on these ten names, as they did on the twelve. Copied
verbatim rather than improved.
"""

from __future__ import annotations

from typing import Annotated, Any, Literal

from pydantic import Field

from omega_agent.events import AssistantMessageEvent
from omega_agent.types import AssistantMessage, ToolCall, ToolResultMessage, WireModel

#: The four nesting levels, outermost first. Exposed so a renderer can derive
#: indentation from the vocabulary instead of hardcoding it.
AGENT_EVENT_NESTING = ("agent", "turn", "message", "tool_execution")

#: Why a run ended. `stop` is the only success: the model stopped asking for
#: tools. The other three are all "it did not finish", distinguished because a
#: UI should say which.
AgentEndReason = Literal["stop", "max_turns", "error", "aborted"]


# ----------------------------------------------------------------- agent scope

class AgentStartEvent(WireModel):
    """The run begins. Carries nothing — the loop's inputs are the caller's."""

    type: Literal["agent_start"] = "agent_start"


class AgentEndEvent(WireModel):
    """The run is over, for any reason.

    Exactly one of these is emitted per run, including on failure. Tier 1
    signalled failure by yielding a bare provider `error` event, which meant a
    consumer had to distinguish "this turn failed" from "the run is over".
    """

    type: Literal["agent_end"] = "agent_end"
    reason: AgentEndReason
    error_message: str | None = None


# ------------------------------------------------------------------ turn scope

class TurnStartEvent(WireModel):
    type: Literal["turn_start"] = "turn_start"
    turn: int


class TurnEndEvent(WireModel):
    type: Literal["turn_end"] = "turn_end"
    turn: int


# --------------------------------------------------------------- message scope

# All three carry `stream_event`, the underlying one of the twelve. That is what
# keeps the coarser vocabulary from being a downgrade: a renderer wanting text
# deltas reads `stream_event`, one wanting progress ignores it.

class MessageStartEvent(WireModel):
    type: Literal["message_start"] = "message_start"
    message: AssistantMessage
    stream_event: AssistantMessageEvent


class MessageUpdateEvent(WireModel):
    type: Literal["message_update"] = "message_update"
    message: AssistantMessage
    stream_event: AssistantMessageEvent


class MessageEndEvent(WireModel):
    """The response is complete — or failed, which is also complete.

    `message` is the final assistant message either way. A stream that produced
    500 tokens and then died reports both, as in Tier 1.
    """

    type: Literal["message_end"] = "message_end"
    message: AssistantMessage
    stream_event: AssistantMessageEvent


# -------------------------------------------------------- tool execution scope

class ToolExecutionStartEvent(WireModel):
    """A tool is about to run. **The event Tier 1 could not emit.**"""

    type: Literal["tool_execution_start"] = "tool_execution_start"
    tool_call: ToolCall


class ToolExecutionUpdateEvent(WireModel):
    """Progress from a tool that is still running.

    Nothing emits this in Tier 2 — no built-in tool reports progress yet. It is
    declared because the vocabulary is ten, not nine, and because a long
    `run_shell` streaming its output is the obvious next use. Same reasoning as
    Tier 1's `CancellationToken`: the seam ships before the thing that fills it.
    """

    type: Literal["tool_execution_update"] = "tool_execution_update"
    tool_call_id: str
    details: dict[str, Any] | None = None


class ToolExecutionEndEvent(WireModel):
    type: Literal["tool_execution_end"] = "tool_execution_end"
    tool_call: ToolCall
    result: ToolResultMessage


AgentEvent = Annotated[
    AgentStartEvent
    | AgentEndEvent
    | TurnStartEvent
    | TurnEndEvent
    | MessageStartEvent
    | MessageUpdateEvent
    | MessageEndEvent
    | ToolExecutionStartEvent
    | ToolExecutionUpdateEvent
    | ToolExecutionEndEvent,
    Field(discriminator="type"),
]

AGENT_EVENT_TYPES = frozenset(
    {
        "agent_start",
        "agent_end",
        "turn_start",
        "turn_end",
        "message_start",
        "message_update",
        "message_end",
        "tool_execution_start",
        "tool_execution_update",
        "tool_execution_end",
    }
)
