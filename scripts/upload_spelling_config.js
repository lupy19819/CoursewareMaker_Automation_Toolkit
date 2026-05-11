#!/usr/bin/env node
/**
 * upload_spelling_config.js
 * 
 * 上传单词拼拼乐配置到服务器。
 * 自动处理：
 *   1. 配置文件格式（内层配置 or 外层壳子均可）
 *   2. Token 获取（从调试 Chrome 读，支持 9222/9223 两个端口）
 *   3. Chrome 未开时自动提示
 * 
 * 用法：
 *   node scripts/upload_spelling_config.js <game_id> [config_path]
 *   config_path 默认 output/spelling_test_config.json
 */

const fs = require("fs");
const http = require("http");
const WebSocket = require("ws");

const [,, gameId, configPath = "output/spelling_test_config.json"] = process.argv;

if (!gameId) {
  console.error("Usage: node upload_spelling_config.js <game_id> [config_path]");
  process.exit(1);
}

// ── 1. 读取并解包配置 ──────────────────────────────────────────────
const raw = JSON.parse(fs.readFileSync(configPath, "utf8"));
let innerConfig;
if (raw && typeof raw.code === "number" && raw.result?.configuration) {
  // 外层壳子格式 {code, result: {configuration: "..."}, msg}
  innerConfig = typeof raw.result.configuration === "string"
    ? JSON.parse(raw.result.configuration)
    : raw.result.configuration;
  console.log("[upload] 检测到外层壳子，已自动解包");
} else {
  // 内层配置格式（直接是 {additional, common, game, ...}）
  innerConfig = raw;
  console.log("[upload] 直接使用内层配置");
}

// 基本校验
if (!innerConfig.game || !Array.isArray(innerConfig.game)) {
  console.error("[upload] ❌ 配置结构异常：缺少 game 字段");
  process.exit(1);
}
console.log(`[upload] 配置关卡数：${innerConfig.game.length}`);

// ── 2. 找可用的调试 Chrome ──────────────────────────────────────────
async function findChromeTab(ports = [9222, 9223, 18800]) {
  for (const port of ports) {
    try {
      const tabs = await httpGet(`http://127.0.0.1:${port}/json`);
      const parsed = JSON.parse(tabs);
      const tab = parsed.find(t =>
        t.url && t.url.includes("coursewaremaker.speiyou.com") && t.type === "page"
      );
      if (tab) return { port, tabId: tab.id };
    } catch (_) { /* port not open */ }
  }
  return null;
}

function httpGet(url) {
  return new Promise((resolve, reject) => {
    http.get(url, res => {
      let data = "";
      res.on("data", d => data += d);
      res.on("end", () => resolve(data));
    }).on("error", reject);
  });
}

// ── 3. 通过 WebSocket 在 tab 里执行上传 ──────────────────────────────
function wsEval(port, tabId, expression) {
  return new Promise((resolve, reject) => {
    const ws = new WebSocket(`ws://127.0.0.1:${port}/devtools/page/${tabId}`);
    const timer = setTimeout(() => { ws.close(); reject(new Error("WebSocket timeout")); }, 30000);
    ws.on("open", () => {
      ws.send(JSON.stringify({
        id: 1, method: "Runtime.evaluate",
        params: { expression, returnByValue: true, awaitPromise: true }
      }));
    });
    ws.on("message", data => {
      const d = JSON.parse(data);
      if (d.id === 1) {
        clearTimeout(timer);
        ws.close();
        if (d.result?.exceptionDetails) {
          reject(new Error(d.result.exceptionDetails.text || "JS exception"));
        } else {
          resolve(d.result?.result?.value);
        }
      }
    });
    ws.on("error", e => { clearTimeout(timer); reject(e); });
  });
}

// ── 4. 主逻辑 ────────────────────────────────────────────────────────
async function main() {
  // 找 Chrome tab
  const found = await findChromeTab();
  if (!found) {
    console.error(`
[upload] ❌ 未找到调试 Chrome（端口 9222/9223）

请先启动调试 Chrome：
  google-chrome --remote-debugging-port=9222 &
然后在浏览器里打开 CoursewareMaker 并登录，再重新运行本脚本。
`);
    process.exit(1);
  }
  const { port, tabId } = found;
  console.log(`[upload] 找到 Chrome tab（port=${port}, tab=${tabId.slice(0,8)}...）`);

  // 构造上传代码
  const uploadCode = `
(async function() {
  const token = localStorage.getItem('GAMEMAKER_TOKEN') || '';
  if (!token) throw new Error('GAMEMAKER_TOKEN missing，请确保已登录 CoursewareMaker');
  
  const gameId = ${JSON.stringify(gameId)};
  const innerConfig = ${JSON.stringify(innerConfig)};

  // 取当前游戏详情（获取 game_name 等字段）
  const getRes = await fetch('https://sszt-gateway.speiyou.com/beibo/game/config/game?game_id=' + gameId, {
    headers: { beibotoken: token }
  });
  const detail = await getRes.json();
  if (!detail || detail.code !== 0) throw new Error('GET failed: ' + JSON.stringify(detail));

  // 合并并上传
  const payload = { ...detail.result, configuration: innerConfig };
  const putRes = await fetch('https://sszt-gateway.speiyou.com/beibo/game/config/game', {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json;charset=UTF-8', beibotoken: token },
    body: JSON.stringify(payload)
  });
  const putJson = await putRes.json();
  if (putJson.code !== 0) throw new Error('PUT failed: ' + JSON.stringify(putJson));

  // 验证
  const vRes = await fetch('https://sszt-gateway.speiyou.com/beibo/game/config/game?game_id=' + gameId, {
    headers: { beibotoken: token }
  });
  const v = await vRes.json();
  const raw = v?.result?.configuration || '';
  return JSON.stringify({
    game_name: v?.result?.game_name,
    save_time: v?.result?.save_time,
    raw_len: typeof raw === 'string' ? raw.length : JSON.stringify(raw).length,
    double_encoded: typeof raw === 'string' && raw.startsWith('"{')
  });
})()`;

  const result = await wsEval(port, tabId, uploadCode);
  const r = JSON.parse(result);

  if (r.double_encoded) {
    console.error("[upload] ⚠️  警告：配置被二次序列化（double encoded），前端可能崩溃！");
  } else {
    console.log(`[upload] ✅ 上传成功！
  游戏：${r.game_name}
  保存时间：${r.save_time}
  配置大小：${r.raw_len} bytes`);
  }
}

main().catch(e => {
  console.error("[upload] ❌ 错误：", e.message);
  process.exit(1);
});
