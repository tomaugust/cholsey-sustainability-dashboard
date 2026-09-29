# 2026-09-28 — Open-question answer/action-tracking protocol

- **Phase / tasks:** infrastructure/documentation (not a phase task; a gap in the agent workflow itself, raised by Tom directly in chat)
- **Branch / PR:** `claude/new-session-7bcxu1` / not opened
- **Agent / person:** Claude Code agent, direct interactive session with Tom (not a routine firing)

## Goal
Tom asked how asynchronous troubleshooting currently works — whether there's a file he can write answers into that a future routine firing picks up — and then specifically flagged a real gap: the old `Q-NNN` table had a single "Resolution" column that conflated "Tom's answer" with "what the agent did about it", so nothing distinguished "Tom answered this, but no one has acted on it yet" from "fully resolved". Fix that.

## Done
- Redesigned `docs/STATUS.md`'s *Open questions* table: split the old single "Resolution" column into **Tom's answer** and **Status**, with status values `open` / `answered` / `awaiting confirmation` / `actioned`. Added a short explanation directly above the table (how to answer, what each status means) so it's usable without reading the plan.
- Moved Q-001 through Q-004 (already fully resolved on 2026-09-27) into a new collapsed *Answered / closed questions* `<details>` section, in the same style as the existing *Completed phases* summary — keeps the live table showing only what's actually pending (now just Q-005 through Q-008, all genuinely `open`).
- Added **development-plan.md §4.7** ("Open questions: the answer / action-tracking loop") formalising the protocol: Tom only ever has to fill in one cell; an agent is responsible for noticing a filled-in answer, treating it as first-priority work ahead of the normal task queue, acting on it, and setting Status to `actioned` (or `awaiting confirmation` if the answer asks Tom to do something outside the repo, like the GitHub Pages setting in Q-006). Added the status enum to §4.3's vocabulary table alongside task/phase states.
- Updated `CLAUDE.md`'s reading-order step 1 and documentation-duties section to point at this explicitly, since CLAUDE.md is the very first thing read each session and this needs to actually get checked, not just be discoverable three files deep.

## Decisions
- No ADR — this is agent-workflow documentation, not a project architecture or scope decision (development-plan.md §4 itself is exactly the place for this kind of change, per its own rules).
- Judgement call: made Tom's side of the protocol exactly one action (fill in one cell) rather than asking him to also manage a status field — he's a volunteer parish councillor, not someone who should need to learn a status machine to unblock a question. The agent owns the status transitions entirely except the one case it structurally cannot verify (something outside the repo), where `awaiting confirmation` exists specifically so that stays visible rather than silently assumed done.

## Verification
Documentation-only change. Re-read the finished `STATUS.md` file top to bottom to check table formatting, that Q-005 through Q-008 all correctly show `open` with an empty answer cell, and that the `<details>` block renders sensibly as Markdown. Checked file length stayed well under the §4.6 ~200-line guideline (120 lines).

## Not done / carried over
- The protocol is untested by an actual answer-then-pickup cycle yet — the real test will be the next time Tom fills in one of Q-005 through Q-008's answer cells and a subsequent session (routine-fired or not) correctly treats it as first-priority. Worth watching for on the next routine firing after any answer lands.

## Handoff notes
- If you're a routine-fired session reading this: check the *Open questions* table in `STATUS.md` for any row with a non-empty **Tom's answer** cell before doing anything else, per CLAUDE.md's updated step 1 and plan §4.7. This is not optional and not just "nice to notice" — it's now the documented first-priority action.
