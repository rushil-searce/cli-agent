"""The four file/shell tools.

Every test builds its tools rooted at `tmp_path`. That is not test hygiene — it
is the point of the factory. Tier 1's module-level constants captured the
current directory at import, which meant a test could not choose its own fence
and `--fake` in a temp directory got the wrong one.
"""

from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from omega_agent.tools import Tool, ToolError
from omega_coding.builtin_tools import build_tools
from omega_coding.paths import PathOutsideRoot


def _tools(root: Path, **kwargs: object) -> dict[str, Tool]:
    return {tool.name: tool for tool in build_tools(root, **kwargs)}  # type: ignore[arg-type]


# ------------------------------------------------------------------ read/write


async def test_read_file_returns_contents(tmp_path: Path) -> None:
    (tmp_path / "hello.txt").write_text("contents here", encoding="utf-8")

    result = await _tools(tmp_path)["read_file"].execute({"path": "hello.txt"}, None)
    assert result.text == "contents here"


async def test_read_file_raises_a_message_the_model_can_act_on(tmp_path: Path) -> None:
    with pytest.raises(ToolError) as excinfo:
        await _tools(tmp_path)["read_file"].execute({"path": "nope.txt"}, None)

    assert "not found" in str(excinfo.value).lower()


async def test_write_file_creates_parent_directories(tmp_path: Path) -> None:
    result = await _tools(tmp_path)["write_file"].execute(
        {"path": "nested/deep/out.txt", "content": "written"}, None
    )

    assert (tmp_path / "nested" / "deep" / "out.txt").read_text(encoding="utf-8") == "written"
    assert "7 chars" in result.text


# ------------------------------------------------------ confinement, in the tools


async def test_read_file_refuses_to_escape_the_root(tmp_path: Path) -> None:
    """failure #4: Tier 1 could read ~/.ssh/id_rsa."""
    (tmp_path / "secret.txt").write_text("password")
    root = tmp_path / "project"
    root.mkdir()

    with pytest.raises(PathOutsideRoot):
        await _tools(root)["read_file"].execute({"path": "../secret.txt"}, None)


async def test_write_file_refuses_to_escape_the_root(tmp_path: Path) -> None:
    root = tmp_path / "project"
    root.mkdir()

    with pytest.raises(PathOutsideRoot):
        await _tools(root)["write_file"].execute(
            {"path": "../escaped.txt", "content": "x"}, None
        )

    assert not (tmp_path / "escaped.txt").exists()


async def test_a_refused_write_creates_no_directories(tmp_path: Path) -> None:
    """Tier 1 ran mkdir(parents=True) before any check.

    A refusal that has already created `../a/b/c` on the way to being refused is
    not a refusal. Confinement has to gate the mkdir, not just the write.
    """
    root = tmp_path / "project"
    root.mkdir()

    with pytest.raises(PathOutsideRoot):
        await _tools(root)["write_file"].execute(
            {"path": "../outside/a/b/c.txt", "content": "x"}, None
        )

    assert not (tmp_path / "outside").exists(), "directories were created outside the root"


async def test_each_root_gets_its_own_fence(tmp_path: Path) -> None:
    """Two roots in one process — impossible with import-time constants."""
    one = tmp_path / "one"
    two = tmp_path / "two"
    one.mkdir()
    two.mkdir()
    (one / "a.txt").write_text("from one")
    (two / "a.txt").write_text("from two")

    assert (await _tools(one)["read_file"].execute({"path": "a.txt"}, None)).text == "from one"
    assert (await _tools(two)["read_file"].execute({"path": "a.txt"}, None)).text == "from two"


# ----------------------------------------------------------------------- shell


async def test_run_shell_returns_combined_output(tmp_path: Path) -> None:
    result = await _tools(tmp_path)["run_shell"].execute(
        {"command": "echo out; echo err 1>&2"}, None
    )

    assert "out" in result.text
    assert "err" in result.text, "stderr must be captured too"


async def test_failing_command_carries_its_output_into_the_error(tmp_path: Path) -> None:
    """A bare 'exited with code 1' tells the model nothing and it retries blindly."""
    with pytest.raises(ToolError) as excinfo:
        await _tools(tmp_path)["run_shell"].execute(
            {"command": "echo why-it-failed; exit 3"}, None
        )

    message = str(excinfo.value)
    assert "why-it-failed" in message, "the output is the useful part of the failure"
    assert "code 3" in message


async def test_the_shell_starts_in_the_root(tmp_path: Path) -> None:
    result = await _tools(tmp_path)["run_shell"].execute({"command": "pwd"}, None)
    assert str(tmp_path.resolve()) in result.text


async def test_a_hung_command_is_killed(tmp_path: Path) -> None:
    """A TIER-1.md rough edge: run_shell had no timeout, so a hang was forever."""
    with pytest.raises(ToolError) as excinfo:
        await _tools(tmp_path, timeout=0.3)["run_shell"].execute({"command": "sleep 30"}, None)

    assert "timed out" in str(excinfo.value)


async def test_a_running_command_honours_cancellation(tmp_path: Path) -> None:
    """Ctrl-C during a long command should not mean waiting out the timeout."""
    from omega_agent.cancellation import CancelSignal

    signal = CancelSignal()

    async def cancel_shortly() -> None:
        await asyncio.sleep(0.2)
        signal.cancel()

    asyncio.ensure_future(cancel_shortly())

    with pytest.raises(ToolError) as excinfo:
        await _tools(tmp_path, timeout=30.0)["run_shell"].execute(
            {"command": "sleep 30"}, signal
        )

    assert "Cancelled" in str(excinfo.value)


async def test_the_prepare_seam_can_rewrite_a_command(tmp_path: Path) -> None:
    """The hole a Tier 3+ sandbox slots into, with no other file changing."""
    tools = _tools(tmp_path, prepare_shell=lambda command: f"echo wrapped: $({command})")

    result = await tools["run_shell"].execute({"command": "echo inner"}, None)
    assert "wrapped: inner" in result.text


# ---------------------------------------------------------------- descriptions


async def test_tool_descriptions_state_the_budget_they_enforce(tmp_path: Path) -> None:
    """The model is told the constraint it will be subject to."""
    tools = _tools(tmp_path)
    for name in ("read_file", "run_shell"):
        assert "truncated" in tools[name].description.lower()


async def test_file_tool_descriptions_state_the_confinement(tmp_path: Path) -> None:
    tools = _tools(tmp_path)
    for name in ("read_file", "write_file", "edit_file"):
        assert "working directory" in tools[name].description


async def test_descriptions_have_no_run_together_sentences(tmp_path: Path) -> None:
    """The model reads these. A missing space after a full stop is a real defect."""
    for tool in build_tools(tmp_path):
        for glued in (".W", ".P", ".C", ".O"):
            assert glued not in tool.description, f"{tool.name}: {glued}"


async def test_schemas_are_well_formed(tmp_path: Path) -> None:
    for tool in build_tools(tmp_path):
        assert tool.parameters["type"] == "object"
        assert "properties" in tool.parameters
        for name in tool.parameters.get("required", []):
            assert name in tool.parameters["properties"]


async def test_there_are_four_tools_now(tmp_path: Path) -> None:
    assert sorted(t.name for t in build_tools(tmp_path)) == [
        "edit_file",
        "read_file",
        "run_shell",
        "write_file",
    ]
