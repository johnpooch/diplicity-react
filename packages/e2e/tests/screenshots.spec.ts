import { test, expect } from "@playwright/test";
import { readFileSync } from "fs";
import { join } from "path";
import { loginAsTestUser } from "./helpers/auth";

interface SeedData {
  accessToken: string;
  refreshToken: string;
  email: string;
  name: string;
  game1Id: string;
  phase2Id: number;
  phase3Id: number;
  channelId: string;
}

function loadSeedData(): SeedData {
  const seedFile = process.env.SEED_DATA_FILE;
  if (!seedFile) {
    throw new Error(
      "SEED_DATA_FILE env var must point to the seed data JSON file"
    );
  }
  return JSON.parse(readFileSync(seedFile, "utf-8"));
}

const seedData = loadSeedData();

test.beforeEach(async ({ page }) => {
  await page.goto("/");
  await loginAsTestUser(page, {
    accessToken: seedData.accessToken,
    refreshToken: seedData.refreshToken,
    email: seedData.email,
    name: seedData.name,
  });
});

function screenshotPath(
  projectName: string | undefined,
  name: string
): string {
  const folder = projectName ?? "default";
  return join(__dirname, "..", "screenshots", folder, `${name}.png`);
}

test("home screen", async ({ page }, testInfo) => {
  await page.goto("/");
  await page.waitForLoadState("networkidle");
  await expect(page.getByText("The Great War")).toBeVisible({
    timeout: 15000,
  });
  // Allow rendering to settle
  await page.waitForTimeout(1000);
  await page.screenshot({
    path: screenshotPath(testInfo.project.name, "home"),
    fullPage: false,
  });
});

test("map view", async ({ page }, testInfo) => {
  await page.goto(
    `/game/${seedData.game1Id}/phase/${seedData.phase3Id}`
  );
  await page.waitForLoadState("networkidle");
  // Wait for a map SVG to be attached to the DOM (layout may render a hidden duplicate)
  await page.locator('svg[preserveAspectRatio]').first().waitFor({ state: "attached", timeout: 15000 });
  await page.waitForTimeout(2000);
  await page.screenshot({
    path: screenshotPath(testInfo.project.name, "map"),
    fullPage: false,
  });
});

test("orders resolved", async ({ page }, testInfo) => {
  await page.goto(
    `/game/${seedData.game1Id}/phase/${seedData.phase2Id}`
  );
  await page.waitForLoadState("networkidle");
  // Wait for at least one map SVG to be attached (completed phases may render two)
  await page.locator('svg[preserveAspectRatio]').first().waitFor({ state: "attached", timeout: 15000 });
  await page.waitForTimeout(2000);
  await page.screenshot({
    path: screenshotPath(testInfo.project.name, "orders-resolved"),
    fullPage: false,
  });
});

test("chat", async ({ page }, testInfo) => {
  await page.goto(
    `/game/${seedData.game1Id}/phase/${seedData.phase3Id}/chat/channel/${seedData.channelId}`
  );
  await page.waitForLoadState("networkidle");
  // Wait for chat messages to appear
  await expect(
    page.getByText("I think we should work together")
  ).toBeVisible({ timeout: 15000 });
  await page.waitForTimeout(1000);
  await page.screenshot({
    path: screenshotPath(testInfo.project.name, "chat"),
    fullPage: false,
  });
});
