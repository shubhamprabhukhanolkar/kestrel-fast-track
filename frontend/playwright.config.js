import { defineConfig } from "@playwright/test";
import path from "node:path";
const runId = Date.now();
const python =
  process.platform === "win32"
    ? ".venv/Scripts/python.exe"
    : ".venv/bin/python";
export default defineConfig({
  testDir: "./e2e",
  outputDir: "../artifacts/playwright",
  timeout: 45000,
  workers: 1,
  use: {
    baseURL: "http://127.0.0.1:8091",
    viewport: { width: 1440, height: 1050 },
    launchOptions: {
      executablePath:
        process.env.KESTREL_CHROME ||
        (process.platform === "win32"
          ? "C:/Program Files/Google/Chrome/Application/chrome.exe"
          : "/usr/bin/google-chrome"),
    },
    screenshot: "only-on-failure",
  },
  webServer: {
    command: `"${python}" -m uvicorn backend.main:app --host 127.0.0.1 --port 8091`,
    cwd: path.resolve(".."),
    url: "http://127.0.0.1:8091/api/v1/health",
    reuseExistingServer: false,
    timeout: 30000,
    env: {
      DEMO_MODE: "true",
      AUTH_MODE: "demo",
      SEED_TELEMETRY: "true",
      DATABASE_PATH: `artifacts/browser-${runId}/kestrel.db`,
      DOCUMENT_DIR: `artifacts/browser-${runId}/documents`,
      STATIC_DIR: "frontend/dist",
    },
  },
});
