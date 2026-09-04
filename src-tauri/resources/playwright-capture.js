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
  const [stepsPath, outputBase, themeArg, aspectArg, resArg] = process.argv.slice(2);
  if (!stepsPath || !outputBase) {
    console.error("Usage: node playwright-capture.js <steps.json> <output-base> [dark|light] [16:9|9:16] [720p|1080p]");
    process.exit(1);
  }
  const theme = themeArg === "light" ? "light" : "dark";
  const isVertical = aspectArg === "9:16";
  const is1080p = resArg === "1080p";

  let width = 1280;
  let height = 720;
  if (isVertical) {
    width = is1080p ? 1080 : 720;
    height = is1080p ? 1920 : 1280;
  } else if (is1080p) {
    width = 1920;
    height = 1080;
  }

  const steps = JSON.parse(fs.readFileSync(stepsPath, "utf8"));
  const outputDir = path.dirname(outputBase);
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    viewport: { width, height },
    deviceScaleFactor: 1,
    recordVideo: { dir: outputDir, size: { width, height } },
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

  // Inject visual click ripples on user click interactions
  await page.addInitScript(() => {
    window.addEventListener(
      "click",
      (e) => {
        const circle = document.createElement("div");
        circle.style.position = "fixed";
        circle.style.left = `${e.clientX - 16}px`;
        circle.style.top = `${e.clientY - 16}px`;
        circle.style.width = "32px";
        circle.style.height = "32px";
        circle.style.borderRadius = "50%";
        circle.style.backgroundColor = "rgba(245, 158, 11, 0.4)";
        circle.style.border = "2px solid rgba(245, 158, 11, 0.9)";
        circle.style.pointerEvents = "none";
        circle.style.zIndex = "999999";
        circle.style.transform = "scale(0.5)";
        circle.style.transition = "transform 0.4s ease-out, opacity 0.4s ease-out";
        circle.style.opacity = "1";
        document.documentElement.appendChild(circle);

        requestAnimationFrame(() => {
          circle.style.transform = "scale(1.8)";
          circle.style.opacity = "0";
        });

        setTimeout(() => {
          circle.remove();
        }, 450);
      },
      true,
    );
  });


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
