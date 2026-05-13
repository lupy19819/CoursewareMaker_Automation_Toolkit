/**
 * 上传运动PK配置到指定游戏（修复版）
 * 修复：credentials: 'include' + POST 方法
 */
const fs = require("fs");
const { chromium } = require("playwright");

async function main() {
  const [, , gameId, configPath] = process.argv;
  if (!gameId || !configPath) {
    console.error("Usage: node upload_yundongpk_fixed.js <gameId> <configPath>");
    process.exit(1);
  }

  if (!fs.existsSync(configPath)) {
    console.error(`Config file not found: ${configPath}`);
    process.exit(1);
  }

  const configText = fs.readFileSync(configPath, "utf8");
  const configObject = JSON.parse(configText);

  console.log(`Uploading to game ${gameId}...`);

  const browser = await chromium.connectOverCDP("http://127.0.0.1:9222");
  const context = browser.contexts()[0];
  const page = context.pages().find((p) =>
    (p.url() || "").includes("coursewaremaker.speiyou.com")
  );
  if (!page) {
    throw new Error("No CoursewareMaker page found.");
  }

  const result = await page.evaluate(
    async ({ gameId, configObject }) => {
      const token = localStorage.getItem("GAMEMAKER_TOKEN") || "";
      if (!token) throw new Error("GAMEMAKER_TOKEN missing");

      // 1. 获取游戏详情（带 credentials）
      const getRes = await fetch(
        `https://sszt-gateway.speiyou.com/beibo/game/config/game?game_id=${gameId}`,
        {
          credentials: "include",
          headers: { beibotoken: token },
        }
      );
      const detailText = await getRes.text();
      let detail;
      try {
        detail = JSON.parse(detailText);
      } catch (e) {
        return { error: "parse detail: " + detailText.slice(0, 100) };
      }
      if (!detail || detail.code !== 0 || !detail.result) {
        return { error: "get detail failed: " + JSON.stringify(detail).slice(0, 200) };
      }

      // 2. 构建 payload（configuration 传对象，同时修正元数据）
      const payload = {
        ...detail.result,
        configuration: configObject,
        // ⚠️ 必须修正这三个字段，否则 Vue 组件初始化报 TypeError
        game_type: 2,          // 1=草稿模板 2=正式游戏，错误时 Vue 读 engine_version.length 崩溃
        version: "1.2",        // 0.0 会导致编辑器行为异常
        engine_version: "3.X", // 空字符串时 .length 读取 undefined
      };

      // 3. POST 保存（带 credentials）
      const saveRes = await fetch(
        "https://sszt-gateway.speiyou.com/beibo/game/config/game",
        {
          method: "PUT",
          credentials: "include",
          headers: {
            "Content-Type": "application/json;charset=UTF-8",
            beibotoken: token,
          },
          body: JSON.stringify(payload),
        }
      );
      const saveText = await saveRes.text();

      // 4. 验证
      const verifyRes = await fetch(
        `https://sszt-gateway.speiyou.com/beibo/game/config/game?game_id=${gameId}`,
        {
          credentials: "include",
          headers: { beibotoken: token },
        }
      );
      const verify = await verifyRes.json();

      return {
        save: saveText.slice(0, 200),
        verify: {
          game_id: verify?.result?.game_id,
          game_name: verify?.result?.game_name,
          cfg_len: (verify?.result?.configuration || "").length,
        },
      };
    },
    { gameId, configObject }
  );

  console.log(JSON.stringify(result, null, 2));
  await browser.close();
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
