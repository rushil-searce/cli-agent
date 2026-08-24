"""Where sessions live.

A `Protocol` plus one implementation, so the backend can change without the
harness noticing. Pi eventually moves to SQLite for cross-session search; JSONL
is the right size for Tier 2 and the interface is what makes that later swap an
addition rather than surgery.

Sessions land in `<root>/.omega/sessions/<id>.jsonl` — beside the project, so a
transcript travels with the work it is about.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Protocol

from omega.session.entries import SessionEntry, SessionHeader
from omega.session.jsonl import append_record, read_records
from omega.types import AgentMessage


class SessionStore(Protocol):
    """The storage seam. Four methods, all the harness needs."""

    def create_session(self, *, model: str) -> str:
        """Start a session and return its id."""
        ...

    def append(self, session_id: str, message: AgentMessage) -> None:
        """Add one message to the end of a session."""
        ...

    def load(self, session_id: str) -> list[AgentMessage]:
        """Every message in a session, in order. Empty if it does not exist."""
        ...

    def latest_session_id(self) -> str | None:
        """The most recently written session, for `--resume`."""
        ...


class JsonlSessionStore:
    """One append-only JSONL file per session."""

    def __init__(self, root: Path) -> None:
        self.directory = Path(root) / ".omega" / "sessions"

        #: The id of the last entry written per session, so the next one can point
        #: at it. Populated lazily on append, because a resumed session was
        #: written by a different process and this store has never seen its tail.
        self._last_entry: dict[str, str | None] = {}

    def path_for(self, session_id: str) -> Path:
        return self.directory / f"{session_id}.jsonl"

    def create_session(self, *, model: str) -> str:
        # Timestamp-first so the directory sorts chronologically for a human
        # reading it with `ls`; the random suffix keeps two sessions started in
        # the same second apart.
        stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S")
        session_id = f"{stamp}-{uuid.uuid4().hex[:6]}"

        append_record(
            self.path_for(session_id),
            SessionHeader(
                session_id=session_id,
                created_at=datetime.now(UTC).isoformat(),
                model=model,
            ),
        )
        self._last_entry[session_id] = None
        return session_id

    def append(self, session_id: str, message: AgentMessage) -> None:
        entry = SessionEntry(
            id=uuid.uuid4().hex[:12],
            parent_id=self._parent_for(session_id),
            message=message,
        )
        append_record(self.path_for(session_id), entry)
        self._last_entry[session_id] = entry.id

    def load(self, session_id: str) -> list[AgentMessage]:
        return [
            record.message
            for record in read_records(self.path_for(session_id))
            if isinstance(record, SessionEntry)
        ]

    def latest_session_id(self) -> str | None:
        if not self.directory.exists():
            return None
        files = list(self.directory.glob("*.jsonl"))
        if not files:
            return None
        # Nanosecond mtime, because two sessions in the same second are common
        # and a whole-second comparison would pick arbitrarily between them.
        return max(files, key=lambda path: path.stat().st_mtime_ns).stem

    def _parent_for(self, session_id: str) -> str | None:
        if session_id in self._last_entry:
            return self._last_entry[session_id]

        # Never seen this session: read its tail to find where to hang the next
        # entry. Happens exactly once per resumed session.
        records = read_records(self.path_for(session_id))
        entries = [r for r in records if isinstance(r, SessionEntry)]
        last = entries[-1].id if entries else None
        self._last_entry[session_id] = last
        return last
