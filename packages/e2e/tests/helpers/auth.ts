import { execSync } from "child_process";
import { Page } from "@playwright/test";

interface TestUserTokens {
  accessToken: string;
  refreshToken: string;
  email: string;
  name: string;
}

function createTestUser(
  email = "test@e2e.local",
  name = "E2E Test User"
): TestUserTokens {
  const output = execSync(
    `docker exec diplicity-service python3 manage.py create_test_user --email "${email}" --name "${name}"`,
    { encoding: "utf-8" }
  );
  return JSON.parse(output.trim());
}

async function loginAsTestUser(
  page: Page,
  tokens?: TestUserTokens
): Promise<void> {
  const userTokens = tokens ?? createTestUser();
  await page.evaluate((t) => {
    localStorage.setItem("accessToken", t.accessToken);
    localStorage.setItem("refreshToken", t.refreshToken);
    localStorage.setItem("email", t.email);
    localStorage.setItem("name", t.name);
  }, userTokens);
}

export { createTestUser, loginAsTestUser };
export type { TestUserTokens };
