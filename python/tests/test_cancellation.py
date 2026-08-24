"""Cancellation — beginner failure #3, first half.

Tier 1 threaded a `CancellationToken` through every layer and never created one.
The seam was complete and inert. This is the tier that fills it.

The important thing being tested is not "Ctrl-C works". It is that a cancelled
run still ends *properly*: exactly one `agent_end`, a valid transcript, and a
provider that upheld its contract on the way out. A cancellation that leaves the
conversation malformed is worse than no cancellation at all, because the damage
only shows up later.
"""

from __future__ import annotations

from typing import Any

from omega.agent_events import AgentEvent
from omega.cancellation import CancelSignal
from omega.harness import Harness
from omega.providers.fake import FakeProvider, text_turn, tool_turn
from omega.tools import Tool, ToolResult


async def _ok(arguments: dict[str, Any], signal: Any) -> ToolResult:
    return ToolResult(content="ran")


OK_TOOL = Tool(name="ok", description="works", parameters={"type": "object"}, execute=_ok)


def _harness(streams: list[list[Any]], signal: CancelSignal) -> Harness:
    return Harness(
        provider=FakeProvider(streams),
        model="test-model",
        system="be helpful",
        tools=[OK_TOOL],
        signal=signal,
    )


# ------------------------------------------------------------------- the token


def test_the_token_starts_clear_and_latches_when_set() -> None:
    signal = CancelSignal()
    assert signal.is_cancelled() is False
    signal.cancel()
    assert signal.is_cancelled() is True
    signal.reset()
    assert signal.is_cancelled() is False


def test_it_satisfies_the_protocol_without_inheriting_it() -> None:
    """Structural typing, same as FakeProvider and ModelProvider."""
    from omega.types import CancellationToken

    assert isinstance(CancelSignal(), CancellationToken)


# ------------------------------------------------------------------ mid-stream


async def test_cancelling_mid_stream_ends_the_run_as_aborted() -> None:
    signal = CancelSignal()
    harness = _harness([text_turn("this will be cut off")], signal)

    def cut(event: AgentEvent) -> None:
        if event.type == "message_update":
            signal.cancel()

    harness.add_listener(cut)
    events = [event async for event in harness.run("go")]

    assert events[-1].type == "agent_end"
    assert events[-1].reason == "aborted"


async def test_a_cancelled_stream_still_produces_one_terminal_event() -> None:
    """The provider contract does not get a cancellation exemption.

    A stream that just stops would leave the loop with no assistant message and
    force it into its defensive "provider produced no terminal event" branch —
    reporting a *bug* where the user simply pressed Ctrl-C.
    """
    signal = CancelSignal()
    harness = _harness([text_turn("cut off")], signal)

    def cut(event: AgentEvent) -> None:
        if event.type == "message_update":
            signal.cancel()

    harness.add_listener(cut)
    events = [event async for event in harness.run("go")]

    ends = [e for e in events if e.type == "message_end"]
    assert len(ends) == 1
    assert ends[0].message.stop_reason == "aborted"
    assert "no terminal event" not in (events[-1].error_message or "")


# --------------------------------------------------------------- between turns


async def test_cancelling_between_turns_stops_before_the_next_request() -> None:
    """The cheapest cancellation there is: don't start the next turn."""
    signal = CancelSignal()
    provider = FakeProvider([tool_turn("ok", {}), text_turn("never reached")])
    harness = Harness(
        provider=provider,
        model="test-model",
        system="be helpful",
        tools=[OK_TOOL],
        signal=signal,
    )

    def stop_after_the_tool(event: AgentEvent) -> None:
        if event.type == "tool_execution_end":
            signal.cancel()

    harness.add_listener(stop_after_the_tool)
    events = [event async for event in harness.run("go")]

    assert len(provider.calls) == 1, "a second request was sent after cancellation"
    assert events[-1].type == "agent_end"
    assert events[-1].reason == "aborted"


async def test_no_spurious_turn_is_announced_when_cancelled() -> None:
    """turn_start must be paired with turn_end. A UI indents on that."""
    signal = CancelSignal()
    harness = _harness([tool_turn("ok", {}), text_turn("never reached")], signal)

    def stop_after_the_tool(event: AgentEvent) -> None:
        if event.type == "tool_execution_end":
            signal.cancel()

    harness.add_listener(stop_after_the_tool)
    events = [event async for event in harness.run("go")]

    starts = [e.turn for e in events if e.type == "turn_start"]
    ends = [e.turn for e in events if e.type == "turn_end"]
    assert starts == ends == [0]


# ------------------------------------------------------------------ the reset


async def test_the_token_is_cleared_before_each_run() -> None:
    """Otherwise the first Ctrl-C would cancel every later turn too.

    This is the bug that makes a cancellable agent feel broken: you interrupt
    once, and from then on nothing works until you restart.
    """
    signal = CancelSignal()
    signal.cancel()
    harness = _harness([text_turn("hello")], signal)

    events = [event async for event in harness.run("go")]

    assert events[-1].reason == "stop", "a stale token poisoned the next turn"


async def test_a_cancelled_run_can_be_followed_by_a_working_one() -> None:
    signal = CancelSignal()
    harness = _harness([text_turn("cut"), text_turn("fine")], signal)

    def cut_once(event: AgentEvent) -> None:
        if event.type == "message_update" and len(harness.messages) < 3:
            signal.cancel()

    harness.add_listener(cut_once)
    first = [event async for event in harness.run("one")]
    assert first[-1].reason == "aborted"

    second = [event async for event in harness.run("two")]
    assert second[-1].reason == "stop"


# ------------------------------------------------------- the real-world case


async def test_ctrl_c_during_a_tool_leaves_a_valid_transcript() -> None:
    """The scenario failure #3 actually describes.

    You press Ctrl-C while a command is running. The interrupt lands *inside* the
    tool, not between turns and not mid-stream. Tier 1 killed the process here,
    which is how the unanswered-tool-call corruption got created in the first
    place.

    Three things must hold afterwards: the tool call was answered, the run ended
    as `aborted` rather than as an error, and the next prompt works.
    """
    signal = CancelSignal()

    async def interrupted_midway(arguments: dict[str, Any], token: Any) -> ToolResult:
        signal.cancel()  # stands in for the user's Ctrl-C
        return ToolResult(content="partially done")

    tool = Tool(
        name="slow",
        description="takes a while",
        parameters={"type": "object"},
        execute=interrupted_midway,
    )
    provider = FakeProvider(
        [tool_turn("slow", {}, call_id="c1"), text_turn("should not be reached")]
    )
    harness = Harness(
        provider=provider, model="m", system="s", tools=[tool], signal=signal
    )

    events = [event async for event in harness.run("run the slow thing")]

    assert len(provider.calls) == 1, "the loop must not start a turn after cancellation"
    assert events[-1].reason == "aborted"

    from omega.types import AssistantMessage, ToolResultMessage

    asked = {
        b.id for m in harness.messages if isinstance(m, AssistantMessage) for b in m.tool_calls
    }
    answered = {m.tool_call_id for m in harness.messages if isinstance(m, ToolResultMessage)}
    assert asked == answered == {"c1"}, "an unanswered call would invalidate this forever"


async def test_the_transcript_after_an_interrupt_is_resumable() -> None:
    """The proof that matters: the *next* request succeeds.

    Failure #3's real damage is that a corrupted transcript fails on every
    future request, so the test of the fix is not the interrupt — it is what
    happens afterwards.
    """
    signal = CancelSignal()

    async def interrupted_midway(arguments: dict[str, Any], token: Any) -> ToolResult:
        signal.cancel()
        return ToolResult(content="partial")

    tool = Tool(
        name="slow",
        description="takes a while",
        parameters={"type": "object"},
        execute=interrupted_midway,
    )
    provider = FakeProvider(
        [tool_turn("slow", {}), text_turn("unreached"), text_turn("resumed cleanly")]
    )
    harness = Harness(
        provider=provider, model="m", system="s", tools=[tool], signal=signal
    )

    async for _event in harness.run("first"):
        pass

    second = [event async for event in harness.run("second")]
    assert second[-1].reason == "stop"

    sent = provider.calls[-1].messages
    from omega.types import AssistantMessage, ToolResultMessage

    asked = {b.id for m in sent if isinstance(m, AssistantMessage) for b in m.tool_calls}
    answered = {m.tool_call_id for m in sent if isinstance(m, ToolResultMessage)}
    assert asked <= answered, "the resumed request carried an unanswered tool call"
