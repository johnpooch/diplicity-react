import { Page } from "@playwright/test";

type PermissionState = "default" | "granted" | "denied";

interface StubNotificationPermissionOptions {
  initial: PermissionState;
  requestResult?: PermissionState;
}

/**
 * Override the browser Notification API permission state for testing.
 *
 * Playwright's Chromium doesn't fully support the Notification API (permission
 * is always "denied" and requestPermission() is a no-op). This uses
 * `page.addInitScript` to redefine `Notification.permission` and
 * `Notification.requestPermission()` before any application code runs,
 * allowing tests to simulate all three permission states (default, granted,
 * denied) and permission prompt outcomes.
 */
async function stubNotificationPermission(
  page: Page,
  options: StubNotificationPermissionOptions
): Promise<void> {
  const { initial, requestResult } = options;
  await page.addInitScript(
    ({ initial, requestResult }) => {
      let currentPermission = initial;
      Object.defineProperty(Notification, "permission", {
        get: () => currentPermission,
        configurable: true,
      });
      Notification.requestPermission = async () => {
        const result = (requestResult ?? initial) as NotificationPermission;
        currentPermission = result;
        return result;
      };
    },
    { initial, requestResult }
  );
}

export { stubNotificationPermission };
