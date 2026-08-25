"""A cancellation token you can actually set.

`types.py` defines `CancellationToken` as a Protocol — one method, "should I
stop?" — and Tier 1 threaded it through the provider interface, the loop, and
every tool executor without ever creating one. The seam was complete and inert.
This is the twenty lines that fill it.

Kept separate from `harness.py` on purpose. The harness *owns* an instance, but
the token itself has no dependencies and no knowledge of a conversation, which
makes it trivially testable and reusable by anything that needs to be
interruptible.

**It latches.** Once cancelled it stays cancelled until `reset()`, so a check
that happens slightly late still sees the cancellation. The alternative — a
signal that clears itself when read — loses interrupts that arrive between two
checks, which is the worst kind of bug to debug.
"""

from __future__ import annotations


class CancelSignal:
    """Set by whoever handles the interrupt; read by whoever can act on it.

    Deliberately not `asyncio.Event`. An Event's natural use is `await
    event.wait()`, which invites code that blocks until cancellation. What is
    wanted here is the opposite: a cheap, synchronous "am I still wanted?" that
    a tool can poll inside a loop, and that a signal handler can set without
    needing an event loop to hand.
    """

    __slots__ = ("_cancelled",)

    def __init__(self) -> None:
        self._cancelled = False

    def is_cancelled(self) -> bool:
        """The whole `CancellationToken` protocol."""
        return self._cancelled

    def cancel(self) -> None:
        """Request a stop. Idempotent, and safe to call from a signal handler."""
        self._cancelled = True

    def reset(self) -> None:
        """Clear the request, ready for the next turn.

        The harness calls this before every run. Without it the first Ctrl-C
        would cancel every later turn too — an agent that appears to break
        permanently the first time you interrupt it.
        """
        self._cancelled = False
