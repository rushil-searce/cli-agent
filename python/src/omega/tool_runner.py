"""Running one tool. Extracted from `loop.py` because the tripwire fired.

`04-boundaries-and-layout.md` Rule 4 says the loop gets its own file and should
not grow, with a number attached: past roughly 250 lines, something in it is not
the loop's own mechanism. Adding the between-turns queues in Step 6 took
`loop.py` to 249, and this is what came out.

It is the right thing to have moved. The loop's mechanism is *ask the model, run
what it asked for, repeat*. **How** one tool call becomes one tool result —
looking up the tool, consulting the gate, catching the crash, letting
cancellation through — is a separate mechanism that happens to be called from
there. Splitting it makes both readable, and the loop is back to the shape the
rule describes.

Nothing here is a *decision*. Every policy is still somebody else's function,
reached through `hooks`.
"""

from __future__ import annotations

import asyncio

from omega.hooks import AgentHooks
from omega.tools import Tool
from omega.types import CancellationToken, ToolCall, ToolResultMessage


async def execute_tool_call(
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
