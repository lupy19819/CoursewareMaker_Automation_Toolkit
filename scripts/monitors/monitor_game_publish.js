/**
 * 监控 CoursewareMaker 发布游戏流程
 * 专注记录发布相关的API调用和操作
 */

const puppeteer = require('puppeteer-core');
const fs = require('fs');
const path = require('path');

const LOG_DIR = path.join(__dirname, 'chrome_monitoring_logs');
const timestamp = Date.now();
const mainLogFile = path.join(LOG_DIR, `game_publish_${timestamp}.log`);
const networkLogFile = path.join(LOG_DIR, `network_publish_${timestamp}.jsonl`);
const eventsLogFile = path.join(LOG_DIR, `events_publish_${timestamp}.jsonl`);

// 确保日志目录存在
if (!fs.existsSync(LOG_DIR)) {
  fs.mkdirSync(LOG_DIR, { recursive: true });
}

function log(message) {
  const timestamp = new Date().toISOString();
  const logLine = `[${timestamp}] ${message}\n`;
  console.log(logLine.trim());
  fs.appendFileSync(mainLogFile, logLine);
}

function logJSON(file, data) {
  fs.appendFileSync(file, JSON.stringify(data) + '\n');
}

(async () => {
  try {
    log('🔍 开始监控游戏发布流程...');

    const browser = await puppeteer.connect({
      browserURL: 'http://localhost:9222',
      defaultViewport: null
    });

    const pages = await browser.pages();
    const page = pages[0];

    log(`✅ 已连接到浏览器，当前URL: ${page.url()}`);

    // 监听网络请求
    await page.setRequestInterception(true);

    page.on('request', request => {
      const url = request.url();
      const method = request.method();

      // 重点关注发布相关的API
      if (url.includes('/beibo/game/') ||
          url.includes('/publish') ||
          url.includes('/release') ||
          url.includes('/deploy') ||
          url.includes('/status') ||
          url.includes('/save') ||
          url.includes('/update')) {

        const requestData = {
          type: 'request',
          timestamp: new Date().toISOString(),
          method: method,
          url: url,
          headers: request.headers(),
          postData: request.postData() || null
        };

        logJSON(networkLogFile, requestData);
        log(`[请求] ${method} ${url}`);

        // 如果有POST数据，记录下来
        if (request.postData()) {
          try {
            const parsed = JSON.parse(request.postData());
            log(`[请求体] ${JSON.stringify(parsed, null, 2)}`);
          } catch (e) {
            log(`[请求体] ${request.postData().substring(0, 200)}...`);
          }
        }
      }

      request.continue();
    });

    page.on('response', async response => {
      const url = response.url();
      const status = response.status();

      // 重点关注发布相关的API响应
      if (url.includes('/beibo/game/') ||
          url.includes('/publish') ||
          url.includes('/release') ||
          url.includes('/deploy') ||
          url.includes('/status') ||
          url.includes('/save') ||
          url.includes('/update')) {

        try {
          const responseBody = await response.text();

          const responseData = {
            type: 'response',
            timestamp: new Date().toISOString(),
            status: status,
            url: url,
            headers: response.headers(),
            body: responseBody
          };

          logJSON(networkLogFile, responseData);
          log(`[响应] ${status} ${url}`);

          // 尝试解析响应体
          try {
            const parsed = JSON.parse(responseBody);
            log(`[响应体] ${JSON.stringify(parsed, null, 2)}`);

            // 特别标注重要信息
            if (parsed.game_id) {
              log(`⭐ 发现 game_id: ${parsed.game_id}`);
            }
            if (parsed.publish_id || parsed.release_id) {
              log(`⭐ 发现发布ID: ${parsed.publish_id || parsed.release_id}`);
            }
            if (parsed.status) {
              log(`⭐ 状态: ${parsed.status}`);
            }
          } catch (e) {
            log(`[响应体] ${responseBody.substring(0, 300)}...`);
          }
        } catch (err) {
          log(`[响应错误] ${err.message}`);
        }
      }
    });

    // 监听页面导航
    page.on('framenavigated', frame => {
      if (frame === page.mainFrame()) {
        const navData = {
          type: 'navigation',
          timestamp: new Date().toISOString(),
          url: frame.url()
        };
        logJSON(eventsLogFile, navData);
        log(`[导航] ${frame.url()}`);
      }
    });

    // 监听控制台输出
    page.on('console', msg => {
      const text = msg.text();
      if (text.includes('publish') ||
          text.includes('发布') ||
          text.includes('release') ||
          text.includes('deploy')) {
        log(`[Console ${msg.type()}] ${text}`);
      }
    });

    // 定期保存localStorage和cookies
    setInterval(async () => {
      try {
        const localStorage = await page.evaluate(() => {
          return JSON.stringify(window.localStorage);
        });
        fs.writeFileSync(
          path.join(LOG_DIR, 'latest_localStorage_publish.json'),
          localStorage
        );

        const cookies = await page.cookies();
        fs.writeFileSync(
          path.join(LOG_DIR, 'latest_cookies_publish.json'),
          JSON.stringify(cookies, null, 2)
        );
      } catch (err) {
        // 忽略错误
      }
    }, 5000);

    log('✅ 监控启动成功！正在监听发布游戏的所有操作...');
    log('📁 日志文件:');
    log(`  - 主日志: ${mainLogFile}`);
    log(`  - 网络日志: ${networkLogFile}`);
    log(`  - 事件日志: ${eventsLogFile}`);
    log('');
    log('🎮 请在浏览器中执行发布游戏的操作...');

    // 保持监听
    await new Promise(() => {});

  } catch (error) {
    console.error('监控错误:', error);
    process.exit(1);
  }
})();
