import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: false,
  retries: 0,
  workers: 1,
  reporter: "list",
  use: {
    baseURL: "http://127.0.0.1:11135",
    trace: "retain-on-failure",
    // Fleet standard: CUA/e2e always runs dark-theme (see cua_nsis_smoke_testing.md
    // "Dark Mode Only") - force it regardless of any persisted light-mode toggle.
    colorScheme: "dark",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
  webServer: [
    {
      command: "uv run python -m demo_vid_mcp --serve",
      cwd: "..",
      url: "http://127.0.0.1:11134/api/health",
      reuseExistingServer: true,
      timeout: 30_000,
    },
    {
      command: "bun run dev",
      url: "http://127.0.0.1:11135",
      reuseExistingServer: true,
      timeout: 30_000,
    },
  ],
});
