"""Per-path write serialization — beginner failure #8.

Two edits to one file, both reading the original and both writing: the second
silently discards the first. Both references ship a lock per resolved path, and
Tau keeps it even though its loop is sequential.

The lock is only load-bearing because the file tools do their I/O in a thread
(`asyncio.to_thread`). That is worth doing on its own merits — a synchronous
`read_text` on a large file blocks the whole event loop — but it is also what
makes the race real rather than theoretical, and therefore what makes the lock
something other than decoration.
"""

from __future__ import annotations

import asyncio
from pathlib import Path

from omega.file_lock import FileLocks


async def test_the_same_path_serialises() -> None:
    locks = FileLocks()
    order: list[str] = []

    async def worker(name: str) -> None:
        async with locks.for_path(Path("/tmp/same")):
            order.append(f"{name}-in")
            await asyncio.sleep(0)  # a chance to interleave, if it could
            order.append(f"{name}-out")

    await asyncio.gather(worker("a"), worker("b"))

    assert order == ["a-in", "a-out", "b-in", "b-out"]


async def test_different_paths_do_not_block_each_other() -> None:
    """A global lock would be correct and needlessly slow."""
    locks = FileLocks()
    order: list[str] = []

    async def worker(name: str, path: str) -> None:
        async with locks.for_path(Path(path)):
            order.append(f"{name}-in")
            await asyncio.sleep(0)
            order.append(f"{name}-out")

    await asyncio.gather(worker("a", "/tmp/one"), worker("b", "/tmp/two"))

    assert order == ["a-in", "b-in", "a-out", "b-out"], "these should interleave"


async def test_the_same_file_reached_by_two_names_shares_one_lock(tmp_path: Path) -> None:
    """Keyed on the *resolved* path.

    `notes.txt` and `./notes.txt` and a symlink to it are one file. Keying on the
    string the model happened to type would hand out two locks for one file,
    which is the same as having none.
    """
    target = tmp_path / "notes.txt"
    target.write_text("x")
    link = tmp_path / "alias.txt"
    link.symlink_to(target)

    locks = FileLocks()
    assert locks.for_path(target) is locks.for_path(link)
    assert locks.for_path(target) is locks.for_path(tmp_path / "." / "notes.txt")


async def test_a_lock_is_reused_not_recreated() -> None:
    locks = FileLocks()
    first = locks.for_path(Path("/tmp/x"))
    assert locks.for_path(Path("/tmp/x")) is first
