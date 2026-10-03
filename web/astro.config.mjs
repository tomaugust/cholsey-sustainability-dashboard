import { defineConfig } from "astro/config";
import { fileURLToPath } from "node:url";
import path from "node:path";

// SITE_DATA_DIR lets tests build the site against fixture JSON (tests/fixture-build.test.ts).
const dataDir = process.env.SITE_DATA_DIR
  ? path.resolve(process.env.SITE_DATA_DIR)
  : fileURLToPath(new URL("./src/data", import.meta.url));

// GitHub Pages project site; internal links go through `href()` in src/lib/data.ts.
export default defineConfig({
  output: "static",
  site: "https://tomaugust.github.io",
  base: "/cholsey-sustainability-dashboard",
  vite: { resolve: { alias: { "@data": dataDir } } },
});
