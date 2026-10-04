# Launch checklist

The site is deployed to GitHub Pages but **deliberately unshared** (ADR-0016): pages carry `noindex`, content is marked draft. Do not share the URL until every box below is ticked.

## Automated gates (in CI)

- [x] axe-core: zero serious or critical violations on every page (`web/e2e/a11y.spec.ts`)
- [x] No horizontal scroll at 360 px on every page; tap targets at least 44 px
- [x] Lighthouse CI (mobile): accessibility, best practices at least 95, performance at least 90 on home and one metric page (`web/lighthouserc.json`)
- [x] Footer carries the OGL text, every source attribution, the data-refresh date and a repo link
- [x] Home page weight under 500 KB (gzip estimate)
- [x] Link checker (CI plus weekly)

## Manual checks (record result and date here or in the worklog)

- [ ] Keyboard-only walk-through of every page
- [ ] Screen-reader spot check (VoiceOver or NVDA) on home and one metric page
- [ ] Real-phone check: iOS Safari
- [ ] Real-phone check: Android Chrome
- [ ] Print preview of a metric page looks right for council papers

## Content (P7.8, ADR-0016)

- [ ] Reviewer "S" has reviewed `docs/content-review-pack.md` (regenerate first: `cd web && npm run content:export`)
- [ ] Feedback applied; every file in `content/` has `status: approved`, `reviewed_by` (role only) and `reviewed_on`; draft notices are gone

## Launch switches

- [ ] Set `LAUNCHED = true` in `web/src/lib/site.ts` (removes `noindex`)
- [ ] Custom domain (P7.7): not planned (Q-004). If wanted, set Astro `site`/`base`, the Pages custom domain and DNS, and update `lychee.toml`/sitemap checks
- [ ] Project lead gives launch sign-off, recorded in the worklog
- [ ] Publish the URL
