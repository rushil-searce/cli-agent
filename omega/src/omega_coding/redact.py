"""Keep credentials out of the transcript — anatomy.md #32.

The agent reads files and runs commands, so `cat .env` is one normal turn away.
Tier 1 put whatever came back straight into the conversation, which means it went
to the provider — and from Step 5 it would go onto disk too.

**This is not containment.** A model that wants to exfiltrate a key can encode it
first, and no pattern list stops that. What this buys is the ordinary case: not
*casually* pasting a live key into a session log that later ends up in a bug
report or a screen share.

Fills `after_tool_call`, so the loop gains nothing from it — same as the gate.

Two ordering decisions matter:

1. **Specific key shapes run before the generic `NAME=value` rule.** Otherwise
   `token: ghp_...` gets reported as "a value called token" and the fact that it
   was a *GitHub* token — the useful part — is lost.
2. **The variable name survives.** `ANTHROPIC_API_KEY=[redacted]` tells the model
   the key is set, which is usually what it was checking. Masking the whole line
   would just send it looking again.
"""

from __future__ import annotations

import re

from omega_agent.tools import ToolResult
from omega_agent.types import ToolCall

#: Specific, high-confidence shapes. Anthropic is listed before OpenAI because
#: the OpenAI pattern would otherwise swallow `sk-ant-...` and mislabel it.
_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("Anthropic API key", re.compile(r"sk-ant-[A-Za-z0-9_\-]{16,}")),
    ("OpenAI API key", re.compile(r"sk-(?:proj-)?[A-Za-z0-9_\-]{20,}")),
    ("GitHub token", re.compile(r"gh[pousr]_[A-Za-z0-9]{20,}")),
    ("AWS access key id", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("Slack token", re.compile(r"xox[baprse]-[A-Za-z0-9-]{10,}")),
    # Real Google keys are AIza + 35 chars, but the prefix is distinctive enough
    # that a loose bound costs nothing and an exact one silently misses variants.
    ("Google API key", re.compile(r"\bAIza[0-9A-Za-z_\-]{20,}")),
    (
        "private key block",
        re.compile(r"-----BEGIN[^\n]*PRIVATE KEY-----.*?-----END[^\n]*-----", re.DOTALL),
    ),
)

#: `Authorization: Bearer <token>`. The scheme is kept; the token is not.
_BEARER = re.compile(r"\b(bearer)(\s+)[A-Za-z0-9._\-]{20,}", re.IGNORECASE)

#: The catch-all: any assignment whose *name* says it holds a secret. Runs last,
#: so anything recognisable has already been labelled properly.
# The `indent` group exists so an indented line keeps its indentation. Without
# it, redacting a key inside a YAML block would silently reformat the file the
# model is looking at.
_ENV_ASSIGNMENT = re.compile(
    r"(?im)^(?P<indent>[ \t]*)(?P<name>[A-Za-z0-9_]*"
    r"(?:SECRET|TOKEN|PASSWORD|PASSWD|API_?KEY|APIKEY|CREDENTIAL|PRIVATE_KEY)"
    r"[A-Za-z0-9_]*)(?P<sep>\s*[=:]\s*)(?P<value>\S+)"
)


def redact(text: str) -> tuple[str, list[str]]:
    """Return the text with credentials masked, and what kinds were found.

    The report deliberately contains no part of the secret — a log line reading
    "redacted ghp_EEEE..." would defeat the entire exercise.
    """
    found: list[str] = []
    cleaned = text

    for label, pattern in _PATTERNS:
        if pattern.search(cleaned):
            found.append(label)
            cleaned = pattern.sub(f"[redacted {label}]", cleaned)

    if _BEARER.search(cleaned):
        found.append("bearer token")
        cleaned = _BEARER.sub(r"\1\2[redacted bearer token]", cleaned)

    if _ENV_ASSIGNMENT.search(cleaned):
        found.append("secret-looking environment value")
        cleaned = _ENV_ASSIGNMENT.sub(r"\g<indent>\g<name>\g<sep>[redacted]", cleaned)

    return cleaned, found


async def redacting_hook(call: ToolCall, result: ToolResult) -> ToolResult:
    """`after_tool_call`: mask anything credential-shaped on the way out.

    What was hidden is recorded in `details`, which goes to a UI and not to the
    model — so a user can see that redaction happened without the transcript
    itself carrying the secret.
    """
    cleaned, found = redact(result.text)
    if not found:
        return result

    details = dict(result.details or {})
    details["redacted"] = found
    return ToolResult(content=cleaned, details=details)  # type: ignore[arg-type]
