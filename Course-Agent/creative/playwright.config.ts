import path from "node:path"

import { defineConfig, devices } from "@playwright/test"

const projectRoot = __dirname

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: false,
  forbidOnly: Boolean(process.env.CI),
  retries: process.env.CI ? 1 : 0,
  workers: 1,
  timeout: 120_000,
  expect: { timeout: 15_000 },
  reporter: "list",
  outputDir: path.resolve(projectRoot, "../../artifacts/demo/raw"),
  use: {
    ...devices["Desktop Chrome"],
    baseURL: "http://127.0.0.1:3000",
    screenshot: "only-on-failure",
    trace: "on-first-retry",
    video: "on",
  },
  projects: [
    { name: "desktop-1366", use: { viewport: { width: 1366, height: 768 } } },
    { name: "desktop-1440", use: { viewport: { width: 1440, height: 900 } } },
    { name: "desktop-1920", use: { viewport: { width: 1920, height: 1080 } } },
  ],
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
        MOCK_EVENT_DELAY_MS: "180",
      },
      reuseExistingServer: true,
      timeout: 120_000,
      url: "http://127.0.0.1:8000/health",
    },
  ],
})
