"""Path confinement — one function, called by every filesystem tool.

Tier 1 could read `~/.ssh/id_rsa` and write anywhere on the disk. This is half
the fix for beginner failure **#4** (the approval gate in Step 4 is the other
half, and covers the shell, which no amount of path checking can confine).

`anatomy.md:362` is blunt about the shape: **one place, not per-tool.** A check
copied into four tools is a check that will be correct in three of them, and the
fourth is the one the model finds. So the tools do not validate paths; they call
this and use what comes back.

Three implementations of this idea are wrong in ways that look right:

1. **`str.startswith`** — `/repo-evil` starts with `/repo`.
2. **Comparing before resolving** — `project/../../etc/passwd` is inside
   `project` until you normalise it.
3. **`Path.resolve()` on the whole path** — it cannot follow a symlink it never
   reaches. `project/link/new.txt`, where `link` points outside and `new.txt`
   does not exist yet, resolves without ever traversing `link`. Since
   `write_file` exists precisely to create files that are not there, this is the
   common case, not the exotic one.

The third is why this file is longer than a one-liner.
"""

from __future__ import annotations

import os
from pathlib import Path

from omega.tools import ToolError


class PathOutsideRoot(ToolError):
    """A tool was asked to touch something outside the working directory.

    A `ToolError`, so the loop turns it into a tool result the model reads and
    adapts to. A refusal is an observation, not a crash — and one that names the
    path and the root is a refusal the model can act on instead of retrying.
    """


def resolve_within_root(candidate: str | Path, root: Path) -> Path:
    """Resolve `candidate` and return it, or raise if it lands outside `root`.

    The returned path is fully resolved, which makes it the right key for
    `FileLocks` as well: two names for one file must share one lock.
    """
    resolved_root = root.resolve()

    # Checked explicitly because pathlib will not do it for us: `Path.exists()`
    # swallows the ValueError that a null byte raises and simply returns False,
    # so an embedded null would slip through the walk below unnoticed.
    if "\x00" in str(candidate):
        raise PathOutsideRoot(f"Refused: {candidate!r} contains a null byte.")

    raw = Path(candidate)
    target = raw if raw.is_absolute() else resolved_root / raw

    try:
        resolved = _resolve_through_existing(target)
    except (OSError, ValueError) as exc:
        # A null byte, a path too long, a loop of symlinks. Unusable either way,
        # and refusing is the honest answer.
        raise PathOutsideRoot(f"Refused: {candidate!r} is not a usable path ({exc}).") from exc

    try:
        resolved.relative_to(resolved_root)
    except ValueError as exc:
        raise PathOutsideRoot(
            f"Refused: {candidate} resolves to {resolved}, which is outside the working "
            f"directory {resolved_root}. omega only reads and writes inside it."
        ) from exc

    return resolved


def _resolve_through_existing(target: Path) -> Path:
    """Resolve the deepest ancestor that exists, then re-append the rest.

    This is the part that closes the symlinked-parent hole. Walking up to
    something real forces every link along the way to be followed; the tail that
    does not exist yet is then appended to wherever that really was.

    A symlink is treated as existing even when it dangles. A link pointing
    outside the root has declared its intent, and the file it points at may be
    created a moment later.
    """
    remainder: list[str] = []
    probe = target

    while not (probe.exists() or probe.is_symlink()):
        parent = probe.parent
        if parent == probe:  # reached the filesystem root
            break
        remainder.append(probe.name)
        probe = parent

    resolved = probe.resolve()
    for name in reversed(remainder):
        resolved = resolved / name

    # The remainder can contain `..` of its own — `a/b/../../../outside.txt`
    # walks all the way up to an existing ancestor and carries every component
    # back with it. Collapsing those lexically is safe *here* precisely because
    # these components did not exist when probed, and a path that does not exist
    # cannot be a symlink. Without this the `..` survives into the comparison and
    # the path looks like it is inside the root.
    return Path(os.path.normpath(resolved))
