"""Secret redaction — anatomy.md #32.

The agent reads files and runs commands. `cat .env` and `env` both produce
credentials, and Tier 1 put whatever came back straight into the transcript —
which goes to the provider, and from Step 5 onto disk.

This is not containment; a determined model can encode its way past any pattern
list. It is the difference between *casually* leaking a key into a session log
you later paste into a bug report, and not doing that.

Filling `after_tool_call` means the loop gains nothing from it, same as the gate.
"""

from __future__ import annotations

import pytest

from omega.redact import redact


@pytest.mark.parametrize(
    ("label", "secret"),
    [
        ("anthropic", "sk-ant-api03-AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"),
        ("openai", "sk-proj-BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB"),
        ("github", "ghp_CCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC"),
        ("aws", "AKIAIOSFODNN7EXAMPLE"),
        ("slack", "xoxb-123456789012-ABCDEFGHIJKLMNOPQRSTUVWX"),
        ("google", "AIzaSyDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDD"),
    ],
)
def test_known_key_shapes_are_masked(label: str, secret: str) -> None:
    cleaned, found = redact(f"the key is {secret} ok")

    assert secret not in cleaned
    assert "[redacted" in cleaned
    assert found, f"{label} was not reported"


def test_a_private_key_block_is_masked() -> None:
    text = "-----BEGIN RSA PRIVATE KEY-----\nMIIEowIBAAKCAQ\n-----END RSA PRIVATE KEY-----"
    cleaned, found = redact(text)

    assert "MIIEowIBAAKCAQ" not in cleaned
    assert found


def test_an_env_assignment_keeps_the_name_and_hides_the_value() -> None:
    """The name is the useful part: the model should know the variable is set."""
    cleaned, found = redact("ANTHROPIC_API_KEY=sk-ant-xyzxyzxyzxyzxyzxyz\nPATH=/usr/bin")

    assert "ANTHROPIC_API_KEY" in cleaned, "the model still needs to know it exists"
    assert "sk-ant-xyzxyzxyzxyzxyzxyz" not in cleaned
    assert "PATH=/usr/bin" in cleaned, "ordinary variables must survive"
    assert found


def test_a_bearer_header_is_masked() -> None:
    cleaned, _found = redact("Authorization: Bearer abcdefghijklmnopqrstuvwxyz123456")

    assert "abcdefghijklmnopqrstuvwxyz123456" not in cleaned
    assert "Bearer" in cleaned


def test_ordinary_output_is_returned_untouched() -> None:
    """False positives cost real work: a mangled diff is a broken tool."""
    text = "def add(a, b):\n    return a + b\n\n5 passed in 0.42s\n"
    cleaned, found = redact(text)

    assert cleaned == text
    assert found == []


def test_it_says_what_it_hid_without_repeating_the_secret() -> None:
    cleaned, found = redact("token: ghp_EEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEE")

    report = " ".join(found)
    assert "GitHub" in report
    assert "ghp_E" not in report, "the report must not leak what it redacted"
    assert "ghp_E" not in cleaned


def test_several_secrets_in_one_blob_are_all_masked() -> None:
    text = (
        "AWS_SECRET=AKIAIOSFODNN7EXAMPLE\n"
        "GH=ghp_FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF\n"
        "harmless=yes\n"
    )
    cleaned, found = redact(text)

    assert "AKIAIOSFODNN7EXAMPLE" not in cleaned
    assert "ghp_F" not in cleaned
    assert "harmless=yes" in cleaned
    assert len(found) >= 2


# ------------------------------------------------------ it plugs into the loop


async def test_a_leaked_key_never_reaches_the_transcript() -> None:
    """End to end through the hook, which is the only thing that matters."""
    from typing import Any

    from omega.harness import Harness
    from omega.hooks import AgentHooks
    from omega.providers.fake import FakeProvider, text_turn, tool_turn
    from omega.redact import redacting_hook
    from omega.tools import Tool, ToolResult
    from omega.types import ToolResultMessage

    async def leaky(arguments: dict[str, Any], signal: Any) -> ToolResult:
        return ToolResult(content="ANTHROPIC_API_KEY=sk-ant-api03-LEAKEDLEAKEDLEAKEDLEAKED")

    tool = Tool(name="env", description="d", parameters={"type": "object"}, execute=leaky)
    harness = Harness(
        provider=FakeProvider([tool_turn("env", {}), text_turn("ok")]),
        model="m",
        system="s",
        tools=[tool],
        hooks=AgentHooks(after_tool_call=redacting_hook),
    )

    async for _event in harness.run("show me the env"):
        pass

    result = next(m for m in harness.messages if isinstance(m, ToolResultMessage))
    assert "sk-ant-api03-LEAKED" not in result.text
    assert "ANTHROPIC_API_KEY" in result.text
