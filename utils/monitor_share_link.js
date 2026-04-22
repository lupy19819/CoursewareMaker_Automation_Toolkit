/**
 * 监控 CoursewareMaker 生成分享链接流程
 * 记录所有相关的API调用、页面操作
 */

const puppeteer = require('puppeteer-core');
const fs = require('fs');
const path = require('path');

const CHROME_DEBUG_PORT = 9222;
const LOG_DIR = 'D:/codexProject/chrome_monitoring_logs';
const timestamp = Date.now();

// 确保日志目录存在
if (!fs.existsSync(LOG_DIR)) {
  fs.mkdirSync(LOG_DIR, { recursive: true });
}

const logFile = path.join(LOG_DIR, `share_link_${timestamp}.log`);
const networkLogFile = path.join(LOG_DIR, `network_share_${timestamp}.jsonl`);
const eventsLogFile = path.join(LOG_DIR, `events_share_${timestamp}.jsonl`);

function log(message) {
  const msg = `[${new Date().toISOString()}] ${message}\n`;
  fs.appendFileSync(logFile, msg);
  console.log(message);
}

function logNetwork(data) {
  fs.appendFileSync(networkLogFile, JSON.stringify(data) + '\n');
}

function logEvent(data) {
  fs.appendFileSync(eventsLogFile, JSON.stringify(data) + '\n');
}

async function main() {
  log('🚀 开始监听 CoursewareMaker 生成分享链接流程...');

  try {
    // 连接到已运行的Chrome
    const browser = await puppeteer.connect({
      browserURL: `http://localhost:${CHROME_DEBUG_PORT}`,
      defaultViewport: null
    });

    log('✅ 已连接到Chrome浏览器');

    const pages = await browser.pages();
    const page = pages[0];

    const currentUrl = page.url();
    log(`📄 当前页面: ${currentUrl}`);

    // 监听所有网络请求
    await page.setRequestInterception(true);

    page.on('request', request => {
      const url = request.url();
      const method = request.method();

      // 只记录关键API请求
      if (url.includes('beibo/game') ||
          url.includes('share') ||
          url.includes('link') ||
          url.includes('publish') ||
          url.includes('qrcode')) {

        log(`[请求] ${method} ${url}`);

        const postData = request.postData();
        if (postData) {
          try {
            const parsed = JSON.parse(postData);
            log(`[请求体] ${JSON.stringify(parsed, null, 2)}`);
            logNetwork({
              timestamp: Date.now(),
              type: 'request',
              method,
              url,
              body: parsed
            });
          } catch (e) {
            log(`[请求体] ${postData}`);
            logNetwork({
              timestamp: Date.now(),
              type: 'request',
              method,
              url,
              body: postData
            });
          }
        } else {
          logNetwork({
            timestamp: Date.now(),
            type: 'request',
            method,
            url
          });
        }
      }

      request.continue();
    });

    page.on('response', async response => {
      const url = response.url();
      const status = response.status();

      // 只记录关键API响应
      if (url.includes('beibo/game') ||
          url.includes('share') ||
          url.includes('link') ||
          url.includes('publish') ||
          url.includes('qrcode')) {

        log(`[响应] ${status} ${url}`);

        try {
          const responseBody = await response.text();
          try {
            const parsed = JSON.parse(responseBody);
            log(`[响应体] ${JSON.stringify(parsed, null, 2)}`);
            logNetwork({
              timestamp: Date.now(),
              type: 'response',
              status,
              url,
              body: parsed
            });
          } catch (e) {
            log(`[响应体] ${responseBody.substring(0, 500)}`);
            logNetwork({
              timestamp: Date.now(),
              type: 'response',
              status,
              url,
              body: responseBody.substring(0, 500)
            });
          }
        } catch (e) {
          log(`[响应错误] ${e.message}`);
        }
      }
    });

    // 监听页面导航
    page.on('framenavigated', frame => {
      if (frame === page.mainFrame()) {
        const url = frame.url();
        log(`[导航] ${url}`);
        logEvent({
          timestamp: Date.now(),
          type: 'navigation',
          url
        });
      }
    });

    // 监听控制台日志
    page.on('console', msg => {
      const text = msg.text();
      if (text.includes('share') ||
          text.includes('link') ||
          text.includes('分享') ||
          text.includes('链接')) {
        log(`[控制台] ${text}`);
        logEvent({
          timestamp: Date.now(),
          type: 'console',
          text
        });
      }
    });

    // 监听localStorage变化
    page.on('domcontentloaded', async () => {
      const storage = await page.evaluate(() => {
        return JSON.stringify(localStorage);
      });

      const storageFile = path.join(LOG_DIR, 'latest_localStorage_share.json');
      fs.writeFileSync(storageFile, storage);
    });

    log('✅ 监听已启动，等待用户操作...');
    log('📝 日志文件:');
    log(`   - 主日志: ${logFile}`);
    log(`   - 网络日志: ${networkLogFile}`);
    log(`   - 事件日志: ${eventsLogFile}`);
    log('');
    log('🎯 现在可以在浏览器中进行"生成分享链接"操作');
    log('');

    // 保持连接
    await new Promise(() => {});

  } catch (error) {
    log(`❌ 错误: ${error.message}`);
    console.error(error);
    process.exit(1);
  }
}

main();
