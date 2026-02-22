import { Page } from "@playwright/test";

const FAKE_FCM_TOKEN = "e2e-fake-fcm-registration-token";

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
