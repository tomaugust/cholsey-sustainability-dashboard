# CLAUDE.md — agent entry point

Cholsey Parish Sustainability Dashboard: a static, zero-cost public dashboard that tracks Cholsey parish's environmental and energy-transition indicators, benchmarks them against neighbouring parishes, the district and the national average, and links each one to local actions. Every number on it must be traceable to its source.

## Read first, in this order, every session

1. `docs/STATUS.md`: where the project is **now**, the current phase, tasks, blockers, open questions and **next steps**.
2. The latest 1–3 entries in `docs/worklog/` (`ls docs/worklog | tail -3`).
3. `docs/development-plan.md`: the section for the current phase (goal, work packages, tests of success, exit criteria), plus §4 (working protocol) if you haven't read it this session.
4. Any ADRs in `docs/decisions/` linked from the task you're picking up.
5. `docs/technical-specification.md` when you need the underlying requirement. The spec wins over the plan when they conflict.

## Non-negotiable rules

- **Provenance on every value.** Pipeline rows carry source, URL, vintage, retrieval date, geography used, method and flag. The UI exposes them on every number. A value without provenance is a bug.
- **Never show Cholsey alone.** Comparisons always include comparators and a district or national reference.
- **Flag estimates. Never silently interpolate.** "Current" means latest available year, labelled.
- **One phase per PR.** Small, reviewable increments. Don't jump ahead of the current phase's exit criteria.
- **Never hand-edit generated data** (`data/processed/`, `web/src/data/`). Regenerate it.
- **Never skip, disable or weaken a test** to get green.
- **Don't edit `docs/technical-specification.md`.** Raise an Open question in `STATUS.md` instead.
- Raise spec-level, scope, stack or comparator decisions with the project lead as **Proposed** ADRs. Don't decide them unilaterally.

## Documentation duties (plan §4)

- **During work:** write an ADR for any non-trivial decision, in the same PR. Add newly discovered tasks to `STATUS.md` with new `P<phase>.<n>` IDs. Log questions for the project lead as `Q-NNN` in `STATUS.md`.
- **Before ending a session (mandatory):** update `docs/STATUS.md` (task states, Next steps, Last updated) and add `docs/worklog/YYYY-MM-DD-<slug>.md` using the template in `docs/worklog/README.md`. Commit the docs with the code.
- Commit and PR titles start with the task ID, for example `P2.5: DESNZ LSOA fetcher`.

## Commands

`setup`, `test` and `lint` work for real (verified in CI, `.github/workflows/ci.yml`). `refresh` and `site` are placeholders — `refresh` fails on purpose until Phase 2/3 build the real pipeline; `site` currently just builds the front-end skeleton and will build the real dashboard once Phase 4/5 wire in data.

```bash
make setup     # install pipeline (uv) and web (npm) dependencies
make test      # all pipeline + web tests
make lint      # ruff + eslint/prettier
make refresh   # fetch → validate → metrics → validate → export (stub until Phase 2/3)
make site      # build the static site into web/dist
```

CI (`ci.yml`) runs `test`/`lint` on every PR. Deploy (`deploy.yml`) publishes `web/dist/` to GitHub Pages on push to `main` — requires the repo's Settings → Pages → Source to be set to "GitHub Actions" once (a workflow can't do this itself).

## Layout

See `docs/development-plan.md` §2.2 for the target layout. Key paths are `pipeline/`, `config/`, `data/`, `content/`, `web/` and `docs/`.
