/**
 * Playwright capture script for demo-vid-mcp.
 * Usage: node scripts/playwright-capture.js <steps.json> <output-base> [theme] [aspect] [res]
 *
 * Accepts a JSON array of steps, records browser interactions as .webm.
 * theme: "dark" (default) | "light" — forces the fleet theme class on the
 * page so demo videos match the requested mode (see chat_skills_prefab_standard
 * §7.1: webapps with the optional light toggle must be forced before capture).
 * Fails if the page appears blank or returns an error status.
 *
 * Records one clip PER page-visit segment (a run of steps starting at a
 * "goto" and continuing until the next "goto" or the end), not one
 * continuous recording — each "goto" opens a fresh Playwright page (Chromium
 * tab) in the same recording context, and closing a page finalizes its own
 * .webm. This lets recorder.py/pipeline/vfx.py join the clips with real
 * crossfade/wipe/slide transitions between pages instead of a single flat
 * capture. Emits <output-base>.clips.json listing the resulting clip paths
 * in order; recorder.py stitches them.
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

  // Context-level addInitScript applies to every page created in this
  // context, past and future - required now that recording spans multiple
  // pages (one per goto-delimited segment) instead of a single page, so
  // each new page still gets the theme forced and click ripples wired up
  // without re-registering per page.
  await context.addInitScript((mode) => {
    const dark = mode === "dark";
    document.documentElement.classList.toggle("dark", dark);
    try {
      const key = "ocmcp-light-mode";
      if (localStorage.getItem(key) !== null) {
        localStorage.setItem(key, dark ? "0" : "1");
      }
    } catch { /* cross-origin / privacy mode */ }
  }, theme);

  await context.addInitScript(() => {
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

  const clips = [];
  let currentPage = null;

  async function finalizeSegment() {
    if (!currentPage) return;
    const video = currentPage.video();
    await currentPage.close();
    if (video) {
      try {
        clips.push(await video.path());
      } catch (err) {
        console.error("Failed to finalize clip:", err.message);
      }
    }
    currentPage = null;
  }

  for (const step of steps) {
    try {
      if (step.action === "goto") {
        await finalizeSegment();
        currentPage = await context.newPage();
        const resp = await currentPage.goto(step.url, { waitUntil: "load", timeout: 15000 });
        if (resp && resp.status() >= 400) {
          console.error(`HTTP ${resp.status()} at ${step.url} — aborting`);
          process.exit(1);
        }
        const bodyHtml = await currentPage.evaluate(() => document.body?.innerHTML?.trim() || "");
        if (!bodyHtml || bodyHtml === "<div id=\"root\"></div>" || bodyHtml.length < 10) {
          console.error(`Blank page at ${step.url} — target webapp may not be running`);
          process.exit(1);
        }
      } else {
        if (!currentPage) currentPage = await context.newPage();
        switch (step.action) {
          case "click":
            try { await currentPage.click(step.target, { timeout: 5000 }); } catch { /* ok */ }
            break;
          case "type":
            try { await currentPage.fill(step.target, step.text || ""); } catch { /* ok */ }
            break;
          case "text_overlay":
            await currentPage.evaluate((text) => {
              const prev = document.getElementById("__demo_vid_overlay");
              if (prev) prev.remove();
              const el = document.createElement("div");
              el.id = "__demo_vid_overlay";
              el.textContent = text || "";
              Object.assign(el.style, {
                position: "fixed",
                inset: "0",
                zIndex: "999998",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                textAlign: "center",
                padding: "10%",
                background: "rgba(9, 9, 11, 0.92)",
                color: "#fafafa",
                fontFamily: "system-ui, sans-serif",
                fontSize: "clamp(24px, 4vw, 56px)",
                fontWeight: "700",
                lineHeight: "1.4",
                whiteSpace: "pre-wrap",
              });
              document.documentElement.appendChild(el);
            }, step.text || "");
            break;
          case "end": {
            // Clear any lingering overlay before the final hold/fade so the
            // closing frame shows the real page, not a stale title card.
            await currentPage.evaluate(() => {
              const prev = document.getElementById("__demo_vid_overlay");
              if (prev) prev.remove();
            }).catch(() => {});
            break;
          }
          // "sfx" and any other action type: no on-page effect - resolved
          // and mixed in separately as timed audio (see pipeline/sfx.py).
          // Falls through here as a no-op, same as an unrecognized action.
        }
      }
      if (step.wait) await currentPage.waitForTimeout(step.wait * 1000);
    } catch (err) {
      console.error("Step failed:", step.action, err.message);
      process.exit(1);
    }
  }
  await finalizeSegment();

  await context.close();
  await browser.close();

  const manifestPath = `${outputBase}.clips.json`;
  if (clips.length === 1) {
    const dst = outputBase.endsWith(".webm") ? outputBase : `${outputBase}.webm`;
    try {
      fs.renameSync(clips[0], dst);
      clips[0] = dst;
    } catch { /* keep original path if rename fails */ }
  }
  fs.writeFileSync(manifestPath, JSON.stringify(clips));

  process.exit(0);
}

main().catch((err) => {
  console.error(err.message);
  process.exit(1);
});
