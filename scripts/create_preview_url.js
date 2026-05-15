#!/usr/bin/env node
/**
 * Create a CoursewareMaker preview URL for one game.
 */
const fs = require("fs");
const path = require("path");
const { chromium } = require("playwright");

async function main() {
  const [, , gameId, outputArg] = process.argv;
  if (!gameId) {
    console.error("Usage: node scripts/create_preview_url.js <game_id> [output.json]");
    process.exit(1);
  }

  const chromePort = process.env.CHROME_PORT || "9222";
  const outputPath = outputArg || path.join("output", "share_links", `${gameId}.preview.json`);
  const browser = await chromium.connectOverCDP(`http://127.0.0.1:${chromePort}`);
  const context = browser.contexts()[0];
  const page =
    context.pages().find((p) => (p.url() || "").includes("coursewaremaker.speiyou.com")) ||
    (await context.newPage());

  const result = await page.evaluate(async (gameId) => {
    const token = localStorage.getItem("GAMEMAKER_TOKEN") || "";
    if (!token) throw new Error("GAMEMAKER_TOKEN missing");
    const res = await fetch("https://sszt-gateway.speiyou.com/beibo/game/config/createPreviewUrl", {
      method: "POST",
      credentials: "include",
      headers: { "content-type": "application/json;charset=UTF-8", beibotoken: token },
      body: JSON.stringify({
        game_id: gameId,
        base_preview_url: "https://coursewaremaker.speiyou.com/#/share-preview",
      }),
    });
    return await res.json();
  }, gameId);

  await browser.close();
  if (!result || result.code !== 0) {
    throw new Error(`create preview failed: ${JSON.stringify(result).slice(0, 300)}`);
  }
  const payload = { gameId, ...result.result };
  fs.mkdirSync(path.dirname(outputPath), { recursive: true });
  fs.writeFileSync(outputPath, JSON.stringify(payload, null, 2));
  console.log(JSON.stringify({ ...payload, output: outputPath }, null, 2));
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
