/**
 * 通过 CDP 保存游戏配置到 CoursewareMaker
 * 关键修复：fetch 必须带 credentials: 'include' 才能正确发送 cookies
 * 工作流：GET 现有游戏详情 → PUT 更新原 game_id 的 configuration
 */
const fs = require("fs");
const { chromium } = require("playwright");

async function main() {
  const [, , gameId, configPath, verifyMarker = ""] = process.argv;
  if (!gameId || !configPath) {
    console.error("Usage: node save_game_config_via_cdp.js <gameId> <configPath> [verifyMarker]");
    process.exit(1);
  }

  const configText = fs.readFileSync(configPath, "utf8");
  const configObject = JSON.parse(configText);

  const _port = process.env.CHROME_PORT || 9222; const browser = await chromium.connectOverCDP("http://127.0.0.1:" + _port);
  const context = browser.contexts()[0];
  const page = context.pages().find((p) =>
    (p.url() || "").includes("coursewaremaker.speiyou.com")
  );
  if (!page) {
    throw new Error("No CoursewareMaker page found in the attached Chrome.");
  }

  const result = await page.evaluate(
    async ({ gameId, configObject, verifyMarker }) => {
      const token = localStorage.getItem("GAMEMAKER_TOKEN") || "";
      if (!token) {
        throw new Error("GAMEMAKER_TOKEN missing");
      }

      // 关键修复：必须加 credentials: 'include' 才能正确获取 cookies/session
      const getRes = await fetch(
        `https://sszt-gateway.speiyou.com/beibo/game/config/game?game_id=${gameId}`,
        {
          credentials: "include",
          headers: { beibotoken: token },
        }
      );
      const detail = await getRes.json();
      if (!detail || detail.code !== 0 || !detail.result) {
        throw new Error(`get detail failed: ${JSON.stringify(detail).slice(0, 200)}`);
      }

      // 配置可能是 API 响应壳子 {code,result,configuration} → unwrap 取内层
      let innerConfig = configObject;
      if (configObject && typeof configObject.code === 'number' && configObject.result && configObject.result.configuration) {
        innerConfig = JSON.parse(configObject.result.configuration);
        console.warn("[save] 检测到外层API响应壳子，已自动 unwrap");
      }

      // 排除 components（组件库模板，~32MB）等大字段
      const { components: _omitComponents, ...detailMeta } = detail.result;

      // 更新已有游戏使用 PUT。POST 在部分已有 game_id 上会被平台当成新建/另存版本，
      // 可能返回“游戏名字重复，请从修改入口进入”。
      const payload = {
        ...detailMeta,
        configuration: innerConfig,
      };

      const saveRes = await fetch(
        "https://sszt-gateway.speiyou.com/beibo/game/config/game",
        {
          method: "PUT",
          credentials: "include", // 关键修复
          headers: {
            "Content-Type": "application/json;charset=UTF-8",
            beibotoken: token,
          },
          body: JSON.stringify(payload),
        }
      );
      const saveJson = await saveRes.json();

      // 验证写入
      const verifyRes = await fetch(
        `https://sszt-gateway.speiyou.com/beibo/game/config/game?game_id=${gameId}`,
        {
          credentials: "include",
          headers: { beibotoken: token },
        }
      );
      const verify = await verifyRes.json();
      const raw = verify?.result?.configuration || "";

      return {
        save: saveJson,
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
