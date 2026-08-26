"""One lock per file — beginner failure #8.

Two edits to one file, both reading the original and both writing it back: the
second silently discards the first. No error, no warning, just missing work.

Both references ship a lock keyed on the resolved path, and Tau keeps it even
though its loop runs tools sequentially. Worth copying that judgement: the lock
costs a dictionary lookup, and the day tool calls run in parallel it is the
difference between a fast agent and a lossy one.

**Keyed on the resolved path, not the string the model typed.** `notes.txt`,
`./notes.txt`, and a symlink named `alias.txt` are one file. Handing out three
locks for one file is indistinguishable from having none.
"""

from __future__ import annotations

import asyncio
from pathlib import Path


class FileLocks:
    """A lock per file, created on first use.

    Locks are never evicted. That is a deliberate non-problem: the key is one
    `Path` per file the agent has touched in this session, which is bounded by
    how much work a person does in a sitting.
    """

    __slots__ = ("_locks",)

    def __init__(self) -> None:
        self._locks: dict[Path, asyncio.Lock] = {}

    def for_path(self, path: Path) -> asyncio.Lock:
        """The lock for one file. Same file, same lock, whatever it was called."""
        key = self._resolve(path)
        lock = self._locks.get(key)
        if lock is None:
            lock = asyncio.Lock()
            self._locks[key] = lock
        return lock

    @staticmethod
    def _resolve(path: Path) -> Path:
        try:
            return path.resolve()
        except (OSError, ValueError):
            # Unresolvable paths still deserve consistent locking; the tools will
            # refuse them a moment later on their own merits.
            return path


#: Shared by the built-in file tools, so `write_file` and `edit_file` contend on
#: the same lock. Two independent lock tables would be two independent illusions
#: of safety.
FILE_LOCKS = FileLocks()
