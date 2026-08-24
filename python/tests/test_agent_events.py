"""The ten agent events — Layer 2's vocabulary.

Tier 1 had one vocabulary and the loop passed it straight through. Tier 2 has
two, and the distinction is the whole reason `agent_events.py` is a separate
file from `events.py`:

    the **12** describe one model response arriving, token by token
    the **10** describe the whole run's progress, coarsely

Pi and Tau converged on these ten names exactly as they converged on the twelve,
so the names are copied verbatim rather than improved.
"""

from __future__ import annotations

from omega.agent_events import AGENT_EVENT_TYPES


def test_there_are_exactly_ten() -> None:
    assert len(AGENT_EVENT_TYPES) == 10


def test_the_names_are_copied_verbatim_from_pi_and_tau() -> None:
    expected = frozenset(
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
    assert expected == AGENT_EVENT_TYPES


def test_they_nest_four_deep() -> None:
    """agent > turn > message > tool execution.

    Asserted as a property of the names rather than of a run: every level except
    `agent` is scoped by the one above it, which is what lets a UI indent them.
    """
    from omega.agent_events import AGENT_EVENT_NESTING

    assert AGENT_EVENT_NESTING == ("agent", "turn", "message", "tool_execution")
