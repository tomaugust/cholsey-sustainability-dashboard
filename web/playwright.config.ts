import { defineConfig } from "@playwright/test";

// CI installs Chromium with `npx playwright install --with-deps chromium`;
// locally set PW_CHROMIUM_PATH to a preinstalled browser.
const executablePath = process.env.PW_CHROMIUM_PATH;

export default defineConfig({
  testDir: "e2e",
  webServer: {
    command: "npm run preview -- --port 4321",
    url: "http://localhost:4321/cholsey-sustainability-dashboard/",
    reuseExistingServer: !process.env.CI,
  },
  use: {
    baseURL: "http://localhost:4321/cholsey-sustainability-dashboard/",
    launchOptions: executablePath ? { executablePath } : {},
  },
});
