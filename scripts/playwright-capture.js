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
          case "hold":
            break;
          case "arrow":
            // Big-arrow-on-the-screen port (in-video version): draw a big
            // friendly arrow + label pointing at a selector or x,y coords.
            // MIT idea credit: franzenzenhofer/big-arrow-on-the-screen.
            // Unlike bigarrow there is no OS overlay - this is a DOM overlay
            // baked into the recording. Missing target = skip, never abort.
            await currentPage.evaluate((opts) => {
              const prev = document.getElementById("__demo_vid_arrow");
              if (prev) prev.remove();
              const COLORS = {
                red: "#ef4444", orange: "#f97316", yellow: "#eab308",
                green: "#22c55e", teal: "#14b8a6", blue: "#3b82f6",
                purple: "#a855f7", pink: "#ec4899", black: "#111111",
                white: "#ffffff",
              };
              const color = COLORS[opts.color] || opts.color || "#ef4444";
              const SIZES = { S: 0.75, M: 1, L: 1.4 };
              const scale = SIZES[opts.size] || 1;
              let x = null, y = null, w = 0, h = 0;
              if (opts.target) {
                try {
                  const el = document.querySelector(opts.target);
                  if (el) {
                    const r = el.getBoundingClientRect();
                    x = r.left + r.width / 2; y = r.top + r.height / 2;
                    w = r.width; h = r.height;
                  }
                } catch { /* bad selector -> fall through to at */ }
              }
              if (x === null && opts.at) {
                const parts = String(opts.at).split(",").map((s) => parseFloat(s.trim()));
                if (parts.length === 2 && parts.every((n) => Number.isFinite(n))) {
                  x = parts[0]; y = parts[1];
                }
              }
              if (x === null) return; // no target, draw nothing
              const style = opts.style || "arrow";
              const box = document.createElement("div");
              box.id = "__demo_vid_arrow";
              Object.assign(box.style, {
                position: "fixed", left: "0", top: "0", width: "100vw", height: "100vh",
                zIndex: "999997", pointerEvents: "none",
                fontFamily: "system-ui, sans-serif",
              });
              const label = String(opts.text || "");
              // Pulsing ring/box highlight around the target.
              const ring = document.createElement("div");
              const pad = 10 * scale + Math.max(w, h) * 0.1;
              Object.assign(ring.style, {
                position: "absolute",
                left: `${Math.max(0, x - w / 2 - pad)}px`,
                top: `${Math.max(0, y - h / 2 - pad)}px`,
                width: `${w + pad * 2}px`,
                height: `${h + pad * 2}px`,
                border: `${4 * scale}px solid ${color}`,
                borderRadius: style === "box" ? "8px" : "50%",
                boxShadow: "0 2px 12px rgba(0,0,0,0.5)",
                animation: "__demo_vid_pulse 1s ease-in-out infinite alternate",
              });
              box.appendChild(ring);
              if (style === "arrow") {
                // Label sign above-left of target + SVG shaft pointing down-right.
                const sign = document.createElement("div");
                sign.textContent = label;
                Object.assign(sign.style, {
                  position: "absolute",
                  left: `${Math.max(8, x - 260 * scale)}px`,
                  top: `${Math.max(8, y - 140 * scale)}px`,
                  background: color, color: "#fff",
                  fontWeight: "800", fontSize: `${20 * scale}px`,
                  padding: `${10 * scale}px ${16 * scale}px`,
                  borderRadius: "12px", maxWidth: "320px",
                  boxShadow: "0 4px 16px rgba(0,0,0,0.5)",
                  lineHeight: "1.3",
                });
                box.appendChild(sign);
                const svgNS = "http://www.w3.org/2000/svg";
                const svg = document.createElementNS(svgNS, "svg");
                Object.assign(svg.style, {
                  position: "absolute", left: "0", top: "0",
                  width: "100vw", height: "100vh", overflow: "visible",
                });
                const sx = Math.max(8, x - 260 * scale) + 40 * scale;
                const sy = Math.max(8, y - 140 * scale) + 44 * scale;
                const line = document.createElementNS(svgNS, "line");
                line.setAttribute("x1", sx); line.setAttribute("y1", sy);
                line.setAttribute("x2", x); line.setAttribute("y2", y);
                line.setAttribute("stroke", color);
                line.setAttribute("stroke-width", String(8 * scale));
                line.setAttribute("stroke-linecap", "round");
                svg.appendChild(line);
                const head = document.createElementNS(svgNS, "polygon");
                const hs = 22 * scale;
                head.setAttribute("points", `0,${-hs} ${hs * 0.9},0 0,${hs} ${-hs * 0.35},0`);
                head.setAttribute("fill", color);
                const ang = Math.atan2(y - sy, x - sx) * 180 / Math.PI;
                head.setAttribute("transform", `translate(${x},${y}) rotate(${ang})`);
                svg.appendChild(head);
                box.appendChild(svg);
              } else if (label) {
                const tag = document.createElement("div");
                tag.textContent = label;
                Object.assign(tag.style, {
                  position: "absolute", left: `${x + w / 2 + 14}px`, top: `${y - 18}px`,
                  background: color, color: "#fff", fontWeight: "700",
                  fontSize: `${16 * scale}px`, padding: "6px 12px",
                  borderRadius: "8px", boxShadow: "0 4px 16px rgba(0,0,0,0.5)",
                  whiteSpace: "nowrap",
                });
                box.appendChild(tag);
              }
              const css = document.createElement("style");
              css.textContent = "@keyframes __demo_vid_pulse{from{opacity:1}to{opacity:0.55}}";
              box.appendChild(css);
              document.documentElement.appendChild(box);
            }, { target: step.target, at: step.at, text: step.text, color: step.color, style: step.style, size: step.size });
            break;
          case "end": {
            // Clear any lingering overlay before the final hold/fade so the
            // closing frame shows the real page, not a stale title card.
            await currentPage.evaluate(() => {
              const prev = document.getElementById("__demo_vid_overlay");
              if (prev) prev.remove();
              const arrow = document.getElementById("__demo_vid_arrow");
              if (arrow) arrow.remove();
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
