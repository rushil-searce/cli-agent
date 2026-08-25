"""omega_coding — Layers 3 and 4, the application.

Everything that knows what a file is, what a shell is, or what a screen is. The
four tools, the fence around them, the approval gate, the redactor, the two
gauges, the headless driver, the smoke eval, and the REPL.

The division that decides what lives here rather than in `omega_agent`:

    the seam is core, the policy is application

`hooks.py` is Layer 2 because the loop declares the callbacks it will consult.
Everything that *fills* one of those callbacks — `approval.py`, `redact.py`,
`history.py` — is Layer 3, because each is a *decision*, and the loop asks rather
than decides.

`cli.py` is the composition root, and the only file in the whole tree that names
a concrete provider.
"""
