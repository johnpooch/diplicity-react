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
