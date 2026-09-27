# 2026-09-27 — Recurring routine fixed after first run failed to push

- **Phase / tasks:** infrastructure (blocks P0.3, not a project task itself)
- **Branch / PR:** `claude/new-session-7bcxu1` / not opened
- **Agent / person:** Claude Code agent, at Tom's request

## Goal
Diagnose and fix why the first automated firing of the 5-hourly recurring job did the right work but couldn't push it, and stop it happening again.

## What happened
The recurring job was originally set up as a Claude Code Remote "Routine" with `create_new_session_on_fire: true` — each firing spawns a brand-new session in the environment. The first real firing:
- Correctly read `docs/STATUS.md` and picked up P0.3 (pipeline Python skeleton).
- Built `pipeline/` per ADR-0002 (uv, Python 3.12, the package skeleton, `pyproject.toml`, `uv.lock`, `.gitignore`), and reported `uv run pytest` and `uv run ruff check/format` all passing.
- Committed locally (two commits) but **could not push**: "not in this session's authorized repository set".
- Tried to follow the fallback instruction to disable the Routine via `list_triggers`/`update_trigger`, but those tools were not available in that session either.
- Correctly did NOT try to route around the push denial (no credential extraction), and reported the blocker back via the one channel that did work: the mandatory end-of-run push notification.

## Root cause
Confirmed via `get_session` and `create_trigger`'s own warning: a fresh-session-per-fire Routine, created the way we created it, gets **no repo `sources`/`outcomes` config** (there's no parameter for it on `create_trigger`) and **no Claude_Code_Remote/github/Claude_Docs MCP connector tools** (connectors on a trigger can only be drawn from ones the *creating* session itself holds as claude.ai connectors, and `ListConnectors` showed this account has none — GitHub repo access here is a different mechanism, `session_context.sources`, set only at normal session creation). So a fresh-session Routine can read/clone public-ish things but can't push, and can't call `add_repo`, `list_triggers` or `update_trigger` to fix or flag itself. This makes the "self-disable on blocker" design fundamentally unworkable for that trigger type given current tool exposure.

## Decision
Rebuilt the Routine bound to **this session** instead (`persistent_session_id` omitted → defaults to "fire into the calling session"). This session already has full repo access (`session_context.sources`/`outcomes`) and the Claude_Code_Remote tools, so push and self-disable both work as originally intended. No ADR — this is session/tooling plumbing, not a project decision.

- Deleted the old trigger `trig_01XoxPusLGKgyz5eFnhvpFQ8`.
- Created `trig_01UeEpu3FYupU2DqgxXzSvpu`, same cadence (every 5 hours, now `18 */5 * * *`), bound to session `session_01Hy7urgJZza83eVqHxGWcJY`, with the prompt updated to say the conversation continues but repo files are the source of truth (not chat memory), and to verify the push actually landed (`git log origin/...`) before ending.
- Archived/abandoned the stranded fresh session (`session_017S9yjSnErNdozVFKKtATk2`) rather than trying to extract its commits — it's a small, cheap skeleton to redo, not worth cross-session patch archaeology.
- **P0.3 reset to `todo`** in STATUS.md. Its work needs to be redone by the next firing (or by Tom).

## Verification
- `git fetch origin claude/new-session-7bcxu1` confirmed the remote branch is still at `4c1e85c` (P0.2) — nothing from the failed run ever landed, so no data is inconsistent, just absent.
- Confirmed via `get_session` on this session that `session_context.sources`/`outcomes` list the repo and the target branch — this is why pushes from this session (P0.1, P0.2) succeeded.

## Not done / carried over
- P0.3 needs doing (again). Should be quick — it's a skeleton, not novel design work.
- Worth revisiting later whether a fresh-session-per-fire Routine could be made to work (e.g. if `create_trigger` gains a way to specify repo sources, or if connectors become available), since a persistent-session Routine will accumulate conversation context turn over turn and is bounded by this session's context window and the Routine's own 7-day auto-expiry. Not urgent — flag if it becomes a problem.

## Handoff notes
- If a future firing reports it can't push or can't find `list_triggers`/`update_trigger`, that's a sign the binding broke again (e.g. the Routine somehow reverted to spawning fresh sessions) — check the Routine's `persist_session`/`persistent_session_id` fields via `list_triggers` first, don't just retry.
- The stranded session `session_017S9yjSnErNdozVFKKtATk2` may still exist read-only; it is not expected to be needed again.
