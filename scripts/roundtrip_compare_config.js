#!/usr/bin/env node
/**
 * Fetch a CoursewareMaker game's online configuration and compare it with a
 * local config using canonical JSON ordering.
 */
const fs = require("fs");
const path = require("path");
const { chromium } = require("playwright");

function usage() {
  console.error("Usage: node scripts/roundtrip_compare_config.js <game_id> <local_config.json> [remote_output.json]");
}

function canonical(value) {
  if (Array.isArray(value)) return value.map(canonical);
  if (value && typeof value === "object") {
    return Object.fromEntries(Object.keys(value).sort().map((key) => [key, canonical(value[key])]));
  }
  return value;
}

function parseConfig(value) {
  if (typeof value === "string") return JSON.parse(value);
  if (value && typeof value === "object" && value.result && value.result.configuration) {
    return parseConfig(value.result.configuration);
  }
  if (value && typeof value === "object" && typeof value.configuration === "string") {
    return parseConfig(value.configuration);
  }
  return value;
}

async function main() {
  const [, , gameId, localConfigPath, remoteOutputArg] = process.argv;
  if (!gameId || !localConfigPath) {
    usage();
    process.exit(1);
  }

  const chromePort = process.env.CHROME_PORT || "9222";
  const localConfig = parseConfig(JSON.parse(fs.readFileSync(localConfigPath, "utf8")));
  const remoteOutput =
    remoteOutputArg ||
    path.join("output", "roundtrip", `${gameId.replace(/[^a-zA-Z0-9_-]/g, "_")}.remote.config.json`);

  const browser = await chromium.connectOverCDP(`http://127.0.0.1:${chromePort}`);
  const context = browser.contexts()[0];
  const page =
    context.pages().find((p) => (p.url() || "").includes("coursewaremaker.speiyou.com")) ||
    (await context.newPage());

  const detail = await page.evaluate(async (gameId) => {
    const token = localStorage.getItem("GAMEMAKER_TOKEN") || "";
    if (!token) throw new Error("GAMEMAKER_TOKEN missing");
    const res = await fetch(
      `https://sszt-gateway.speiyou.com/beibo/game/config/game?game_id=${gameId}`,
      { credentials: "include", headers: { beibotoken: token } }
    );
    return await res.json();
  }, gameId);

  await browser.close();

  if (!detail || detail.code !== 0 || !detail.result) {
    throw new Error(`get detail failed: ${JSON.stringify(detail).slice(0, 300)}`);
  }

  const remoteConfig = parseConfig(detail.result.configuration);
  fs.mkdirSync(path.dirname(remoteOutput), { recursive: true });
  fs.writeFileSync(remoteOutput, JSON.stringify(remoteConfig, null, 2));

  const localCanonical = JSON.stringify(canonical(localConfig));
  const remoteCanonical = JSON.stringify(canonical(remoteConfig));
  const result = {
    game_id: detail.result.game_id,
    game_name: detail.result.game_name,
    save_time: detail.result.save_time,
    remote_output: remoteOutput,
    canonical_match: localCanonical === remoteCanonical,
    local_len: localCanonical.length,
    remote_len: remoteCanonical.length,
  };
  console.log(JSON.stringify(result, null, 2));
  if (!result.canonical_match) process.exit(2);
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
