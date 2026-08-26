"""The provider contract, re-exported.

Five lines that carry an argument.

The interface itself lives in `omega_agent/provider.py`, because **the consumer
owns the interface** — the loop needs *a* provider, so the loop's package defines
what a provider must look like. If this file defined it instead, the adapters
would own the shape, and the loop would have to adapt to whatever Anthropic
happened to do. That is beginner failure #7 recreated by a directory layout.

So why re-export at all? So an adapter can write `from omega_ai.provider import
ModelProvider` and read as though the contract were local, without that being
true. Tau does exactly this: `tau_ai/provider.py` is a re-export of `tau_agent`'s.

The import direction is the thing to notice. It points **down**, from `omega_ai`
into `omega_agent`, and there is no import going the other way anywhere in the
tree.
"""

from omega_agent.provider import CancellationToken, ModelProvider

__all__ = ["CancellationToken", "ModelProvider"]
