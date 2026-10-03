import { defineConfig } from "astro/config";

// GitHub Pages project site; internal links go through `href()` in src/lib/data.ts.
export default defineConfig({
  output: "static",
  site: "https://tomaugust.github.io",
  base: "/cholsey-sustainability-dashboard",
});
