import eslintPluginAstro from "eslint-plugin-astro";
import tsParser from "@typescript-eslint/parser";
import tsPlugin from "@typescript-eslint/eslint-plugin";

export default [
  {
    // env.d.ts is Astro-generated and requires the triple-slash reference
    // convention that @typescript-eslint/triple-slash-reference otherwise
    // flags — see https://docs.astro.build/en/guides/typescript/
    ignores: ["dist/**", ".astro/**", "node_modules/**", "src/env.d.ts"],
  },
  {
    files: ["**/*.ts"],
    languageOptions: {
      parser: tsParser,
    },
    plugins: {
      "@typescript-eslint": tsPlugin,
    },
    rules: {
      ...tsPlugin.configs.recommended.rules,
    },
  },
  ...eslintPluginAstro.configs.recommended,
];
