"""omega_agent — Layer 2, the portable core.

The loop, the harness, the two event vocabularies, the message model, and the
provider *contract*. What it knows about: messages, events, tools, turns.

What it does not know about, and must never learn: **files, shells, terminals,
and vendors.** Those are `omega_coding` and `omega_ai` respectively, and both of
them import this package rather than the other way round.

`provider.py` living here is the point of the whole arrangement. The consumer
defines the interface and adapters conform to it — reverse that and Anthropic's
shape becomes the shape of the system. `omega_ai/provider.py` is a re-export, so
adapters can import from their own package without owning the contract, which is
exactly what Tau does.

`tests/test_layers.py` enforces all of this rather than trusting it.
"""

__version__ = "0.2.0"
