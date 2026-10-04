# Content

Plain-English copy for the dashboard. Edit these Markdown files directly on GitHub (pencil icon, then "Propose changes"). The site rebuilds from them.

- `metrics/<metric_id>.md`: "What this means" and 2-4 "Opportunities" for each metric. Every opportunity needs a title, description, working `https` link, provider and `last_checked` date.
- `home.md`: the home page headline and the four story headings.
- `glossary.md`, `about.md`, `methodology.md`: the glossary, "About" page and the explanatory sections of the methodology page.

Rules:

- **Do not type figures** (no numbers) in the wording. Every number on the site must come from the data so it can show its source. A test fails if digits appear in `what_this_means`.
- Aim for plain English (reading age about 12). A readability score is printed in the test output.
- `status` stays `draft` until the parish council reviewer has approved the wording. Then set `status: approved`, `reviewed_by` (role only, no personal names) and `reviewed_on` (YYYY-MM-DD).

Before sending the wording to the reviewer, regenerate the review pack: `cd web && npm run content:export` (writes `docs/content-review-pack.md`). The pack is not kept in sync automatically.
