# omega

A terminal coding agent, built from scratch in layers.

Named after a physics letter, following [Pi](https://github.com/earendil-works/pi) and
[Tau](https://github.com/huggingface/tau) — the two MIT-licensed agents this is studied from.
Written independently, not forked.

**Currently at Tier 2 — "it is usable."** 4,644 lines of source, 289 tests, all offline.

* [`TIER-1.md`](TIER-1.md) — what the first tier does, and what it deliberately left out
* [`TIER-2.md`](TIER-2.md) — what this tier adds, and where each remaining gap plugs in at Tier 3

Tier 1 proved the loop terminates. Tier 2 makes it safe to point at a real repository: it can be
interrupted without corrupting the conversation, it remembers across restarts, it asks before it
destroys anything, and its provider abstraction is no longer a claim but a measured result.

## Run it

```bash
uv sync

uv run omega --fake                 # scripted responses — no key, no network, no credits
uv run omega                        # Anthropic; needs ANTHROPIC_API_KEY in ../.env
uv run omega --provider openai      # OpenAI Chat Completions
uv run omega --resume               # continue the most recent session here
```

`--fake` is not a stub. It drives the entire agent — loop, harness, tools, streaming, approvals —
through `FakeProvider`, so you can watch the whole thing work without spending anything.

Useful flags: `--yes` approves tool calls automatically (it does **not** disable the
refuse-outright list), `--no-save` skips writing a session, `--session ID` resumes a specific one,
and `--base-url` points the OpenAI adapter at a local server:

```bash
uv run omega --provider openai --base-url http://localhost:11434/v1   # Ollama, free
```

Drop an `OMEGA.md` in the working directory and its contents are appended to the system prompt,
so project conventions stop being something you retype.

## Check it

```bash
uv run pytest -q                    # 289 tests, ~1.7s, fully offline
uv run mypy --strict src
uv run ruff check .
uv run python -m omega.evals        # smoke eval: does the assembled agent still work?
```

The test suite never touches the network. Every provider call is faked at the interface boundary —
which is why `providers/fake.py` was written before the real adapter — and the two vendor SDKs are
faked one layer lower, in `tests/stub_anthropic.py` and `tests/stub_openai.py`, so the adapters'
own retry and auth behaviour is testable too.

The **smoke eval** is deliberately not a test. The tests check units; the eval checks the
assembled agent against a task. It catches the class of breakage where every unit passes and the
whole thing still does nothing.

## Layout

```
src/omega/
├── types.py          neutral messages and content blocks
├── events.py         the 12 stream events    — Layer 1's vocabulary
├── agent_events.py   the 10 agent events     — Layer 2's vocabulary
├── provider.py       the interface. The core owns it; adapters conform.
├── providers/
│   ├── fake.py       scripted replay. Written first, on purpose.
│   ├── retry.py      backoff — invisible above this layer
│   ├── anthropic.py  one wire format
│   └── openai.py     a different one. Also Groq, Together, Ollama, vLLM.
├── hooks.py          the seams. Six of Pi's nine.
├── loop.py           the agent loop. 190 lines, and it should not grow.
├── tool_runner.py    one tool call to one tool result
├── harness.py        owns the transcript, the queues, and cancellation
├── cancellation.py   a token you can actually set
├── history.py        two views of history — what is kept vs what is sent
├── context.py        how full the window is (measures failure #1)
├── cost.py           token totals; dollars only if you supply a price
├── tools.py          Tool and ToolResult
├── truncate.py       output budget: 2,000 lines / 50 KB, tail-biased
├── paths.py          confinement. ONE place, not per-tool.
├── file_lock.py      one lock per resolved path
├── approval.py       the gate. Fills before_tool_call.
├── redact.py         keeps credentials out of the transcript
├── builtin_tools.py  read, write, edit, run — behind all of the above
├── session/          append-only JSONL, migrate-on-read, parent_id on entries
├── headless.py       prompt in, transcript out. No keyboard.
├── evals.py          the smoke eval
└── cli.py            print-based REPL. Not a TUI — that would still hide bugs.
```

`session/` is the only subdirectory Tier 2 earned. Folders follow subsystems, and it is the first
thing here big enough to be one — which is also true of Tau, whose entire agent core has exactly
one subfolder, and it is this one.

### The check that the layering held

**Which files import a vendor SDK:**

```bash
grep -rln --include='*.py' -E '^(from|import) (anthropic|openai)' src/omega/
```

should print exactly two paths, both under `providers/`.

This is deliberately narrower than "which files mention a vendor". `cli.py` imports
`omega.providers.anthropic` — our module, not the SDK — because something has to choose a concrete
provider, and that job belongs to the composition root. The leak would be a *core* module
importing an SDK, and none does.

The stronger version of the same check is in the git history. Adding the second provider — a
genuinely different wire format, with the opposite rule about how tool results are sent — required
changes to `providers/`, its tests, and a few lines of provider selection in `cli.py`. Nothing
else moved: not the loop, not the interface, not either event vocabulary. `git show ac0e370` has
the full accounting.

## Why it's shaped this way

Every design decision traces to a document in [`../docs/`](../docs/) — in particular
`03-architecture/04-boundaries-and-layout.md` for the layer rules,
`03-architecture/02-beginner.md` for the nine failures each layer exists to fix, and
`01-teardown/` for where each pattern came from in Pi and Tau.

The nine-failure scorecard is the quickest way to see which tier this is:

| Failure | Fixed in |
|---|---|
| one big output kills the session · nothing appears until it finishes · no turn limit | Tier 1 |
| Ctrl-C corrupts the conversation · it deletes something you wanted · one rate limit ends the run · two edits lose data · no persistence | **Tier 2** |
| switching providers means a rewrite | Tier 1 built the seam · **Tier 2 proved it** |
| context fills up and dies · it costs more than it should | Tier 3 |
