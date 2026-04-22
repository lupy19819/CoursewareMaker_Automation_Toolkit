/**
 * 监控 CoursewareMaker 新建运动PK游戏（赛跑/游泳/赛车）的完整流程
 * 记录所有网络请求、页面事件、存储变化
 */
const puppeteer = require('puppeteer-core');
const fs = require('fs');
const path = require('path');

const LOG_DIR = 'D:/codexProject/chrome_monitoring_logs';
const SESSION_ID = Date.now();
const LOG_FILE = path.join(LOG_DIR, `create_yundongpk_${SESSION_ID}.log`);
const NETWORK_FILE = path.join(LOG_DIR, `network_yundongpk_${SESSION_ID}.jsonl`);
const EVENTS_FILE = path.join(LOG_DIR, `events_yundongpk_${SESSION_ID}.jsonl`);

if (!fs.existsSync(LOG_DIR)) fs.mkdirSync(LOG_DIR, { recursive: true });

function ts() { return new Date().toLocaleString('zh-CN', { hour12: false }); }

function log(msg) {
  const line = `[${ts()}] ${msg}`;
  console.log(line);
  fs.appendFileSync(LOG_FILE, line + '\n');
}

function logNetwork(data) {
  fs.appendFileSync(NETWORK_FILE, JSON.stringify(data) + '\n');
}

function logEvent(data) {
  fs.appendFileSync(EVENTS_FILE, JSON.stringify(data) + '\n');
}

(async () => {
  log('=== CoursewareMaker 运动PK游戏创建流程监控 ===');
  log(`会话ID: ${SESSION_ID}`);
  log(`日志文件: ${LOG_FILE}`);
  log(`网络日志: ${NETWORK_FILE}`);
  log(`事件日志: ${EVENTS_FILE}`);

  const browser = await puppeteer.connect({
    browserURL: 'http://localhost:9222',
    defaultViewport: null
  });

  log('✅ 已连接到Edge浏览器');

  const pages = await browser.pages();
  log(`当前打开 ${pages.length} 个标签页`);

  // 监听所有现有和新建的标签页
  async function monitorPage(page, idx) {
    const url = page.url();
    log(`📄 监听标签页 #${idx}: ${url}`);

    // 启用CDP会话
    const client = await page.target().createCDPSession();

    // 监听网络请求
    await client.send('Network.enable');

    const pendingRequests = new Map();

    client.on('Network.requestWillBeSent', (params) => {
      const { requestId, request, timestamp, type } = params;
      const { url, method, postData, headers } = request;

      // 只记录API相关请求
      if (url.includes('/beibo/') || url.includes('/api/') ||
          url.includes('game') || url.includes('config') ||
          url.includes('template') || url.includes('create') ||
          url.includes('save') || url.includes('lock') ||
          url.includes('unlock') || url.includes('resource') ||
          url.includes('sszt-gateway') || url.includes('coursewaremaker')) {

        const entry = {
          type: 'request',
          timestamp: ts(),
          requestId,
          method,
          url,
          postData: postData || null,
          headers: Object.fromEntries(
            Object.entries(headers).filter(([k]) =>
              ['content-type', 'beibotoken', 'authorization', 'cookie'].includes(k.toLowerCase())
            )
          ),
          resourceType: type
        };

        pendingRequests.set(requestId, entry);
        logNetwork(entry);

        // 人类可读日志
        let shortUrl = url.replace(/https?:\/\/[^/]+/, '');
        log(`🌐 请求 ${method} ${shortUrl}`);
        if (postData) {
          try {
            const parsed = JSON.parse(postData);
            log(`   📤 参数: ${JSON.stringify(parsed).substring(0, 500)}`);
          } catch {
            log(`   📤 数据: ${postData.substring(0, 300)}`);
          }
        }
      }
    });

    client.on('Network.responseReceived', (params) => {
      const { requestId, response } = params;
      if (pendingRequests.has(requestId)) {
        const reqEntry = pendingRequests.get(requestId);
        logNetwork({
          type: 'response_header',
          timestamp: ts(),
          requestId,
          url: reqEntry.url,
          status: response.status,
          statusText: response.statusText,
          contentType: response.headers['content-type'] || response.headers['Content-Type']
        });
        log(`   📥 响应 ${response.status} ${response.statusText}`);
      }
    });

    client.on('Network.loadingFinished', async (params) => {
      const { requestId } = params;
      if (pendingRequests.has(requestId)) {
        try {
          const resp = await client.send('Network.getResponseBody', { requestId });
          let body = resp.body;
          if (body && body.length > 5000) {
            body = body.substring(0, 5000) + `... [truncated, total ${resp.body.length} chars]`;
          }

          const entry = {
            type: 'response_body',
            timestamp: ts(),
            requestId,
            url: pendingRequests.get(requestId).url,
            body
          };
          logNetwork(entry);

          // 尝试解析JSON
          try {
            const parsed = JSON.parse(resp.body);
            if (parsed.data && (parsed.data.game_id || parsed.data.id || parsed.data.config)) {
              log(`   📦 关键数据: ${JSON.stringify(parsed.data).substring(0, 500)}`);
            } else if (parsed.code !== undefined) {
              log(`   📦 结果: code=${parsed.code}, msg=${parsed.msg || ''}`);
            }
          } catch {}
        } catch (e) {
          // Response body not available
        }
        pendingRequests.delete(requestId);
      }
    });

    // 监听页面导航
    page.on('framenavigated', (frame) => {
      if (frame === page.mainFrame()) {
        const newUrl = frame.url();
        log(`🔀 页面导航: ${newUrl}`);
        logEvent({ type: 'navigation', timestamp: ts(), url: newUrl });
      }
    });

    // 监听控制台消息
    page.on('console', (msg) => {
      const text = msg.text();
      if (text.includes('game') || text.includes('config') || text.includes('save') ||
          text.includes('create') || text.includes('template') || text.includes('error') ||
          text.includes('Error') || text.includes('运动') || text.includes('赛跑') ||
          text.includes('游泳') || text.includes('赛车') || text.includes('PK')) {
        log(`💬 控制台 [${msg.type()}]: ${text.substring(0, 300)}`);
        logEvent({ type: 'console', timestamp: ts(), level: msg.type(), text: text.substring(0, 1000) });
      }
    });

    // 监听弹窗
    page.on('dialog', async (dialog) => {
      log(`⚠️ 弹窗 [${dialog.type()}]: ${dialog.message()}`);
      logEvent({ type: 'dialog', timestamp: ts(), dialogType: dialog.type(), message: dialog.message() });
    });
  }

  // 监听所有现有标签页
  for (let i = 0; i < pages.length; i++) {
    await monitorPage(pages[i], i);
  }

  // 监听新标签页
  browser.on('targetcreated', async (target) => {
    if (target.type() === 'page') {
      const newPage = await target.page();
      const idx = (await browser.pages()).length - 1;
      log(`📄 新标签页打开: ${newPage.url()}`);
      await monitorPage(newPage, idx);
    }
  });

  // 定期快照localStorage
  setInterval(async () => {
    try {
      const pages = await browser.pages();
      for (const page of pages) {
        if (page.url().includes('coursewaremaker')) {
          const storage = await page.evaluate(() => {
            const items = {};
            for (let i = 0; i < localStorage.length; i++) {
              const key = localStorage.key(i);
              items[key] = localStorage.getItem(key);
            }
            return items;
          });
          fs.writeFileSync(
            path.join(LOG_DIR, 'latest_localStorage_yundongpk.json'),
            JSON.stringify(storage, null, 2)
          );
        }
      }
    } catch {}
  }, 10000);

  log('');
  log('🎯 监听已就绪！请在浏览器中执行以下操作：');
  log('   1. 打开CoursewareMaker');
  log('   2. 点击创建新游戏');
  log('   3. 选择运动PK类型（赛跑/游泳/赛车）');
  log('   4. 完成游戏创建并保存');
  log('');
  log('所有操作将被自动记录...');
  log('');

  // 保持进程运行
  process.on('SIGINT', () => {
    log('🛑 监听结束（手动停止）');
    process.exit(0);
  });

  // 心跳日志
  setInterval(() => {
    log(`💓 监听中... (已运行 ${Math.floor((Date.now() - SESSION_ID) / 60000)} 分钟)`);
  }, 120000);
})();
