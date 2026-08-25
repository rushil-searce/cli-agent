"""Orphaned tool-result repair — beginner failure #3, second half.

**The nastiest bug in the nine**, because it is silent until you add persistence
and then it looks like data corruption.

The mechanism: an assistant message says "run this tool" and carries a
`tool_use` block with an id. If no `tool_result` with that id follows, providers
reject the conversation outright — not once, but on **every future request**. The
transcript is permanently invalid. Interrupt a run at the wrong moment and you
have created a file that can never be resumed.

`anatomy.md:254` says this ships "the same day you add cancellation", and that
is why these two are one step: cancellation without repair converts a working
agent into a corruption generator.

The fix is unglamorous — synthesize the missing result and say it was interrupted.
"""

from __future__ import annotations

from typing import Any

from omega.harness import Harness
from omega.providers.fake import FakeProvider, text_turn
from omega.tools import Tool, ToolResult
from omega.types import AssistantMessage, ToolCall, ToolResultMessage, UserMessage


async def _ok(arguments: dict[str, Any], signal: Any) -> ToolResult:
    return ToolResult(content="ran")


OK_TOOL = Tool(name="ok", description="works", parameters={"type": "object"}, execute=_ok)


def _harness(streams: list[list[Any]] | None = None) -> Harness:
    return Harness(
        provider=FakeProvider(streams if streams is not None else []),
        model="test-model",
        system="be helpful",
        tools=[OK_TOOL],
    )


def _asked_for(*call_ids: str) -> AssistantMessage:
    return AssistantMessage(
        model="test-model",
        stop_reason="toolUse",
        content=[ToolCall(id=cid, name="ok", arguments={}) for cid in call_ids],
    )


def _answered(call_id: str) -> ToolResultMessage:
    return ToolResultMessage(tool_call_id=call_id, tool_name="ok", content="fine")


# ------------------------------------------------------------------- the repair


def test_an_unanswered_call_gets_a_result() -> None:
    harness = _harness()
    harness.messages.extend([UserMessage(content="go"), _asked_for("c1")])

    assert harness.repair_orphans() == 1

    assert [m.role for m in harness.messages] == ["user", "assistant", "toolResult"]
    result = harness.messages[-1]
    assert isinstance(result, ToolResultMessage)
    assert result.tool_call_id == "c1"
    assert result.is_error is True
    assert "nterrupt" in result.text, "the model should be told what happened"


def test_a_complete_transcript_is_left_alone() -> None:
    harness = _harness()
    harness.messages.extend([UserMessage(content="go"), _asked_for("c1"), _answered("c1")])
    before = [m.model_copy(deep=True) for m in harness.messages]

    assert harness.repair_orphans() == 0
    assert harness.messages == before


def test_only_the_missing_call_of_several_is_answered() -> None:
    """A parallel turn interrupted halfway. Two answered, one not."""
    harness = _harness()
    harness.messages.extend(
        [UserMessage(content="go"), _asked_for("a", "b", "c"), _answered("a"), _answered("c")]
    )

    assert harness.repair_orphans() == 1

    results = [m for m in harness.messages if isinstance(m, ToolResultMessage)]
    assert [r.tool_call_id for r in results] == ["a", "c", "b"]
    synthesized = next(r for r in results if r.tool_call_id == "b")
    assert synthesized.is_error is True


def test_the_result_lands_beside_its_own_call_not_at_the_end() -> None:
    """Ordering is a provider requirement, not a preference.

    Results must belong to the assistant turn that asked. Appending everything
    to the end of a multi-turn transcript would answer the wrong message.
    """
    harness = _harness()
    harness.messages.extend(
        [
            UserMessage(content="go"),
            _asked_for("first"),  # interrupted, no result
            UserMessage(content="again"),
            _asked_for("second"),
            _answered("second"),
        ]
    )

    assert harness.repair_orphans() == 1

    roles = [m.role for m in harness.messages]
    assert roles == ["user", "assistant", "toolResult", "user", "assistant", "toolResult"]
    repaired = harness.messages[2]
    assert isinstance(repaired, ToolResultMessage)
    assert repaired.tool_call_id == "first"


def test_repair_is_idempotent() -> None:
    harness = _harness()
    harness.messages.extend([UserMessage(content="go"), _asked_for("c1")])

    assert harness.repair_orphans() == 1
    assert harness.repair_orphans() == 0, "the second pass must find nothing to fix"


def test_a_message_with_no_tool_calls_is_untouched() -> None:
    harness = _harness()
    harness.messages.extend(
        [UserMessage(content="go"), AssistantMessage(model="m", stop_reason="stop")]
    )

    assert harness.repair_orphans() == 0
    assert len(harness.messages) == 2


# ------------------------------------------------------------------- automatic


async def test_repair_runs_before_the_next_prompt() -> None:
    """The user should not have to know this failure mode exists.

    An interrupted transcript is healed on the way into the next turn, so the
    request that would have failed permanently simply succeeds.
    """
    harness = _harness([text_turn("carrying on")])
    harness.messages.extend([UserMessage(content="go"), _asked_for("orphan")])

    events = [event async for event in harness.run("next")]

    assert events[-1].reason == "stop"
    roles = [m.role for m in harness.messages]
    assert roles == ["user", "assistant", "toolResult", "user", "assistant"]


async def test_the_provider_never_sees_an_unanswered_call() -> None:
    """The assertion that actually matters: what went over the wire was valid."""
    provider = FakeProvider([text_turn("ok")])
    harness = Harness(
        provider=provider, model="m", system="s", tools=[OK_TOOL]
    )
    harness.messages.extend([UserMessage(content="go"), _asked_for("orphan")])

    async for _event in harness.run("next"):
        pass

    sent = provider.calls[0].messages
    asked = {b.id for m in sent if isinstance(m, AssistantMessage) for b in m.tool_calls}
    answered = {m.tool_call_id for m in sent if isinstance(m, ToolResultMessage)}
    assert asked <= answered, f"unanswered tool calls reached the provider: {asked - answered}"
