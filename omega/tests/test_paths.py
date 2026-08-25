"""Path confinement — beginner failure #4, the filesystem half.

Tier 1 could read `~/.ssh/id_rsa` and write anywhere on the disk. The fix is one
function called by every filesystem tool, because `anatomy.md:362` is blunt about
it: **one place, not per-tool.** A check repeated in four tools is a check that
will be right in three of them.

The tests below are mostly about the ways a naive implementation leaks. Each one
is a real escape, not a hypothetical:

* `startswith` says `/repo-evil` is inside `/repo`
* `resolve()` cannot follow a symlink through a directory that does not exist yet
* a `write_file` that creates parents before checking has already escaped
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from omega.paths import PathOutsideRoot, resolve_within_root


def test_a_plain_relative_path_resolves_under_the_root(tmp_path: Path) -> None:
    assert resolve_within_root("notes.txt", tmp_path) == (tmp_path.resolve() / "notes.txt")


def test_the_root_itself_is_allowed(tmp_path: Path) -> None:
    assert resolve_within_root(".", tmp_path) == tmp_path.resolve()


def test_a_nested_path_that_does_not_exist_yet_is_allowed(tmp_path: Path) -> None:
    """write_file creates parents, so the common case is a path with no parent."""
    resolved = resolve_within_root("a/b/c/new.txt", tmp_path)
    assert resolved == tmp_path.resolve() / "a" / "b" / "c" / "new.txt"


# ---------------------------------------------------------------- the escapes


def test_dot_dot_traversal_is_refused(tmp_path: Path) -> None:
    with pytest.raises(PathOutsideRoot):
        resolve_within_root("../outside.txt", tmp_path)


def test_deep_dot_dot_traversal_is_refused(tmp_path: Path) -> None:
    with pytest.raises(PathOutsideRoot):
        resolve_within_root("a/b/../../../outside.txt", tmp_path)


def test_an_absolute_path_outside_the_root_is_refused(tmp_path: Path) -> None:
    with pytest.raises(PathOutsideRoot):
        resolve_within_root("/etc/passwd", tmp_path)


def test_a_sibling_with_a_shared_prefix_is_refused(tmp_path: Path) -> None:
    """The bug `str.startswith` produces: `/repo-evil` "is inside" `/repo`."""
    root = tmp_path / "repo"
    root.mkdir()
    sibling = tmp_path / "repo-evil"
    sibling.mkdir()
    (sibling / "secret.txt").write_text("x")

    with pytest.raises(PathOutsideRoot):
        resolve_within_root(str(sibling / "secret.txt"), root)


def test_a_symlinked_file_pointing_out_is_refused(tmp_path: Path) -> None:
    root = tmp_path / "project"
    root.mkdir()
    secret = tmp_path / "secret.txt"
    secret.write_text("password")
    (root / "innocent.txt").symlink_to(secret)

    with pytest.raises(PathOutsideRoot):
        resolve_within_root("innocent.txt", root)


def test_a_symlinked_parent_directory_pointing_out_is_refused(tmp_path: Path) -> None:
    """The case a plain `resolve()` on the full path misses.

    `resolve()` cannot follow a link it never reaches, so if the *target* file
    does not exist the link in its parent is never traversed and the check
    passes. Resolving the deepest existing ancestor first is what closes it.
    """
    root = tmp_path / "project"
    root.mkdir()
    outside = tmp_path / "elsewhere"
    outside.mkdir()
    (root / "link").symlink_to(outside, target_is_directory=True)

    with pytest.raises(PathOutsideRoot):
        resolve_within_root("link/created-later.txt", root)


def test_a_broken_symlink_pointing_out_is_refused(tmp_path: Path) -> None:
    """A dangling link still declares its intent, and it may exist tomorrow."""
    root = tmp_path / "project"
    root.mkdir()
    (root / "dangling").symlink_to(tmp_path / "not-there-yet")

    with pytest.raises(PathOutsideRoot):
        resolve_within_root("dangling", root)


def test_a_root_that_is_itself_a_symlink_still_works(tmp_path: Path) -> None:
    """macOS makes this the default case: /tmp is a link to /private/tmp.

    If the root is not resolved before comparing, every path under it looks like
    an escape and the agent can touch nothing at all.
    """
    real = tmp_path / "real"
    real.mkdir()
    linked = tmp_path / "linked"
    linked.symlink_to(real, target_is_directory=True)

    assert resolve_within_root("inside.txt", linked) == real.resolve() / "inside.txt"


def test_the_error_names_the_path_and_the_root(tmp_path: Path) -> None:
    """A refusal the model can act on beats one it retries."""
    with pytest.raises(PathOutsideRoot) as caught:
        resolve_within_root("/etc/passwd", tmp_path)

    message = str(caught.value)
    assert "/etc/passwd" in message
    assert str(tmp_path.resolve()) in message


def test_it_is_a_tool_error_so_the_loop_reports_it_as_a_result(tmp_path: Path) -> None:
    """Refusal is an observation for the model, not a crash."""
    from omega.tools import ToolError

    assert issubclass(PathOutsideRoot, ToolError)


@pytest.mark.skipif(os.name == "nt", reason="POSIX path semantics")
def test_a_path_with_a_null_byte_is_refused(tmp_path: Path) -> None:
    with pytest.raises(PathOutsideRoot):
        resolve_within_root("ok\x00/../../etc/passwd", tmp_path)
