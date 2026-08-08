import { defineConfig } from "@playwright/test";

const webBaseUrl = process.env.E2E_BASE_URL ?? "http://127.0.0.1:3000";
const apiBaseUrl = process.env.E2E_API_BASE_URL ?? "http://127.0.0.1:8000";
const useExternalServers = process.env.PLAYWRIGHT_EXTERNAL_SERVERS === "1";

export default defineConfig({
  testDir: "./tests/e2e",
  fullyParallel: true,
  forbidOnly: Boolean(process.env.CI),
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: process.env.CI ? "github" : "list",
  use: {
    baseURL: webBaseUrl,
    trace: "on-first-retry",
  },
  webServer: useExternalServers
    ? undefined
    : [
        {
          command: "pnpm dev:web",
          url: webBaseUrl,
          reuseExistingServer: !process.env.CI,
          timeout: 120_000,
        },
        {
          command: "pnpm dev:api",
          url: `${apiBaseUrl}/health`,
          reuseExistingServer: !process.env.CI,
          timeout: 120_000,
        },
      ],
});
