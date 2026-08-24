"""The approval gate — beginner failure #4, the half confinement cannot reach.

Path confinement stops `read_file` touching `~/.ssh`. It does nothing about a
shell command deleting the wrong directory *inside* the root, and nothing at all
about the shell walking out with `cd ..`.

So there is a gate, and it lives in `before_tool_call` — which means **the loop
gains no lines from it.** That is the test of whether Boundary B was drawn
correctly in Step 1: a whole policy subsystem plugs in through one callback.

Three behaviours worth defending:

* **Reads are not gated.** Confinement already bounds them, and a prompt per read
  trains the user to hit "yes" without looking, which is how a gate becomes
  theatre.
* **Catastrophes are denied, never asked.** Prompting for a disk-wipe is a trap:
  the answer arrives reflexively.
* **No approval channel means deny.** A headless run must not silently become an
  unattended one.

The dangerous-looking strings in `CATASTROPHES` are test data. Every one is
asserted to be *refused*; nothing here runs a shell.
"""

from __future__ import annotations

from typing import Any

import pytest

from omega.approval import ApprovalPolicy, ApprovalRequest
from omega.types import ToolCall

CATASTROPHES = [
    'rm -rf /',
    'rm -rf /*',
    'sudo rm -rf /',
    'rm -fr ~',
    'mkfs.ext4 /dev/sda1',
    'dd if=/dev/zero of=/dev/sda',
    ':(){ :|:& };:',
    'chmod -R 777 /',
    'shutdown -h now',
]


def _call(name: str, **arguments: Any) -> ToolCall:
    return ToolCall(id="c1", name=name, arguments=arguments)


async def _yes(request: ApprovalRequest) -> str:
    return "once"


async def _no(request: ApprovalRequest) -> str:
    return "deny"


# --------------------------------------------------------------- what is gated


async def test_reading_is_never_gated() -> None:
    """Confinement already bounds reads; a prompt per read is training to ignore."""
    policy = ApprovalPolicy(asker=_no)

    assert (await policy(_call("read_file", path="a.txt"))).allowed is True


@pytest.mark.parametrize("tool", ["write_file", "edit_file", "run_shell"])
async def test_anything_that_changes_the_world_is_gated(tool: str) -> None:
    policy = ApprovalPolicy(asker=_no)

    decision = await policy(
        _call(tool, path="a.txt", content="x", command="ls", old_text="a", new_text="b")
    )
    assert decision.allowed is False
    assert decision.reason


async def test_an_unknown_tool_is_gated_by_default() -> None:
    """Fail closed. A tool added later must not be exempt by omission."""
    policy = ApprovalPolicy(asker=_no)

    assert (await policy(_call("send_email", to="x"))).allowed is False


# -------------------------------------------------------------------- answers


async def test_yes_allows_this_one_call() -> None:
    policy = ApprovalPolicy(asker=_yes)

    assert (await policy(_call("run_shell", command="ls"))).allowed is True


async def test_always_stops_asking_for_that_tool() -> None:
    asked: list[str] = []

    async def always(request: ApprovalRequest) -> str:
        asked.append(request.tool_name)
        return "always"

    policy = ApprovalPolicy(asker=always)

    assert (await policy(_call("run_shell", command="ls"))).allowed is True
    assert (await policy(_call("run_shell", command="pwd"))).allowed is True
    assert asked == ["run_shell"], "the second call should not have prompted"


async def test_always_is_scoped_to_one_tool() -> None:
    """"Always allow shell" must not also mean "always allow writes"."""
    asked: list[str] = []

    async def always(request: ApprovalRequest) -> str:
        asked.append(request.tool_name)
        return "always"

    policy = ApprovalPolicy(asker=always)
    await policy(_call("run_shell", command="ls"))
    await policy(_call("write_file", path="a", content="b"))

    assert asked == ["run_shell", "write_file"]


async def test_a_denial_is_not_remembered() -> None:
    """The model is told why and may legitimately ask for something else next."""
    asked: list[str] = []

    async def deny(request: ApprovalRequest) -> str:
        asked.append(request.summary)
        return "deny"

    policy = ApprovalPolicy(asker=deny)
    await policy(_call("run_shell", command="git clean -fdx"))
    await policy(_call("run_shell", command="ls"))

    assert len(asked) == 2, "a refusal must not silently blacklist the tool"


# ------------------------------------------------------------- the deny list


@pytest.mark.parametrize("command", CATASTROPHES)
async def test_catastrophes_are_denied_without_asking(command: str) -> None:
    """Prompting here is a trap - the answer arrives reflexively."""
    asked: list[str] = []

    async def record(request: ApprovalRequest) -> str:
        asked.append(request.summary)
        return "once"

    policy = ApprovalPolicy(asker=record)
    decision = await policy(_call("run_shell", command=command))

    assert decision.allowed is False, command
    assert asked == [], "this must never reach a human for confirmation"
    assert "refused outright" in (decision.reason or "")


async def test_auto_approve_does_not_override_the_deny_list() -> None:
    """--yes means "stop asking me", not "disable the brakes"."""
    policy = ApprovalPolicy(auto_approve=True)

    assert (await policy(_call("run_shell", command=CATASTROPHES[0]))).allowed is False


@pytest.mark.parametrize(
    "command", ["rm -rf build", "rm -rf ./node_modules", "git clean -fdx", "docker system prune"]
)
async def test_ordinary_destructive_commands_are_asked_not_denied(command: str) -> None:
    """The deny list must stay tight, or it becomes the thing people switch off."""
    policy = ApprovalPolicy(asker=_yes)

    assert (await policy(_call("run_shell", command=command))).allowed is True


# ------------------------------------------------------------------- defaults


async def test_no_asker_means_deny() -> None:
    """A headless run must not quietly become an unattended one."""
    policy = ApprovalPolicy()

    decision = await policy(_call("run_shell", command="ls"))
    assert decision.allowed is False
    assert "no approval channel" in (decision.reason or "").lower()


async def test_auto_approve_allows_ordinary_work() -> None:
    policy = ApprovalPolicy(auto_approve=True)

    assert (await policy(_call("run_shell", command="ls"))).allowed is True
    assert (await policy(_call("write_file", path="a", content="b"))).allowed is True


# ------------------------------------------------------------------ the prompt


async def test_the_request_describes_what_will_happen() -> None:
    """A prompt the user cannot evaluate is worse than no prompt at all."""
    seen: list[ApprovalRequest] = []

    async def capture(request: ApprovalRequest) -> str:
        seen.append(request)
        return "once"

    policy = ApprovalPolicy(asker=capture)
    await policy(_call("run_shell", command="pytest -q"))
    await policy(_call("write_file", path="notes.md", content="hello world"))
    await policy(_call("edit_file", path="app.py", old_text="a", new_text="b"))

    assert "pytest -q" in seen[0].summary
    assert "notes.md" in seen[1].summary
    assert "11" in seen[1].summary, "the size of the write is the thing to judge"
    assert "app.py" in seen[2].summary


# --------------------------------------------------------- it plugs into the loop


async def test_the_gate_stops_a_tool_through_the_real_loop() -> None:
    """End to end: the policy as a before_tool_call hook, and the tool never runs."""
    from omega.harness import Harness
    from omega.hooks import AgentHooks
    from omega.providers.fake import FakeProvider, text_turn, tool_turn
    from omega.tools import Tool, ToolResult
    from omega.types import ToolResultMessage

    ran: list[str] = []

    async def dangerous(arguments: dict[str, Any], signal: Any) -> ToolResult:
        ran.append("executed")
        return ToolResult(content="done")

    tool = Tool(
        name="run_shell", description="d", parameters={"type": "object"}, execute=dangerous
    )
    harness = Harness(
        provider=FakeProvider(
            [tool_turn("run_shell", {"command": CATASTROPHES[0]}), text_turn("ok")]
        ),
        model="m",
        system="s",
        tools=[tool],
        hooks=AgentHooks(before_tool_call=ApprovalPolicy(auto_approve=True)),
    )

    async for _event in harness.run("clean up"):
        pass

    assert ran == [], "the deny list did not reach the loop"
    result = next(m for m in harness.messages if isinstance(m, ToolResultMessage))
    assert result.is_error is True
    assert "refused outright" in result.text


async def test_an_unresolvable_home_directory_does_not_crash_the_check(
    monkeypatch: Any,
) -> None:
    """A safety check that raises inside a tool call is worse than no check.

    Path.home() raises RuntimeError when it cannot resolve a home directory -
    a bare container, a stripped environment. The other targets still apply.
    """
    from pathlib import Path as _Path

    def boom() -> _Path:
        raise RuntimeError("no home")

    monkeypatch.setattr(_Path, "home", staticmethod(boom))
    policy = ApprovalPolicy(asker=_yes)

    assert (await policy(_call("run_shell", command=CATASTROPHES[0]))).allowed is False
    assert (await policy(_call("run_shell", command="rm -rf build"))).allowed is True
