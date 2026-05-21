import { defineConfig, devices } from "@playwright/test";

const dockerMode = !!process.env.DOCKER_TEST;

export default defineConfig({
  testDir: "./tests",
  timeout: 60_000,
  expect: {
    timeout: 10_000,
  },
  use: {
    baseURL: dockerMode ? "http://127.0.0.1:8000" : "http://127.0.0.1:3000",
    trace: "retain-on-failure",
  },
  webServer: dockerMode
    ? undefined
    : {
        command: "npm run dev -- --hostname 127.0.0.1 --port 3000",
        url: "http://127.0.0.1:3000",
        reuseExistingServer: true,
        timeout: 120_000,
      },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
});
