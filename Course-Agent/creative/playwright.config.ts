import { defineConfig, devices } from "@playwright/test"

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: false,
  forbidOnly: Boolean(process.env.CI),
  retries: process.env.CI ? 1 : 0,
  workers: 1,
  reporter: "list",
  outputDir: "test-results",
  use: {
    ...devices["Desktop Chrome"],
    baseURL: "http://127.0.0.1:3000",
    screenshot: "only-on-failure",
    trace: "on-first-retry",
    video: "retain-on-failure",
    viewport: { width: 1440, height: 900 },
  },
  webServer: [
    {
      command: "pnpm dev --hostname 127.0.0.1 --port 3000",
      env: {
        NEXT_PUBLIC_API_BASE_URL: "http://127.0.0.1:8000",
      },
      reuseExistingServer: true,
      timeout: 120_000,
      url: "http://127.0.0.1:3000",
    },
    {
      command:
        "..\\..\\backend\\.venv\\Scripts\\python -m uvicorn app.main:app --app-dir ..\\..\\backend --host 127.0.0.1 --port 8000",
      env: {
        AGENT_MODE: "mock",
        DATABASE_URL: "sqlite:///../../backend/data/zhixue-e2e.db",
        MOCK_EVENT_DELAY_MS: "100",
      },
      reuseExistingServer: true,
      timeout: 120_000,
      url: "http://127.0.0.1:8000/health",
    },
  ],
})
