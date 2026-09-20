// Resolves a usable Chromium for Playwright across environments.
//
// CI images ship the browser build Playwright expects, so the default launch
// works. Sandboxes often carry a mismatched build; PLAYWRIGHT_CHROMIUM_PATH
// points at one, and @sparticuz/chromium is the last resort.

import { chromium } from "playwright";

export const resolveExecutablePath = async () => {
  const override = process.env.PLAYWRIGHT_CHROMIUM_PATH;
  if (override) return override;
  try {
    const probe = await chromium.launch({ headless: true });
    await probe.close();
    return undefined;
  } catch {
    const sparticuz = (await import("@sparticuz/chromium")).default;
    return sparticuz.executablePath();
  }
};

export const launchChromium = async () =>
  chromium.launch({
    headless: true,
    executablePath: await resolveExecutablePath(),
    args: ["--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage"],
  });
