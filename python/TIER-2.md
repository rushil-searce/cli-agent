# omega — Tier 2

What this tier contains, and what it deliberately leaves to Tier 3.

**Status: this is the contract, written before the code.** It states what must be true of Tier 2
when it closes. Measured line counts and test totals are filled in at close-out; everything else
is a commitment made in advance, so the tier can be checked against it rather than described
after the fact.

Companion to `TIER-1.md`. Where that file's Part 2 said *"here is a gap and here is the seam it
plugs into"*, this file's Part 2 does the same thing one tier further out.

---

## Part 0 — Tier 1 → Tier 2, the change in one page

Tier 1's verdict was: *a working agent with real layers — not safe, not persistent, not
interruptible.* Tier 2 addresses exactly those three words, and proves the layers were real.

| | **Tier 1** | **Tier 2** |
|---|---|---|
| **Verdict** | the loop works | it is usable |
| Scope | a scratch directory | a real repository |
| Who owns the conversation | `cli.py` holds a bare `list` | `harness.py`, an object |
| Event vocabulary the app sees | the **12** provider events, passed straight through | the **10** agent events, emitted by the loop |
| Ctrl-C | kills the process, may corrupt the transcript | cancels the turn; transcript stays valid |
| Closing the terminal | everything is lost | session is on disk, `--resume` picks it up |
| Editing a file | whole-file rewrite only | exact-match `edit`, one lock per path |
| `rm -rf` | runs | asks first |
| Reading `~/.ssh` | allowed | refused, in one place |
| A 429 | ends the run | retried below the event boundary |
| Providers | one, **unproven** | two, and the second one is the proof |
| Auth | a static `api_key` string | a resolver callback, resolved per request |
| Tokens | captured, unused | summed, priced, and shown |
| Loop hooks | none | six of the nine declared, four wired |

### The nine failures, tier by tier

From `../docs/03-architecture/02-beginner.md`. This is the honest scorecard.

| Failure | Fixed in |
|---|---|
| **#2** one big output kills the session | Tier 1 — truncation |
| **#6** nothing appears until it finishes | Tier 1 — streaming |
| *no turn limit* | Tier 1 — `max_turns` |
| **#3** Ctrl-C corrupts the conversation permanently | **Tier 2** |
| **#4** it deletes something you wanted | **Tier 2** |
| **#5** one rate limit throws away the run | **Tier 2** |
| **#8** two edits to one file lose data | **Tier 2** |
| *no persistence* | **Tier 2** |
| **#7** switching providers means a rewrite | Tier 1 built the seam · **Tier 2 proves it** |
| **#1** context fills up and dies | Tier 3 — compaction |
| **#9** it costs more than it should | Tier 3 — prompt caching |

Tier 2 adds the *instruments* for #1 and #9 — a context gauge and a cost total — without the
fixes. You will be able to watch both problems approach before Tier 3 solves them.

---

## Part 1 — What Tier 2 has

### Layer 1 · Provider

| Capability | File | Why it exists |
|---|---|---|
| **A second adapter** | `providers/openai.py` | Not a feature — the exam. Chat Completions is a genuinely different wire format |
| Retry with backoff | `providers/retry.py` | **Below the event boundary**, so the loop never learns a retry happened — failure **#5** |
| Auth resolver callback | `provider.py`, both adapters | Resolved immediately before each request, so a token can refresh mid-session |
| One wire format per adapter | `providers/` | `openai.py` also reaches Groq, Together, Ollama and vLLM — the format is the unit, not the vendor |

**The provider interface itself does not change.** If it had to, Tier 1 was wrong.

### Layer 2 · Agent core

| Capability | File | Why it exists |
|---|---|---|
| **The 10 agent events** | `agent_events.py` | Coarse progress — `turn_start`, `tool_execution_start`. A **separate file** from the 12 |
| **The harness** | `harness.py` | Something has to own `messages`, or persistence, cancellation and the queues have nowhere to live |
| **Hook bundle** | `hooks.py` | `before_tool_call` · `after_tool_call` · `convert_to_llm` · `transform_context` · the two queue sources. **Not** `get_api_key` — auth is a provider-level resolver, one layer lower |
| Concrete cancellation | `harness.py` | Tier 1 threaded the `signal` everywhere and created nothing. This creates one |
| **Orphaned tool-result repair** | `harness.py` | An unanswered tool call is a **permanent** API error. Runs on interrupt *and* on resume |
| Steering queue | `harness.py` | Type while it works; picked up between turns |
| Follow-up queue | `harness.py` | Queue the next task instead of waiting |
| Two views of history | `hooks.py` | What you see vs what gets sent. **The seam compaction plugs into at Tier 3** |
| Context gauge | `context.py` | chars/4, counts tool schemas. Measures failure **#1**; does not fix it |
| Cost accounting | `cost.py` | Sums and prices the `Usage` Tier 1 already captured |

**`loop.py` must not pass ~250 lines.** It was 151 at the end of Tier 1; Tau's is 318. Growth
means a *decision* leaked in where only the *mechanism* belongs.

### Layer 3 · Coding app

| Capability | File | Why it exists |
|---|---|---|
| **`edit` tool** | `builtin_tools.py` | Exact-match replace, unique match required. Whole-file writes are hopeless past a few hundred lines |
| **Path confinement** | `paths.py` | **One** `resolve_within_root`, called by every filesystem tool. Symlinks resolved before checking — failure **#4** |
| **Per-path write lock** | `file_lock.py` | Keyed on the *resolved* path, shared by `write` and `edit` — failure **#8** |
| **Approval gate** | `approval.py` | Fills `before_tool_call`. Prompts on shell and writes, remembers the answer, blanket-denies the catastrophes |
| Secret redaction | `redact.py` | Fills `after_tool_call`. Key-shaped strings never reach the model or a log |
| `prepare` seam on the shell tool | `builtin_tools.py` | So Tier 3+ sandboxing lands without surgery |
| `run_shell` timeout | `builtin_tools.py` | A hung command used to hang forever |
| Project instruction file | `cli.py` | `OMEGA.md` prepended to the system prompt. Stop retyping the conventions |

### Layer 3 · Sessions

| Capability | File | Why it exists |
|---|---|---|
| **Session persistence** | `session/jsonl.py` | Append-only, migrate-on-read. Pydantic makes this `model_dump_json` |
| Entries carry `parent_id` | `session/entries.py` | Branching is Tier 3, but **retrofitting a tree onto a list is a rewrite** |
| Storage interface | `session/store.py` | So the backend can change without the harness noticing |
| `--resume` / `--continue` | `cli.py` | Resume runs orphan repair first |

### Interface & harness

| Capability | File |
|---|---|
| REPL driving the harness, not the loop | `cli.py` |
| Tool activity shown *while* it runs | `cli.py` |
| Context % and running cost | `cli.py` |
| `--provider` selection | `cli.py` |
| **Headless driver** — prompt in, messages out | `headless.py` |
| Smoke eval | `evals/smoke.py` |

The headless driver is also the terminal-bench interface. Built once, used twice.

### Verified at close-out

- Tests, all offline. No network, no API key, no cost. *(count filled in at close-out)*
- `mypy --strict` clean · `ruff` clean.
- Ctrl-C mid-tool-call, then `--resume`: the next request **succeeds**.
- Writing outside the working directory is refused; `rm -rf` is prompted.
- `--provider openai` runs the same application code.
- Exactly two files import a vendor SDK, both in `providers/`.

---

## Part 2 — What Tier 2 lacks, and where Tier 3 puts it

Same test as Tier 1: every gap below must plug into a seam that already exists. If any of these
would force a change to `loop.py`, `provider.py`, or either event vocabulary, the layering is
wrong and that is the thing to fix.

### The two remaining beginner failures

| Missing | What it costs | The seam it plugs into |
|---|---|---|
| **Compaction** — failure **#1** | Long tasks still die at the context limit. Tier 2 only *shows* you the wall approaching | `transform_context`, wired and doing real work in Tier 2. Pi's 880-line compaction subsystem plugs into exactly this one callback, and the loop contains **zero** lines of it |
| **Prompt caching** — failure **#9** | Every turn re-bills the system prompt and the whole tool schema block | Not a hook — a *constraint*. Cache markers need a byte-identical prefix, which is why `OMEGA.md` is prepended once at startup and never regenerated per turn |

### Things Tier 3 adds next

| Missing | What it costs today | The seam |
|---|---|---|
| **Session branching** | You can rewind by reading the JSONL, but not fork and navigate | `parent_id` is already on every entry. Tier 3 adds `tree.py` — `path_to_entry`, cycle detection |
| **Search tools** — `grep`, `find`, `ls` | It shells out to `rg`, which works but has no output budget of its own | Three more `Tool` objects. `truncate_output()` exists; confinement via `paths.py` exists |
| **A real TUI** | Print output can't show a diff, a spinner, or a sidebar | The 10 agent events **are** the UI contract. Tau's whole agent→UI bridge is 99 lines because of this |
| **Structured logging** | Debugging means reading print output | The same event stream the UI subscribes to. A second listener, not a new mechanism |
| **Image reading** | Screenshots can't be handed to the model | `types.py` content blocks are a discriminated union; an image block is an addition |
| **Subagents *or* plan mode** | No task decomposition | `before_tool_call` plus the headless driver. A subagent *is* the headless driver called from a tool |

### Deliberately not in Tier 3 either

Recorded so the absence is a decision and not an oversight: no MCP, no retrieval/RAG. Neither
reference implements them. Sandboxing is Tier 3+, and its `prepare` seam ships in Tier 2 so it
lands without surgery.

### Known rough edges, stated plainly

- **Cost figures are estimates.** Prices are hardcoded per model; nothing fetches them.
- **The context gauge is chars/4.** It never claims to be exact — only never wildly wrong.
- **Tool calls still execute sequentially.** Tau's do too, despite advertising otherwise.
- **`--fake` still replays a fixed script.** It demonstrates machinery, not intelligence.
- **Approval memory is per-session.** No persisted trust store; that arrives with config.
- **Nothing is sandboxed.** Approvals and path confinement are policy, not containment.

---

## The one-line summary

Tier 1 proved the loop terminates. **Tier 2 makes it safe to point at a real repository** — it can
be interrupted without corruption, it remembers, it asks before it destroys, and its provider
abstraction is no longer a claim but a measured result. What it still cannot do is survive a task
long enough to fill the context window, and that is the whole of Tier 3.
