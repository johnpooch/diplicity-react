import { chromium } from "playwright";

const resolveExecutablePath = async () => {
  try {
    const probe = await chromium.launch({ headless: true });
    await probe.close();
    return undefined;
  } catch {
    const sparticuz = (await import("@sparticuz/chromium")).default;
    return sparticuz.executablePath();
  }
};

const executablePath = await resolveExecutablePath();
const browser = await chromium.launch({
  headless: true,
  executablePath,
  args: ["--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage"],
});

const context = await browser.newContext({ viewport: { width: 1280, height: 900 } });
const page = await context.newPage();

page.on("pageerror", error => console.error("[pageerror]", error.message));

await page.goto("http://localhost:5173/create-game", { waitUntil: "networkidle", timeout: 60000 });
await page.waitForTimeout(1500);

// Click Next to go to step 2 (Deadlines)
const nextBtn = page.getByRole("button", { name: "Next" });
await nextBtn.click();
await page.waitForTimeout(1000);

await page.screenshot({ path: "/tmp/shots/create-game-deadlines.png" });
console.log("Saved create-game-deadlines.png");

await browser.close();
