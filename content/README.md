# Content

Plain-English copy for the dashboard. Edit these Markdown files directly on GitHub (pencil icon, then "Propose changes"). The site rebuilds from them.

- `metrics/<metric_id>.md`: "What this means" and 2-4 "Opportunities" for each metric. Every opportunity needs a title, description, working `https` link, provider and `last_checked` date.
- `glossary.md`, `about.md`: the glossary and "About" page.

Rules:

- **Do not type figures** (no numbers) in the wording. Every number on the site must come from the data so it can show its source. A test fails if digits appear in `what_this_means`.
- Aim for plain English (reading age about 12). A readability score is printed in the test output.
- `status` stays `draft` until the parish council reviewer has approved the wording. Then set `status: approved`, `reviewed_by` (role only, no personal names) and `reviewed_on` (YYYY-MM-DD).
