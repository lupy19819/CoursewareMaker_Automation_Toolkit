const fs = require("fs");
const { chromium } = require("playwright");

/**
 * 保存游戏配置到 CoursewareMaker 服务器（via CDP port 9223）
 *
 * ⚠️ 历史 BUG 记录（2026-04-28 修复，禁止重犯）：
 *
 * BUG-1: 传入外层 API 响应壳子
 *   错误做法：把 fetch 到的 output/xxx_current.json（结构 {code,result,msg}）直接作为 configPath 传入
 *             → 导致 configuration 字段被存成三层嵌套，前端解析时报 "Cannot read properties of undefined (reading 'length')"
 *   正确做法：传入只包含内层配置对象 {additional,common,components,game} 的文件，
 *             OR 传入外层响应文件时脚本会自动 unwrap（见下方代码）
 *
 * BUG-2: 配置验证路径错误
 *   贪吃小怪兽组件数据在 game[lvl].components[i].component_data.states，
 *   不在 game[lvl].components[i].events，
 *   字段名是 state（'default','clickEnd','compLoadFinish','level_correct'），label 是中文显示名
 *
 * 上传前必须运行校验：
 *   python3 scripts/validate_monster_config.py <file.json> <关卡数>
 */

async function main() {
  const [, , gameId, configPath, verifyMarker = ""] = process.argv;
  if (!gameId || !configPath) {
    throw new Error("Usage: node save_game_config_via_cdp.js <gameId> <configPath> [verifyMarker]");
  }

  const configText = fs.readFileSync(configPath, "utf8");
  const configObject = JSON.parse(configText);
  const browser = await chromium.connectOverCDP("http://127.0.0.1:9223");
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

      // ── 配置 unwrap 逻辑（支持两种输入格式）────────────────────────────────
      // 服务器 PUT 接受 configuration 为 JS 对象（服务器自行序列化存储）
      //
      // 格式A：外层 API 响应壳子 {code, result: {configuration: "<JSON string>"}, msg}
      //   → 取 result.configuration 再 JSON.parse → 内层配置对象
      //   → 适用于直接把 fetch 回来的 current.json 传入的场景
      //
      // 格式B：纯内层配置对象 {additional_custom_game/additional, common, components, custom_game/game, ...}
      //   → 直接传入，不做任何转换
      //   → 适用于 build_yundong_pk_config.py / fix_j8_monster.py 生成的 fixed.json
      //
      // ⚠️ 禁止把格式A文件（含code/result/msg外壳）直接当格式B传入，否则三层嵌套导致前端崩溃
      let innerConfig = configObject;
      if (configObject && typeof configObject.code === 'number' && configObject.result && configObject.result.configuration) {
        // 格式A：外层响应壳子 → unwrap
        innerConfig = JSON.parse(configObject.result.configuration);
        console.warn("[save] 检测到外层API响应壳子，已自动 unwrap 取内层配置");
      }
      // 格式B：纯配置对象，直接使用
      const payload = { ...detail.result, configuration: innerConfig };
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
