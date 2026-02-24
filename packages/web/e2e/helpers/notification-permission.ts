import { Page } from "@playwright/test";

type PermissionState = "default" | "granted" | "denied";

interface StubNotificationPermissionOptions {
  initial: PermissionState;
  requestResult?: PermissionState;
}

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
