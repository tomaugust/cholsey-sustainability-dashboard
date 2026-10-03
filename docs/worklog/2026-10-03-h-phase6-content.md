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
