"""Append-only storage, and migrate-on-read.

Two decisions, both about what happens when things go wrong rather than when
they go right.

**Append-only.** The alternative — hold the transcript in memory and rewrite the
file — loses the entire session if the process dies during the write. Appending
loses at most a partial final line. That is a real difference, because the
process dying unexpectedly is precisely the event persistence exists to survive.

The consequence is that **the reader must tolerate a broken last line.** A
truncated record is the normal shape of a crashed session, not corruption, and a
loader that refuses it destroys the thing it was protecting.

**Migrate on read.** The schema will change. If old files are rejected, every
format change is a data-loss event; if they are migrated, it is a function.
`_MIGRATIONS` ships with one real entry, because a versioning mechanism added
*after* files exist cannot help those files.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

from pydantic import TypeAdapter, ValidationError

from omega_agent.session.entries import SCHEMA_VERSION, SessionRecord

_ADAPTER: TypeAdapter[SessionRecord] = TypeAdapter(SessionRecord)


def _v0_to_v1(raw: dict[str, Any]) -> dict[str, Any]:
    """v0 had no `kind` discriminator: every line was an entry."""
    migrated = dict(raw)
    migrated.setdefault("kind", "entry")
    migrated["version"] = 1
    return migrated


#: Keyed by the version being migrated *from*. Applied in sequence, so a v0 file
#: walks forward through every step rather than needing a v0-to-latest special case.
_MIGRATIONS: dict[int, Callable[[dict[str, Any]], dict[str, Any]]] = {0: _v0_to_v1}


def _migrate(raw: dict[str, Any]) -> dict[str, Any]:
    version = raw.get("version", 0)
    if not isinstance(version, int):
        version = 0
    while version < SCHEMA_VERSION:
        step = _MIGRATIONS.get(version)
        if step is None:
            break
        raw = step(raw)
        next_version = raw.get("version", version + 1)
        version = next_version if isinstance(next_version, int) else version + 1
    return raw


def append_record(path: Path, record: SessionRecord) -> None:
    """Add one line. Existing bytes are never touched."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(record.model_dump_json() + "\n")


def read_records(path: Path) -> list[SessionRecord]:
    """Every record the file holds, skipping any it cannot make sense of.

    Skipping rather than raising is deliberate, and it is not laziness: one bad
    line must not cost the other nine hundred. A missing file is an empty
    session, not an error — asking to resume something that was never written is
    a reasonable thing for a user to do by accident.
    """
    if not path.exists():
        return []

    records: list[SessionRecord] = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        try:
            raw = json.loads(stripped)
        except json.JSONDecodeError:
            # The normal shape of a crash mid-append. Nothing after it either.
            continue
        if not isinstance(raw, dict):
            continue
        try:
            records.append(_ADAPTER.validate_python(_migrate(raw)))
        except ValidationError:
            # Written by something that disagrees with us about the schema, and
            # no migration covers it. Better one lost message than no session.
            continue

    return records
