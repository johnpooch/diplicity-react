import { Page } from "@playwright/test";

const FAKE_FCM_TOKEN = "e2e-fake-fcm-registration-token";

/**
 * Stub the two external API calls Firebase Messaging makes when obtaining a
 * push token: Firebase Installations (creates/refreshes an installation ID)
 * and FCM Registration (exchanges the installation auth for an FCM token).
 *
 * Intercepting these with Playwright route handlers prevents real network
 * calls and returns deterministic fake tokens that tests can assert against.
 */
async function stubFirebaseNetwork(page: Page): Promise<void> {
  // Bypass Firebase SDK entirely via test hook.
  // pushManager.subscribe() fails in headless Chromium (no push service),
  // so we inject a fake token that getFirebaseToken() returns immediately.
  await page.addInitScript((token) => {
    (window as unknown as Record<string, unknown>).__TEST_FCM_TOKEN = token;
  }, FAKE_FCM_TOKEN);

  // Keep route stubs for defense-in-depth (service worker may still attempt Firebase calls)
  await page.route("**/firebaseinstallations.googleapis.com/**", (route) => {
    route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        name: "projects/e2e-test/installations/fake-fid",
        fid: "fake-fid",
        refreshToken: "fake-refresh-token",
        authToken: {
          token: "fake-auth-token",
          expiresIn: "604800s",
        },
      }),
    });
  });

  await page.route("**/fcmregistrations.googleapis.com/**", (route) => {
    route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        token: FAKE_FCM_TOKEN,
      }),
    });
  });
}

export { stubFirebaseNetwork, FAKE_FCM_TOKEN };
