"""The harness — the thing that owns the conversation.

Tier 1 had no such thing: `cli.py` held a bare list and the loop mutated it.
That works until something else needs the transcript, and in Tier 2 three
things do — persistence, orphan repair, and the steering queue. So one object
owns it.

These tests are also where the hooks get exercised, because the hooks are the
reason the loop does not have to grow.
"""

from __future__ import annotations

from typing import Any

from omega.agent_events import AgentEvent
from omega.harness import Harness
from omega.hooks import AgentHooks, ToolCallDecision
from omega.providers.fake import FakeProvider, text_turn, tool_turn
from omega.tools import Tool, ToolResult
from omega.types import AgentMessage, AssistantMessage, ToolCall, ToolResultMessage, UserMessage

RAN: list[dict[str, Any]] = []


async def _record(arguments: dict[str, Any], signal: Any) -> ToolResult:
    RAN.append(arguments)
    return ToolResult(content="did the thing")


def _tool() -> Tool:
    return Tool(name="ok", description="works", parameters={"type": "object"}, execute=_record)


def _harness(streams: list[list[Any]], *, hooks: AgentHooks | None = None) -> Harness:
    return Harness(
        provider=FakeProvider(streams),
        model="test-model",
        system="be helpful",
        tools=[_tool()],
        hooks=hooks,
    )


async def _drain(harness: Harness, prompt: str = "go") -> list[AgentEvent]:
    return [event async for event in harness.run(prompt)]


# ------------------------------------------------------------------ ownership


async def test_the_harness_owns_the_transcript() -> None:
    harness = _harness([text_turn("hello")])
    await _drain(harness)

    assert [m.role for m in harness.messages] == ["user", "assistant"]
    first = harness.messages[0]
    assert isinstance(first, UserMessage)
    assert first.content == "go"


async def test_the_transcript_survives_across_runs() -> None:
    """Two prompts, one harness. The second call must see the first exchange."""
    harness = _harness([text_turn("one"), text_turn("two")])
    await _drain(harness, "first")
    await _drain(harness, "second")

    assert [m.role for m in harness.messages] == ["user", "assistant", "user", "assistant"]


async def test_listeners_see_every_event_without_iterating() -> None:
    """A UI subscribes; it does not drive the loop. Boundary D, one direction."""
    harness = _harness([text_turn("hi")])
    seen: list[str] = []
    harness.add_listener(lambda event: seen.append(event.type))

    streamed = [e.type async for e in harness.run("go")]

    assert seen == streamed
    assert seen[0] == "agent_start"
    assert seen[-1] == "agent_end"


# ---------------------------------------------------------------------- hooks


async def test_before_tool_call_can_deny_and_the_tool_never_runs() -> None:
    """The gate approvals will fill in Step 4. Here it is proven to bite."""
    RAN.clear()

    async def deny(call: ToolCall) -> ToolCallDecision:
        return ToolCallDecision(allowed=False, reason="denied by policy")

    harness = _harness(
        [tool_turn("ok", {"x": 1}), text_turn("fine")],
        hooks=AgentHooks(before_tool_call=deny),
    )
    await _drain(harness)

    assert RAN == [], "a denied tool must not execute"
    result = next(m for m in harness.messages if isinstance(m, ToolResultMessage))
    assert result.is_error is True
    assert "denied by policy" in result.text


async def test_a_denied_tool_still_gets_a_result_so_the_transcript_stays_valid() -> None:
    """An unanswered tool call is a permanent API error. Denial is not silence."""
    async def deny(call: ToolCall) -> ToolCallDecision:
        return ToolCallDecision(allowed=False, reason="no")

    harness = _harness(
        [tool_turn("ok", {}, call_id="c1"), text_turn("fine")],
        hooks=AgentHooks(before_tool_call=deny),
    )
    await _drain(harness)

    calls = [
        b.id for m in harness.messages if isinstance(m, AssistantMessage) for b in m.tool_calls
    ]
    results = [m.tool_call_id for m in harness.messages if isinstance(m, ToolResultMessage)]
    assert calls == results == ["c1"]


async def test_after_tool_call_rewrites_what_the_model_reads() -> None:
    """Where truncation and secret redaction will live."""
    async def shout(call: ToolCall, result: ToolResult) -> ToolResult:
        return ToolResult(content=result.text.upper())

    harness = _harness(
        [tool_turn("ok", {}), text_turn("fine")],
        hooks=AgentHooks(after_tool_call=shout),
    )
    await _drain(harness)

    result = next(m for m in harness.messages if isinstance(m, ToolResultMessage))
    assert result.text == "DID THE THING"


async def test_transform_context_changes_what_is_sent_not_what_is_kept() -> None:
    """The seam compaction plugs into at Tier 3.

    Two views of history: the harness keeps everything, the provider sees the
    transformed version. Conflate them and a failed turn poisons the transcript.
    """
    async def only_the_last(messages: list[AgentMessage]) -> list[AgentMessage]:
        return messages[-1:]

    provider = FakeProvider([tool_turn("ok", {}), text_turn("done")])
    harness = Harness(
        provider=provider,
        model="test-model",
        system="be helpful",
        tools=[_tool()],
        hooks=AgentHooks(transform_context=only_the_last),
    )
    await _drain(harness)

    assert len(provider.calls[1].messages) == 1, "the provider should see the transformed view"
    assert len(harness.messages) == 4, "the harness keeps the whole transcript"


async def test_convert_to_llm_runs_before_transform_context() -> None:
    """Order matters: normalise first, then compact. Recorded so it cannot drift."""
    order: list[str] = []

    async def convert(messages: list[AgentMessage]) -> list[AgentMessage]:
        order.append("convert")
        return messages

    async def transform(messages: list[AgentMessage]) -> list[AgentMessage]:
        order.append("transform")
        return messages

    harness = _harness(
        [text_turn("hi")],
        hooks=AgentHooks(convert_to_llm=convert, transform_context=transform),
    )
    await _drain(harness)

    assert order == ["convert", "transform"]


async def test_no_hooks_is_the_same_as_permissive_hooks() -> None:
    """The default must be "do nothing", not "do something surprising"."""
    RAN.clear()
    harness = _harness([tool_turn("ok", {"y": 2}), text_turn("done")])
    await _drain(harness)

    assert RAN == [{"y": 2}]
