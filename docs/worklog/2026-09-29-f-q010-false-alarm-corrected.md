# 2026-09-29 — Q-010 was a false alarm; corrected after Tom pushed back

- **Phase / tasks:** cross-cutting (question-actioning per plan §4.7), not a phase task
- **Branch / PR:** `main` (documentation-only)
- **Agent / person:** Claude Code agent, responding directly to Tom in a live session

## Goal
Tom said: "I check and pages is definitely set to GitHub actions, could something else be causing this issue?" — a direct challenge to Q-010's claim that Settings → Pages → Source hadn't actually saved as "GitHub Actions". Investigate properly rather than assuming either he or the earlier check was right.

## Done
- Re-checked the live Pages URL from scratch, this time with a rigorous technical check instead of a fuzzy one:
  - `curl -sI` on the live URL: `Last-Modified: Tue, 29 Sep 2026 04:28:04 GMT` — matches recent activity on `main` (a docs-only push around that time), confirming the served content is fresh, not a stale cached build.
  - `curl -s` on the live URL to get the actual HTML, then compared it line-by-line against `web/src/pages/index.astro`'s source. **Exact match**: same `<title>`, same `<h1>`, same "This site is under construction..." paragraph, same link to `development-plan.md` on `main`. No GitHub markdown rendering chrome anywhere (no README styling classes, no GitHub nav/header).
- **Conclusion: Q-010 was wrong.** The live site genuinely is the Astro build, served via the GitHub Actions Pages source, exactly as Tom's original Q-006 answer said. The earlier session that raised Q-010 judged the page "looks like a rendered README" using an AI-based page read (WebFetch) rather than actually inspecting the HTML — a reasonable-looking but ultimately mistaken visual judgement, since a minimal unstyled Astro placeholder page and a minimal unstyled GitHub README render can look superficially similar to that kind of check (both are just a plain heading and a paragraph, no CSS). It never actually fetched or compared the raw HTML at the time.
- Closed Q-010 in `docs/STATUS.md`: moved it into *Answered/closed questions* with the corrected finding, removed it from the open questions table, and fixed every other place in the file that still referenced the old (wrong) claim (header, next steps, Q-006's actioned-as note, Phase 1's exit-criteria note, the Pages URL under *Key links*).

## Decisions
- No ADR — this is correcting a factual error in the project's own documentation, not a new decision.
- Judgement call: rather than just apologising and moving on, fixed every stale reference to the wrong claim across the file in the same pass, so a future session reading STATUS.md doesn't re-inherit the mistake from an untouched corner of the document.

## Verification
```
$ curl -sI "https://tomaugust.github.io/cholsey-sustainability-dashboard/" | grep -i last-modified
last-modified: Tue, 29 Sep 2026 04:28:04 GMT

$ curl -s "https://tomaugust.github.io/cholsey-sustainability-dashboard/"
<!DOCTYPE html>...<h1>Cholsey Parish Sustainability Dashboard</h1>...
# byte-for-byte matches web/src/pages/index.astro's rendered output
```

## Not done / carried over
- No code or settings change needed — there was never a real problem.
- Q-005 and Q-007 remain open.

## Handoff notes
- **Lesson for future sessions**: when checking what a live page actually contains (not just "does it look right"), fetch the raw HTML directly (`curl`) and compare against the known source, rather than relying solely on an AI-based page-read tool's visual judgement — the latter can mistake two superficially similar-looking minimal pages for each other, exactly as happened here. Reserve fuzzy page reads for content/copy questions, not for "is this literally the file I think it is" structural questions.
- If Tom ever reports something looking wrong on the live site again, this is the check to run first: `curl -sI <url>` for `Last-Modified`/cache headers, then `curl -s <url>` and diff against the actual source file, before concluding anything about GitHub Pages configuration.
