# 2026-10-03 — Phase 6 narrative and opportunities content (P6.1–P6.4, P6.5 prepared)

- **Phase / tasks:** Phase 6, P6.1–P6.4 done; P6.5 (council review loop) prepared, awaiting reviewer "S"
- **Branch / PR:** `phase-6-content` → `main`
- **Agent / person:** Claude Code agent, live session with Tom

## Done

- **P6.1** content model and validating loader (ADR-0015): `content/metrics/*.md`, `glossary.md`, `about.md`; contributor guide in `content/README.md`.
- **P6.2** plain-English "What this means" for all six metrics (no digits, so every figure stays data-driven and traceable).
- **P6.3** 3 opportunities per metric with real links. Every external link was checked (HTTP 200, or 403 for sites that block bots) on 2026-10-03; GOV.UK, South Oxfordshire District Council, Low Carbon Hub (including Cholsey Environment Champions), Woodland Trust, BBOWT, Fields in Trust, MCS.
- **P6.4** `/glossary/` and `/about/` pages, added to the nav.
- Metric pages render explainer and opportunities; draft status shows a visible notice.
- `lychee` link check in CI (new `links` job) and weekly `links.yml`; readability (Flesch) printed as a warning.
- **P6.5 prep:** `npm run content:export` -> `docs/content-review-pack.md`.
- Tests: Vitest 44 (schema, rejection cases, readability), Playwright smoke now covers `/glossary/` and `/about/` and 2-4 opportunities per metric section.

## Not done / carried over

- P6.5 sign-off: reviewer "S" must review; approval date and role to go in front-matter and here. Q-015 asks how, and whether to merge before approval.
- Readability: two files score just under 60 (warning only).
- Cholsey Parish Council website and Energy Saving Trust return 403 to automated requests, so they are not linked; lychee accepts 403/429.

## Handoff notes

- Do not record the reviewer's name anywhere (Q-005); use the role.
- After approval run nothing special: set `status: approved` and the review fields; the draft notice disappears.

## Review cycle 1 (Opus)

Four blocking points, all addressed except the process one (held deliberately):

- Gas: removed the Great British Insulation Scheme link (scheme closed; statistics page only); replaced with the GOV.UK energy-efficiency tool.
- Greenspace: allotments removed from the text (the pipeline excludes them, ADR-0008) and the caveat now says the figure is more likely too low than too high (it is clipped to the parish, flag `partial_coverage`), not an "estimate".
- Process: the PR was opened before P6.5 completes. Merge is held until S approves (Q-015).
- Also fixed: Cholsey Environment Champions descriptions no longer claim more than the page says; solar/heat pump caveat now conditional on the estimate flag; impossible dates rejected; no-digits rule extended to all editable prose; content path works from repo root or `web/`; review-pack script ignores non-`.md` files and a test fails if the committed pack is stale; dropped redundant `@types/js-yaml`; readability warning rounds like the display.
- Left as is: lychee runs on PRs (external outages can block; retries and 403/429 accept are set, re-run if it happens); two copies of the link job.

## Q-015 answered (2026-10-04)

Tom: the URL is unshared, so build the most complete site possible with elements marked draft before sharing. ADR-0016 defers P6.5 approval to the Phase 7 launch gate (new P7.8; plan updated). Phase 6 merged with all content `draft`.
