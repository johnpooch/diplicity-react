import { test, expect } from "@playwright/test";
import { createTestUser, loginAsTestUser } from "./helpers/auth";
import { stubFirebaseNetwork } from "./helpers/firebase-stub";

let tokens: ReturnType<typeof createTestUser>;

test.beforeAll(() => {
  tokens = createTestUser();
});

test.describe("Profile smoke test", () => {
  test.beforeEach(async ({ page }) => {
    await stubFirebaseNetwork(page);
    await page.goto("/");
    await loginAsTestUser(page, tokens);
  });

  test("loads profile page with push notification toggle visible", async ({
    page,
  }) => {
    await page.goto("/profile");
    await expect(page.locator("#push-notifications")).toBeVisible();
    await expect(page.getByText("Push Notifications")).toBeVisible();
  });
});
