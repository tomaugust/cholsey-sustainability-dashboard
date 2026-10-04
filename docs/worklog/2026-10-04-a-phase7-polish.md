# 2026-10-04 — Phase 7 polish, accessibility and launch readiness (P7.1–P7.7)

- **Phase / tasks:** Phase 7, P7.1–P7.7 built; P7.8 and manual checks pending (human)
- **Branch / PR:** `phase-7-polish-launch` → `main`
- **Agent / person:** Claude Code agent, live session with Tom

## Done

- **P7.1** type scale, spacing, surface colours, chart colour tokens (`CHART` in `chart.ts`, CSS variables), print styles (hides nav, opens all disclosures for print).
- **P7.2** charts redrawn in a 420-unit viewBox so text is readable at 360 px; nav links, disclosures, selects and opportunity links at least 44 px; value labels use `*` for estimates.
- **P7.3** axe-core on every page with details expanded: zero serious/critical (passed first run after the design pass); global focus-visible outline; reduced-motion guard; `lang="en-GB"`.
- **P7.4** methodology page: draft narrative in `content/methodology.md` plus a data-generated table of methods, flags and geography per metric; narrative checked against `metrics.json` and the metrics code.
- **P7.5** footer: OGL line, each source attribution, data-refresh date (latest `retrieved_at`), repo link.
- **P7.6** meta description, canonical, Open Graph/Twitter tags, social card PNG, hand-rolled sitemap, `noindex` until `LAUNCHED` is set, gzip page-weight budget test.
- **P7.7** launch checklist in `docs/launch-checklist.md`; no custom domain planned (Q-004).
- ADR-0017.
- CI: Lighthouse job (`web/lighthouserc.json`; locally 100/100/100, SEO 63 because of noindex, not asserted).

## Verification

Vitest 46 passed; Playwright 54 passed locally (axe x10, 360 px x10, tap targets, footer, meta, sitemap, weight, plus earlier suites); lint and `astro check` clean; `lhci autorun` assertions passed against local Chromium.

## Not done / carried over

- **Manual checks** (human): keyboard walk-through, screen-reader spot check, iOS Safari and Android Chrome, print preview.
- **P7.8** reviewer "S" approval of content; then flip `LAUNCHED` in `web/src/lib/site.ts`; launch sign-off.
- Individual chart marks remain small touch targets at 360 px; the disclosures and tables provide the accessible route (ADR-0017).
- Phase 7 cannot be marked done until the above are recorded.

## Review cycle 1 (Opus)

No blocking code findings. Fixed: three factual errors in the methodology wording (energy is total energy divided by total meters, address-weighted for Cholsey and Moulsford and land-area-weighted for the others; canopy uses the single ward containing the parish; the MCS Cholsey rate is the district rate); methodology table caption; home-page canonical URL now ends in a slash and is tested; page-weight test now waits for all responses and excludes fonts; trend-chart year labels no longer collide after a new year is added; only Cholsey's trend points are keyboard focusable (was over 300 tab stops on the home energy page); Lighthouse runs three times and keeps its reports as a CI artifact.
Not done: the plan's P7.4 asks for suppression narrative; the draft "Missing data" section covers it only partly (suppression fallback is deferred, ADR-0011).
