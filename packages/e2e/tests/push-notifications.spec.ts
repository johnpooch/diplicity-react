import { test, expect } from "@playwright/test";
import { createTestUser, loginAsTestUser } from "./helpers/auth";
import { stubFirebaseNetwork } from "./helpers/firebase-stub";
import { stubNotificationPermission } from "./helpers/notification-permission";

let tokens: ReturnType<typeof createTestUser>;

test.beforeAll(() => {
  tokens = createTestUser("push-test@e2e.local", "Push Test User");
});

test.describe("Push Notifications", () => {
  test.describe.configure({ mode: "serial" });

  test("enable push notifications", async ({ page }) => {
    await stubNotificationPermission(page, {
      initial: "default",
      requestResult: "granted",
    });
    await stubFirebaseNetwork(page);
    await page.goto("/");
    await loginAsTestUser(page, tokens);
    await page.goto("/profile");

    const toggle = page.locator("#push-notifications");
    await expect(toggle).toBeVisible();
    await expect(toggle).toHaveAttribute("data-state", "unchecked");

    await toggle.click();

    await expect(toggle).toHaveAttribute("data-state", "checked");
  });

  test("disable push notifications", async ({ page, context }) => {
    await context.grantPermissions(["notifications"]);
    await stubFirebaseNetwork(page);
    await page.goto("/");
    await loginAsTestUser(page, tokens);
    await page.goto("/profile");

    const toggle = page.locator("#push-notifications");
    await expect(toggle).toHaveAttribute("data-state", "checked");

    await toggle.click();

    await expect(toggle).toHaveAttribute("data-state", "unchecked");
  });

  test("shows blocked notification alert when permission denied", async ({
    page,
  }) => {
    await stubNotificationPermission(page, { initial: "denied" });
    await stubFirebaseNetwork(page);
    await page.goto("/");
    await loginAsTestUser(page, tokens);
    await page.goto("/profile");

    const toggle = page.locator("#push-notifications");
    await expect(toggle).toBeVisible();
    await expect(toggle).toBeDisabled();
    await expect(
      page.getByText("Notifications are blocked in your browser")
    ).toBeVisible();
  });

  test("shows error when notification permission is dismissed", async ({
    page,
  }) => {
    await stubNotificationPermission(page, {
      initial: "default",
      requestResult: "default",
    });
    await stubFirebaseNetwork(page);
    await page.goto("/");
    await loginAsTestUser(page, tokens);
    await page.goto("/profile");

    const toggle = page.locator("#push-notifications");
    await expect(toggle).toBeVisible();

    await toggle.click();

    await expect(
      page.getByText("Notification permission was not granted")
    ).toBeVisible();
  });
});
