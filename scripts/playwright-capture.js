/**
 * Playwright capture script for demo-vid-mcp.
 * Usage: node scripts/playwright-capture.js <steps.json> <output-path-without-ext>
 *
 * Accepts a JSON array of steps, records browser interactions as .webm
 * via Playwright's native video recording.
 */
const { chromium } = require("playwright");
const fs = require("fs");
const path = require("path");

async function main() {
  const [stepsPath, outputBase] = process.argv.slice(2);
  if (!stepsPath || !outputBase) {
    console.error("Usage: node playwright-capture.js <steps.json> <output-basename>");
    process.exit(1);
  }

  const steps = JSON.parse(fs.readFileSync(stepsPath, "utf8"));
  const outputDir = path.dirname(outputBase);
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    viewport: { width: 1280, height: 720 },
    deviceScaleFactor: 1,
    recordVideo: { dir: outputDir, size: { width: 1280, height: 720 } },
  });
  const page = await context.newPage();

  for (const step of steps) {
    try {
      switch (step.action) {
        case "goto":
          await page.goto(step.url, { waitUntil: "networkidle", timeout: 15000 });
          break;
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
    }
  }

  await context.close();
  await browser.close();

  // Playwright saves video as {dir}/{calculated-name}.webm
  // Rename it predictably
  if (fs.existsSync(outputDir)) {
    const files = fs.readdirSync(outputDir).filter(f => f.endsWith(".webm"));
    if (files.length > 0) {
      const src = path.join(outputDir, files[0]);
      const dst = outputBase.endsWith(".webm") ? outputBase : outputBase + ".webm";
      fs.renameSync(src, dst);
    }
  }
  process.exit(0);
}

main().catch((err) => {
  console.error(err.message);
  process.exit(1);
});
