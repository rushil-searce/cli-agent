"""What goes on a line of a session file.

Two record kinds, discriminated by `kind`, so one append-only file can hold both
the session's metadata and its messages without a second file to keep in sync.

**`parent_id` is on every entry even though Tier 2 only ever writes a straight
line.** `anatomy.md:314` gives the reason without hedging: "Retrofitting a tree
onto a list is a rewrite." Tier 3 adds branching by writing a different
`parent_id`, not by changing the format of files already on disk.

**`version` is on every record.** It is what makes `migrate on read` possible at
all. A file written today has to be loadable by an omega that has changed its
mind about the schema, and that is only true if the file says which schema it is.
"""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import Field

from omega_agent.types import AgentMessage, WireModel

#: Bumped whenever a record shape changes. `jsonl.py` migrates anything older.
SCHEMA_VERSION = 1


class SessionHeader(WireModel):
    """The first line of a session file. Written once, never updated."""

    kind: Literal["header"] = "header"
    version: int = SCHEMA_VERSION
    session_id: str
    created_at: str
    model: str


class SessionEntry(WireModel):
    """One message in the transcript, and where it hangs from."""

    kind: Literal["entry"] = "entry"
    version: int = SCHEMA_VERSION
    id: str
    parent_id: str | None = None
    message: AgentMessage


SessionRecord = Annotated[SessionHeader | SessionEntry, Field(discriminator="kind")]
