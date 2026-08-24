"""Session persistence — the subsystem that earns Tier 2 its one new folder.

`docs/04-folder-trees.md:44`: Tau's entire agent core has exactly one subfolder,
and it is this one. Folders follow subsystems, and this is the first thing in
omega big enough to be one — a record format, a storage mechanism, and a seam
between them.
"""

from omega.session.entries import (
    SCHEMA_VERSION,
    SessionEntry,
    SessionHeader,
    SessionRecord,
)
from omega.session.jsonl import append_record, read_records
from omega.session.store import JsonlSessionStore, SessionStore

__all__ = [
    "SCHEMA_VERSION",
    "JsonlSessionStore",
    "SessionEntry",
    "SessionHeader",
    "SessionRecord",
    "SessionStore",
    "append_record",
    "read_records",
]
