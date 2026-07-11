import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  timeout: 30_000,
  use: { baseURL: "http://127.0.0.1:4173", trace: "retain-on-failure" },
  webServer: [
    {
      command:
        "uv run --project ../backend uvicorn app.main:app --host 127.0.0.1 --port 8000",
      url: "http://127.0.0.1:8000/health",
      reuseExistingServer: true,
      timeout: 30_000,
    },
    {
      command: "npm run build && npm exec vite preview -- --host 127.0.0.1",
      port: 4173,
      reuseExistingServer: false,
      timeout: 30_000,
    },
  ],
});
