const puppeteer = require('puppeteer-core');
const fs = require('fs');
const path = require('path');

// 日志文件路径
const LOG_DIR = 'D:/codexProject/chrome_monitoring_logs';
const LOG_FILE = path.join(LOG_DIR, `game_creation_${Date.now()}.log`);
const NETWORK_LOG = path.join(LOG_DIR, `network_${Date.now()}.jsonl`);
const EVENTS_LOG = path.join(LOG_DIR, `events_${Date.now()}.jsonl`);

// 确保日志目录存在
if (!fs.existsSync(LOG_DIR)) {
    fs.mkdirSync(LOG_DIR, { recursive: true });
}

function log(message, data = null) {
    const timestamp = new Date().toISOString();
    const logEntry = `[${timestamp}] ${message}`;
    console.log(logEntry);
    fs.appendFileSync(LOG_FILE, logEntry + '\n');
    if (data) {
        fs.appendFileSync(LOG_FILE, JSON.stringify(data, null, 2) + '\n\n');
    }
}

function logEvent(eventType, data) {
    const entry = {
        timestamp: new Date().toISOString(),
        type: eventType,
        data: data
    };
    fs.appendFileSync(EVENTS_LOG, JSON.stringify(entry) + '\n');
}

function logNetwork(requestId, type, data) {
    const entry = {
        timestamp: new Date().toISOString(),
        requestId: requestId,
        type: type, // 'request', 'response', 'error'
        data: data
    };
    fs.appendFileSync(NETWORK_LOG, JSON.stringify(entry) + '\n');
}

async function main() {
    log('========== 开始监控 Chrome 浏览器 ==========');
    log(`日志目录: ${LOG_DIR}`);

    // 连接到已启动的 Chrome 实例
    const browser = await puppeteer.connect({
        browserURL: 'http://localhost:9222',
        defaultViewport: null
    });

    log('已连接到 Chrome (端口 9222)');

    // 获取所有页面
    const pages = await browser.pages();
    log(`当前打开的页面数: ${pages.length}`);

    // 监听新页面创建
    browser.on('targetcreated', async (target) => {
        log(`[事件] 新标签页创建: ${target.url()}`);
        logEvent('targetcreated', { url: target.url(), type: target.type() });

        if (target.type() === 'page') {
            const newPage = await target.page();
            setupPageMonitoring(newPage);
        }
    });

    // 监听页面关闭
    browser.on('targetdestroyed', (target) => {
        log(`[事件] 标签页关闭: ${target.url()}`);
        logEvent('targetdestroyed', { url: target.url() });
    });

    // 为现有页面设置监控
    for (const page of pages) {
        await setupPageMonitoring(page);
    }

    log('\n✅ 监控已启动！');
    log('现在可以在浏览器中操作新建游戏，所有活动将被记录。');
    log('按 Ctrl+C 停止监控。\n');

    // 保持脚本运行
    await new Promise(() => {});
}

async function setupPageMonitoring(page) {
    const pageUrl = page.url();
    log(`设置页面监控: ${pageUrl}`);

    // 启用各种 CDP 域
    const client = await page.target().createCDPSession();
    await client.send('Network.enable');
    await client.send('Log.enable');
    await client.send('Runtime.enable');
    await client.send('DOMStorage.enable');

    // 监听控制台日志
    page.on('console', msg => {
        const text = msg.text();
        log(`[Console ${msg.type()}] ${text}`);
        logEvent('console', { type: msg.type(), text: text, url: page.url() });
    });

    // 监听页面错误
    page.on('pageerror', error => {
        log(`[页面错误] ${error.message}`);
        logEvent('pageerror', { message: error.message, stack: error.stack });
    });

    // 监听请求失败
    page.on('requestfailed', request => {
        log(`[请求失败] ${request.method()} ${request.url()}`);
        logEvent('requestfailed', { method: request.method(), url: request.url() });
    });

    // 监听导航
    page.on('framenavigated', frame => {
        if (frame === page.mainFrame()) {
            log(`[导航] ${frame.url()}`);
            logEvent('navigation', { url: frame.url() });
        }
    });

    // 监听网络请求
    page.on('request', request => {
        const url = request.url();
        const method = request.method();

        // 只记录重要的请求（过滤静态资源）
        if (url.includes('api') || url.includes('courseware') || method !== 'GET') {
            log(`[请求] ${method} ${url}`);
            logNetwork(request._requestId, 'request', {
                url: url,
                method: method,
                headers: request.headers(),
                postData: request.postData()
            });
        }
    });

    // 监听网络响应
    page.on('response', async response => {
        const request = response.request();
        const url = request.url();
        const method = request.method();

        // 只记录重要的响应
        if (url.includes('api') || url.includes('courseware') || method !== 'GET') {
            try {
                const status = response.status();
                const headers = response.headers();
                let body = null;

                const contentType = headers['content-type'] || '';
                if (contentType.includes('application/json')) {
                    try {
                        body = await response.json();
                    } catch (e) {
                        body = await response.text();
                    }
                }

                log(`[响应] ${status} ${method} ${url}`);
                logNetwork(request._requestId, 'response', {
                    url: url,
                    status: status,
                    headers: headers,
                    body: body
                });
            } catch (error) {
                log(`[响应解析错误] ${url}: ${error.message}`);
            }
        }
    });

    // 监听 localStorage 变化
    client.on('DOMStorage.domStorageItemUpdated', (params) => {
        log(`[localStorage 更新] Key: ${params.key} = ${params.newValue?.substring(0, 100)}...`);
        logEvent('localStorage', {
            storageId: params.storageId,
            key: params.key,
            oldValue: params.oldValue,
            newValue: params.newValue
        });
    });

    // 监听 Runtime 日志
    client.on('Runtime.consoleAPICalled', (params) => {
        const args = params.args.map(arg => arg.value || arg.description || '').join(' ');
        log(`[Runtime Console] ${params.type}: ${args}`);
    });

    // 监听 Runtime 异常
    client.on('Runtime.exceptionThrown', (params) => {
        const exception = params.exceptionDetails;
        log(`[Runtime 异常] ${exception.text}`);
        logEvent('runtime_exception', exception);
    });

    // 定期捕获 localStorage 和 cookies
    setInterval(async () => {
        try {
            // 捕获 localStorage
            const localStorage = await page.evaluate(() => {
                return JSON.stringify(window.localStorage);
            });
            fs.writeFileSync(
                path.join(LOG_DIR, 'latest_localStorage.json'),
                localStorage
            );

            // 捕获 cookies
            const cookies = await page.cookies();
            fs.writeFileSync(
                path.join(LOG_DIR, 'latest_cookies.json'),
                JSON.stringify(cookies, null, 2)
            );
        } catch (error) {
            // 静默失败
        }
    }, 5000);
}

// 优雅退出
process.on('SIGINT', () => {
    log('\n========== 监控已停止 ==========');
    log(`完整日志: ${LOG_FILE}`);
    log(`网络日志: ${NETWORK_LOG}`);
    log(`事件日志: ${EVENTS_LOG}`);
    process.exit(0);
});

main().catch(error => {
    log('监控脚本错误:', error);
    process.exit(1);
});
