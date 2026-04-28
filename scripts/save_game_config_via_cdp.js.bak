const fs = require("fs");
const { chromium } = require("playwright");

async function main() {
  const [, , gameId, configPath, verifyMarker = ""] = process.argv;
  if (!gameId || !configPath) {
    throw new Error("Usage: node save_game_config_via_cdp.js <gameId> <configPath> [verifyMarker]");
  }

  const configText = fs.readFileSync(configPath, "utf8");
  const configObject = JSON.parse(configText);
  const browser = await chromium.connectOverCDP("http://127.0.0.1:9222");
  const context = browser.contexts()[0];
  const page = context.pages().find((p) => (p.url() || "").includes("coursewaremaker.speiyou.com"));
  if (!page) {
    throw new Error("No CoursewareMaker page found in the attached Chrome.");
  }

  const result = await page.evaluate(
    async ({ gameId, configObject, verifyMarker }) => {
      const token = localStorage.getItem("GAMEMAKER_TOKEN") || "";
      if (!token) {
        throw new Error("GAMEMAKER_TOKEN missing");
      }

      const getRes = await fetch(`https://sszt-gateway.speiyou.com/beibo/game/config/game?game_id=${gameId}`, {
        headers: { beibotoken: token },
      });
      const detail = await getRes.json();
      if (!detail || detail.code !== 0 || !detail.result) {
        throw new Error(`get detail failed: ${JSON.stringify(detail)}`);
      }

      const payload = { ...detail.result, configuration: configObject };
      const putRes = await fetch("https://sszt-gateway.speiyou.com/beibo/game/config/game", {
        method: "PUT",
        headers: {
          "Content-Type": "application/json;charset=UTF-8",
          beibotoken: token,
        },
        body: JSON.stringify(payload),
      });
      const putJson = await putRes.json();

      const verifyRes = await fetch(`https://sszt-gateway.speiyou.com/beibo/game/config/game?game_id=${gameId}`, {
        headers: { beibotoken: token },
      });
      const verify = await verifyRes.json();
      const raw = verify?.result?.configuration || "";
      return {
        put: putJson,
        verify: {
          game_id: verify?.result?.game_id,
          game_name: verify?.result?.game_name,
          save_time: verify?.result?.save_time,
          update_time: verify?.result?.update_time,
          raw_len: raw.length,
          config_prefix: typeof raw === "string" ? raw.slice(0, 40) : "",
          double_encoded: typeof raw === "string" ? raw.startsWith("\"{") : null,
          has_marker: verifyMarker ? raw.includes(verifyMarker) : null,
        },
      };
    },
    { gameId, configObject, verifyMarker }
  );

  console.log(JSON.stringify(result, null, 2));
  await browser.close();
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
