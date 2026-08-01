/**
 * Playwright capture script for demo-vid-mcp.
 * Usage: node scripts/playwright-capture.js <steps.json> <output-base> [theme]
 *
 * Accepts a JSON array of steps, records browser interactions as .webm.
 * theme: "dark" (default) | "light" — forces the fleet theme class on the
 * page so demo videos match the requested mode (see chat_skills_prefab_standard
 * §7.1: webapps with the optional light toggle must be forced before capture).
 * Fails if the page appears blank or returns an error status.
 */
const { chromium } = require("playwright");
const fs = require("fs");
const path = require("path");

async function main() {
  const [stepsPath, outputBase, themeArg] = process.argv.slice(2);
  if (!stepsPath || !outputBase) {
    console.error("Usage: node playwright-capture.js <steps.json> <output-base> [dark|light]");
    process.exit(1);
  }
  const theme = themeArg === "light" ? "light" : "dark";

  const steps = JSON.parse(fs.readFileSync(stepsPath, "utf8"));
  const outputDir = path.dirname(outputBase);
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    viewport: { width: 1280, height: 720 },
    deviceScaleFactor: 1,
    recordVideo: { dir: outputDir, size: { width: 1280, height: 720 } },
  });
  const page = await context.newPage();

  // Force the requested theme on every navigation (fleet dark default, or
  // light for bright videos). Handles both the class toggle and localStorage
  // persistence used by fleet light-mode toggles.
  await page.addInitScript((mode) => {
    const dark = mode === "dark";
    document.documentElement.classList.toggle("dark", dark);
    try {
      const key = "ocmcp-light-mode";
      if (localStorage.getItem(key) !== null) {
        localStorage.setItem(key, dark ? "0" : "1");
      }
    } catch { /* cross-origin / privacy mode */ }
  }, theme);

  for (const step of steps) {
    try {
      switch (step.action) {
        case "goto": {
          const resp = await page.goto(step.url, { waitUntil: "load", timeout: 15000 });
          if (resp && resp.status() >= 400) {
            console.error(`HTTP ${resp.status()} at ${step.url} — aborting`);
            process.exit(1);
          }
          const bodyText = await page.evaluate(() => document.body?.innerText?.trim() || "");
          const bodyHtml = await page.evaluate(() => document.body?.innerHTML?.trim() || "");
          if (!bodyHtml || bodyHtml === "<div id=\"root\"></div>" || bodyHtml.length < 10) {
            console.error(`Blank page at ${step.url} — target webapp may not be running`);
            process.exit(1);
          }
          break;
        }
        case "click":
          try { await page.click(step.target, { timeout: 5000 }); } catch { /* ok */ }
          break;
        case "type":
          try { await page.fill(step.target, step.text || ""); } catch { /* ok */ }
          break;
        case "end":
          break;
      }
      if (step.wait) await page.waitForTimeout(step.wait * 1000);
    } catch (err) {
      console.error("Step failed:", step.action, err.message);
      process.exit(1);
    }
  }

  await context.close();
  await browser.close();

  if (fs.existsSync(outputDir)) {
    const files = fs.readdirSync(outputDir).filter(f => f.endsWith(".webm"));
    if (files.length > 0) {
      const src = path.join(outputDir, files[0]);
      const dst = outputBase.endsWith(".webm") ? outputBase : outputBase + ".webm";
      try { fs.renameSync(src, dst); } catch { /* ok */ }
    }
  }
  process.exit(0);
}

main().catch((err) => {
  console.error(err.message);
  process.exit(1);
});
