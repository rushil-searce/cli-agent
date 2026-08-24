"""The agent loop.

Ask qs to the model instead of knowing answers. If it requested tools, run them
and report back. Repeat until it stops asking. That is the whole idea, and it is
why this file is short.

**It should stay short.** If this file is growing, something in it is a *decision*
rather than the *mechanism* — may I run this, should I compact, is this output too
long — and decisions belong to a caller, reached through a callback. Pi's loop is
792 lines inside 109,000; Tau's is 318 inside 36,000. Neither grew as its system did.

Tier 2 changed two things here, and neither made it longer by much:

1. **It emits the ten agent events**, not the twelve provider ones. The twelve
   still travel, carried on `stream_event`, so nothing is lost — but the run now
   has a vocabulary for *its own* structure, which is what lets `cli.py` announce
   a tool while it runs instead of noticing afterwards that the list grew.
2. **It consults hooks.** Every hook is a decision the loop declines to make.
   Approvals, redaction and (at Tier 3) compaction all arrive as callbacks
   rather than as code in this file.
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator

from omega.agent_events import (
    AgentEndEvent,
    AgentEndReason,
    AgentEvent,
    AgentStartEvent,
    MessageEndEvent,
    MessageStartEvent,
    MessageUpdateEvent,
    ToolExecutionEndEvent,
    ToolExecutionStartEvent,
    TurnEndEvent,
    TurnStartEvent,
)
from omega.hooks import AgentHooks
from omega.provider import ModelProvider
from omega.tools import Tool
from omega.types import (
    AgentMessage,
    AssistantMessage,
    CancellationToken,
    ToolCall,
    ToolResultMessage,
)

DEFAULT_MAX_TURNS = 25


async def run_agent_loop(
    *,
    provider: ModelProvider,
    model: str,
    system: str,
    messages: list[AgentMessage],
    tools: list[Tool],
    hooks: AgentHooks | None = None,
    max_turns: int = DEFAULT_MAX_TURNS,
    signal: CancellationToken | None = None,
) -> AsyncIterator[AgentEvent]:
    """Run until the model stops requesting tools.

    `messages` is mutated in place: the caller's list *is* the transcript, and it
    grows with each assistant message and tool result. Tau does the same. In
    Tier 2 that caller is normally `Harness`, which owns the list — but the loop
    does not require one, which is what keeps it testable on its own.
    """
    hooks = hooks or AgentHooks()
    tool_by_name = {tool.name: tool for tool in tools}

    yield AgentStartEvent()

    for turn in range(max_turns):
        yield TurnStartEvent(turn=turn)
        assistant: AssistantMessage | None = None

        # What gets *sent* is derived from what is *kept*, never the same object.
        # Tier 3's compaction is a `transform_context` that returns something much
        # smaller; the transcript above is unaffected.
        context = await _context_for_request(messages, hooks)

        async for raw in provider.stream_response(
            model=model, system=system, messages=context, tools=tools, signal=signal
        ):
            # Branch on `raw.type` inline rather than assigning it to a variable
            # first — binding the tag to a name defeats type narrowing, which in
            # Tier 1 cost 136 mypy errors from one habit.
            if raw.type == "start":
                yield MessageStartEvent(message=raw.partial, stream_event=raw)
            elif raw.type == "done":
                assistant = raw.message
                yield MessageEndEvent(message=raw.message, stream_event=raw)
            elif raw.type == "error":
                assistant = raw.error
                yield MessageEndEvent(message=raw.error, stream_event=raw)
            else:
                yield MessageUpdateEvent(message=raw.partial, stream_event=raw)

        if assistant is None:
            # Defensive: the contract says this cannot happen. If a future
            # adapter breaks it, fail as data rather than crashing the run.
            yield TurnEndEvent(turn=turn)
            yield AgentEndEvent(
                reason="error", error_message="Provider produced no terminal event"
            )
            return

        messages.append(assistant)

        if assistant.stop_reason == "error" or assistant.stop_reason == "aborted":
            terminal: AgentEndReason = assistant.stop_reason
            yield TurnEndEvent(turn=turn)
            yield AgentEndEvent(reason=terminal, error_message=assistant.error_message)
            return

        # Stop on CONTENT, not on stop_reason. A response can carry tool calls
        # while its stop reason says something else, and content is ground truth
        # call is tool_request
        tool_requests = assistant.tool_calls
        if not tool_requests:
            yield TurnEndEvent(turn=turn)
            yield AgentEndEvent(reason="stop")
            return

        for tool_request in tool_requests:
            yield ToolExecutionStartEvent(tool_call=tool_request)
            result = await _execute_tool_call(tool_request, tool_by_name, hooks, signal)
            messages.append(result)
            yield ToolExecutionEndEvent(tool_call=tool_request, result=result)

        yield TurnEndEvent(turn=turn)

    # Fell out of the loop: a model that never stops asking would otherwise run
    # until the budget is gone. Reported as an event rather than appended to the
    # transcript — an empty failed assistant turn is not valid model context.
    yield AgentEndEvent(
        reason="max_turns", error_message=f"Stopped after max_turns={max_turns}"
    )


async def _context_for_request(
    messages: list[AgentMessage], hooks: AgentHooks
) -> list[AgentMessage]:
    """Build what the provider sees, leaving what the caller keeps alone.

    `convert_to_llm` first, then `transform_context`: normalise the transcript
    into something a model can read, *then* decide how much of it to send. The
    other order would ask compaction to reason about messages that were never
    going to be sent.
    """
    context = list(messages)
    if hooks.convert_to_llm is not None:
        context = list(await hooks.convert_to_llm(context))
    if hooks.transform_context is not None:
        context = list(await hooks.transform_context(context))
    return context


async def _execute_tool_call(
    tool_request: ToolCall,
    tool_by_name: dict[str, Tool],
    hooks: AgentHooks,
    signal: CancellationToken | None,
) -> ToolResultMessage:
    """Run one tool. Never raises.

    Every outcome — success, unknown tool, cancellation, refusal, crash — becomes
    a normal tool result. The model reads failures as observations and adapts,
    which is the entire point of an agent loop. An exception here would end the
    run instead. A *refusal* is in that list for a sharper reason: an unanswered
    tool call is rejected by providers forever, so "no" must still be an answer.
    """
    tool = tool_by_name.get(tool_request.name)
    if tool is None:
        return _error_result(tool_request, f"Tool {tool_request.name} not found")

    if signal is not None and signal.is_cancelled():
        return _error_result(tool_request, "Operation aborted")

    if hooks.before_tool_call is not None:
        decision = await hooks.before_tool_call(tool_request)
        if not decision.allowed:
            return _error_result(tool_request, decision.reason or "Tool call denied")

    try:
        result = await tool.execute(tool_request.arguments, signal)
    except asyncio.CancelledError:
        # Cancellation must propagate. Swallowing it in the broad except below
        # would make Ctrl-C unreliable — and this is Python, where cancellation
        # arrives as an exception.
        raise
    except Exception as exc:  # noqa: BLE001 - tools are an isolation boundary
        # A tool is third-party code touching the filesystem and the network. If
        # a crashing tool crashed the agent, one bad tool would end every session.
        return _error_result(tool_request, str(exc) or exc.__class__.__name__)

    if hooks.after_tool_call is not None:
        result = await hooks.after_tool_call(tool_request, result)

    return ToolResultMessage(
        tool_call_id=tool_request.id,
        tool_name=tool_request.name,
        content=result.content,
        is_error=False,
    )


def _error_result(tool_request: ToolCall, message: str) -> ToolResultMessage:
    return ToolResultMessage(
        tool_call_id=tool_request.id,
        tool_name=tool_request.name,
        content=message,  # type: ignore[arg-type]
        is_error=True,
    )
