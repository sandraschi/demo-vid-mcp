import { expect, test } from "@playwright/test";

const NAV_IDS = [
  "dashboard",
  "depot",
  "generate",
  "choreography",
  "chat",
  "scripts",
  "settings",
  "logs",
  "queue",
  "help",
];

test.beforeEach(async ({ page }) => {
  // Force dark theme regardless of any persisted light-mode toggle (fleet
  // CUA/e2e standard: dark-mode-only baseline for screenshots/assertions).
  await page.addInitScript(() => {
    document.documentElement.classList.add("dark");
  });
});

test("dashboard loads with the hero and backend status indicator", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByTestId("dashboard")).toBeVisible();
  await expect(page.getByTestId("dashboard-hero")).toBeVisible();
  await expect(page.getByTestId("backend-dot")).toBeVisible();
});

test("every sidebar nav item navigates to its page", async ({ page }) => {
  await page.goto("/");
  for (const id of NAV_IDS) {
    await page.getByTestId(`nav-${id}`).click();
    await expect(page.getByTestId(`${id}-page`)).toBeVisible();
  }
});
