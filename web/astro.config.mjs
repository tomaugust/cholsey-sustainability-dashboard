import { defineConfig } from "astro/config";

// See docs/development-plan.md §2 (ADR-0002): static output, deployed to
// GitHub Pages under the default project URL (Q-004 resolution). `site` and
// `base` should be set to the real Pages URL once P0.7 stands up the deploy
// workflow and we know the exact repo/org slug it publishes under.
export default defineConfig({
  output: "static",
});
