"""The approval gate — the half of failure #4 that confinement cannot reach.

`paths.py` bounds *where* the file tools can go. It says nothing about a shell
command deleting the wrong directory inside that boundary, and nothing at all
about the shell walking out with `cd ..`. So there is a second control, and it
asks a human.

**It fills `before_tool_call`, which means the loop gains nothing from it.** A
whole policy subsystem — a deny list, a prompt, per-session memory — plugs in
through one callback. That is Boundary B doing the job it was drawn for in
Step 1, and it is the concrete answer to "why doesn't the loop grow?"

Three decisions, each of which could have gone the lazy way:

**Reads are not gated.** Confinement already bounds them. A prompt on every read
would fire dozens of times per task, and a prompt that fires constantly is a
prompt people answer without looking — which converts the gate into theatre and
makes the *dangerous* prompt less likely to be read.

**Catastrophes are denied, never asked.** Asking "are you sure?" about wiping a
disk is a trap, because by then the user is in the rhythm of saying yes. A short
list of things that are simply refused is worth more than a scarier prompt. The
list stays *tight* on purpose: a deny list that blocks ordinary work becomes the
feature people switch off.

**No approval channel means deny.** If nothing can ask, the answer is no. The
alternative — treating "nobody is watching" as consent — is how a headless run
becomes an unattended one.
"""

from __future__ import annotations

import re
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from omega.hooks import ALLOW, ToolCallDecision
from omega.types import ToolCall

#: What a human can answer. `always` is scoped to one tool, never to everything:
#: "yes, you may run commands" must not also mean "yes, you may rewrite files".
Answer = Literal["once", "always", "deny"]


@dataclass(frozen=True, slots=True)
class ApprovalRequest:
    """What the user is being asked to approve.

    `summary` is the whole value of this type. A prompt that says "allow
    run_shell?" cannot be evaluated; one that quotes the actual command can.
    """

    tool_name: str
    summary: str
    arguments: dict[str, Any]


Asker = Callable[[ApprovalRequest], Awaitable[Answer]]

#: Tools that only observe. Gating these costs attention and buys nothing,
#: because `paths.py` has already bounded where they can look.
READ_ONLY_TOOLS = frozenset({"read_file"})


def _deletes_a_root(command: str) -> bool:
    """A recursive delete aimed at a filesystem or home root.

    Written as code rather than one heroic regex because the distinction is
    genuinely two-part — a recursive flag *and* a target that is a root — and a
    single pattern expressing both is unreadable, therefore unreviewable.

    The point of the target check is to let ordinary work through. Deleting a
    build directory recursively is a normal thing for a coding agent to want.
    """
    home = str(Path.home())
    for match in re.finditer(r"\brm\b(?P<rest>[^;&|\n]*)", command):
        rest = match.group("rest")
        flags = "".join(re.findall(r"(?<!\S)-(\w+)", rest)).lower()
        if "r" not in flags:
            continue
        for target in re.findall(r"(?<!\S)(?!-)(\S+)", rest):
            # Trailing slashes and globs do not change what is being deleted.
            if target.rstrip("/*") in {"", "~", "$HOME", home}:
                return True
    return False


def _matches(pattern: str, flags: int = 0) -> Callable[[str], bool]:
    compiled = re.compile(pattern, flags)
    return lambda command: compiled.search(command) is not None


#: Refused outright, never prompted. Deliberately short — see the module
#: docstring on why a broad deny list is worse than a narrow one.
_FORBIDDEN: tuple[tuple[str, Callable[[str], bool]], ...] = (
    ("a recursive delete of a filesystem or home root", _deletes_a_root),
    ("formatting a filesystem", _matches(r"\bmkfs(\.\w+)?\b")),
    ("a raw write to a block device", _matches(r"\bdd\b[^\n]*\bof=/dev/")),
    ("a fork bomb", _matches(r":\s*\(\s*\)\s*\{.*\|.*&.*\}\s*;\s*:")),
    (
        "a recursive permission change on the filesystem root",
        _matches(r"\bchmod\s+(-\S+\s+)*777\s+/\s*$"),
    ),
    (
        "shutting down or rebooting the machine",
        _matches(r"\b(shutdown|reboot|halt|poweroff)\b"),
    ),
)


def _forbidden_reason(call: ToolCall) -> str | None:
    """Why this call is on the deny list, or None if it is not."""
    if call.name != "run_shell":
        return None
    command = str(call.arguments.get("command", ""))
    for reason, matches in _FORBIDDEN:
        if matches(command):
            return reason
    return None


def _summarise(call: ToolCall) -> str:
    """One line a human can judge in the time they will actually spend on it."""
    arguments = call.arguments
    if call.name == "run_shell":
        return str(arguments.get("command", ""))
    if call.name == "write_file":
        content = str(arguments.get("content", ""))
        return f"write {len(content)} chars to {arguments.get('path', '?')}"
    if call.name == "edit_file":
        return f"edit {arguments.get('path', '?')}"
    return f"{call.name}({arguments})"


class ApprovalPolicy:
    """A `before_tool_call` hook that asks before anything changes.

    Callable, so it *is* the hook — no adapter, no registration step. `AgentHooks`
    accepts any callable of the right shape, which is what a `Callable` alias
    buys over a base class.
    """

    def __init__(
        self,
        *,
        asker: Asker | None = None,
        auto_approve: bool = False,
        read_only: frozenset[str] = READ_ONLY_TOOLS,
    ) -> None:
        self._asker = asker
        self._auto_approve = auto_approve
        self._read_only = read_only

        #: Tools the user said "always" to. Per session, in memory. A persisted
        #: trust store is a config concern and arrives with config.
        self._always: set[str] = set()

    async def __call__(self, call: ToolCall) -> ToolCallDecision:
        if call.name in self._read_only:
            return ALLOW

        # Checked before auto_approve: `--yes` means "stop asking me", not
        # "disable the brakes".
        forbidden = _forbidden_reason(call)
        if forbidden is not None:
            return ToolCallDecision(
                allowed=False,
                reason=(
                    f"This is refused outright ({forbidden}) and was not run. "
                    "It is not something the user can approve. Achieve the goal a "
                    "narrower way, or explain what you were trying to do."
                ),
            )

        if self._auto_approve or call.name in self._always:
            return ALLOW

        if self._asker is None:
            return ToolCallDecision(
                allowed=False,
                reason=(
                    f"Denied: no approval channel is available, so {call.name} cannot be "
                    "confirmed. Run omega interactively, or start it with --yes to approve "
                    "automatically."
                ),
            )

        answer = await self._asker(
            ApprovalRequest(
                tool_name=call.name, summary=_summarise(call), arguments=dict(call.arguments)
            )
        )

        if answer == "always":
            self._always.add(call.name)
            return ALLOW
        if answer == "once":
            return ALLOW

        # Not remembered. The model is told why and may legitimately ask for
        # something different next; a remembered refusal would block that too.
        return ToolCallDecision(
            allowed=False,
            reason=(
                f"The user declined this {call.name} call. Do not retry it as-is - "
                "ask what they would prefer, or take a different approach."
            ),
        )
