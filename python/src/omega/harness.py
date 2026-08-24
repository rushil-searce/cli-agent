"""The harness — the object that owns the conversation.

Tier 1 had nothing here, and `cli.py` held a bare `list`. That is fine while the
transcript has exactly one reader. It stops being fine the moment something else
needs it, and in Tier 2 three things do:

* **persistence** must write entries as they appear
* **orphan repair** must scan the transcript after an interrupt
* **the steering queue** must add to it between turns

`python/TIER-1.md` named this directly: orphan repair "needs a harness that owns
`messages`". So one object owns it, and the loop stays a function over a list.

**Nothing flows downward from a UI.** A listener subscribes and is called; it
cannot reach in and drive the loop. When you type while the agent works, the text
is *queued* on the harness and the loop picks it up when it is ready. That
strictness is why Tau's whole agent-to-UI bridge is 99 lines, and why the same
agent could later run on a server with the UI somewhere else.
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Callable, Sequence

from omega.agent_events import AgentEvent
from omega.hooks import AgentHooks
from omega.loop import DEFAULT_MAX_TURNS, run_agent_loop
from omega.provider import ModelProvider
from omega.tools import Tool
from omega.types import AgentMessage, CancellationToken, UserMessage

#: A subscriber. Synchronous and returning nothing, deliberately: a listener that
#: could block or fail would be able to stall the loop it is only watching.
AgentListener = Callable[[AgentEvent], None]


class Harness:
    """Holds the transcript and the run configuration; drives the loop.

    One harness is one conversation. Call `run()` repeatedly and the transcript
    accumulates, which is what makes a REPL a conversation rather than a series
    of unrelated questions.
    """

    def __init__(
        self,
        *,
        provider: ModelProvider,
        model: str,
        system: str,
        tools: Sequence[Tool],
        hooks: AgentHooks | None = None,
        max_turns: int = DEFAULT_MAX_TURNS,
        signal: CancellationToken | None = None,
    ) -> None:
        self.provider = provider
        self.model = model
        self.system = system
        self.tools = list(tools)
        self.hooks = hooks if hooks is not None else AgentHooks()
        self.max_turns = max_turns
        self.signal = signal

        #: The transcript. The harness owns it; the loop appends to it.
        self.messages: list[AgentMessage] = []
        self._listeners: list[AgentListener] = []

    def add_listener(self, listener: AgentListener) -> None:
        """Subscribe to the agent events. Boundary D, and it only goes one way."""
        self._listeners.append(listener)

    async def run(self, prompt: str) -> AsyncIterator[AgentEvent]:
        """One user prompt, run to completion.

        Events are both handed to every listener and yielded to the caller, so a
        UI can subscribe while a test simply iterates.
        """
        self.messages.append(UserMessage(content=prompt))

        async for event in run_agent_loop(
            provider=self.provider,
            model=self.model,
            system=self.system,
            messages=self.messages,
            tools=self.tools,
            hooks=self.hooks,
            max_turns=self.max_turns,
            signal=self.signal,
        ):
            for listener in self._listeners:
                listener(event)
            yield event
