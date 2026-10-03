import { fileURLToPath } from "node:url";
import { defineConfig } from "vitest/config";

export default defineConfig({
  resolve: {
    alias: { "@data": fileURLToPath(new URL("./src/data", import.meta.url)) },
  },
  test: {
    include: ["tests/**/*.test.ts"],
  },
});
