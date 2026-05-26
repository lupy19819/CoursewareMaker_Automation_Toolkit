#!/usr/bin/env node
/**
 * CoursewareMaker browser preflight.
 *
 * Checks that a controllable CDP browser is open and logged in to
 * coursewaremaker.speiyou.com. When login is missing, it opens the login page
 * and captures a screenshot so the caller can show the QR code to the user.
 */

const fs = require("fs");
const path = require("path");
const { chromium } = require("playwright");

const LOGIN_URL = "https://coursewaremaker.speiyou.com/#/login";
const HOME_URL = "https://coursewaremaker.speiyou.com/#/list/game";

function parseArgs(argv) {
  const args = {
    port: process.env.CHROME_PORT || "9222",
    outputDir: path.join("output", "courseware_preflight"),
    openLogin: true,
  };
  for (let i = 2; i < argv.length; i += 1) {
    const arg = argv[i];
    if (arg === "--port") args.port = argv[++i];
    else if (arg === "--output-dir") args.outputDir = argv[++i];
    else if (arg === "--no-open-login") args.openLogin = false;
    else if (arg === "--help") {
      console.log("Usage: node scripts/check_coursewaremaker_browser.js [--port 9222] [--output-dir output/courseware_preflight] [--no-open-login]");
      process.exit(0);
    }
  }
  return args;
}

function report(status, extra = {}) {
  return {
    schema: "coursewaremaker.browser_preflight.v1",
    status,
    chrome_port: String(extra.chrome_port || ""),
    courseware_url: extra.courseware_url || "",
    login_url: LOGIN_URL,
    login_screenshot: extra.login_screenshot || "",
    message: extra.message || "",
  };
}

async function findCoursewarePage(context) {
  const pages = context.pages();
  return pages.find((page) => (page.url() || "").includes("coursewaremaker.speiyou.com"));
}

async function readLoginState(page) {
  return page.evaluate(() => {
    const token = localStorage.getItem("GAMEMAKER_TOKEN") || "";
    const userInfoRaw = localStorage.getItem("GAMEMAKER_USER_INFO") || "";
    let userInfo = null;
    try {
      userInfo = userInfoRaw ? JSON.parse(userInfoRaw) : null;
    } catch {
      userInfo = null;
    }
    return {
      logged_in: Boolean(token),
      token_length: token.length,
      user_name: userInfo?.name || userInfo?.userName || userInfo?.realName || "",
      emp_no: userInfo?.empNo || userInfo?.emp_no || "",
      href: location.href,
      title: document.title,
    };
  });
}

async function captureLoginPage(context, outputDir, openLogin) {
  let page = await findCoursewarePage(context);
  if (!page) {
    page = await context.newPage();
  }
  if (openLogin) {
    await page.goto(LOGIN_URL, { waitUntil: "domcontentloaded", timeout: 30000 });
  }
  await page.waitForTimeout(2500);

  fs.mkdirSync(outputDir, { recursive: true });
  const screenshotPath = path.resolve(outputDir, `coursewaremaker-login-${Date.now()}.png`);
  await page.screenshot({ path: screenshotPath, fullPage: true });
  return { page, screenshotPath };
}

async function main() {
  const args = parseArgs(process.argv);
  let browser;
  try {
    browser = await chromium.connectOverCDP(`http://127.0.0.1:${args.port}`);
  } catch (error) {
    console.log(JSON.stringify(report("no_listening_browser", {
      chrome_port: args.port,
      message: `未检测到可监听浏览器。请用 --remote-debugging-port=${args.port} 启动 Chrome，并打开 CoursewareMaker。`,
    }), null, 2));
    process.exit(2);
  }

  try {
    const context = browser.contexts()[0] || await browser.newContext();
    let page = await findCoursewarePage(context);
    if (!page) {
      const login = await captureLoginPage(context, args.outputDir, args.openLogin);
      page = login.page;
      console.log(JSON.stringify(report("not_logged_in", {
        chrome_port: args.port,
        courseware_url: page.url(),
        login_screenshot: login.screenshotPath,
        message: "未找到 CoursewareMaker 页面，已打开登录页。请扫码登录后重试。",
      }), null, 2));
      process.exit(2);
    }

    let loginState;
    try {
      loginState = await readLoginState(page);
    } catch {
      await page.goto(HOME_URL, { waitUntil: "domcontentloaded", timeout: 30000 });
      await page.waitForTimeout(1500);
      loginState = await readLoginState(page);
    }

    if (loginState.logged_in) {
      console.log(JSON.stringify({
        ...report("ok", {
          chrome_port: args.port,
          courseware_url: loginState.href,
          message: "CoursewareMaker 浏览器登录态可用。",
        }),
        user_name: loginState.user_name,
        emp_no: loginState.emp_no,
        token_length: loginState.token_length,
      }, null, 2));
      return;
    }

    const login = await captureLoginPage(context, args.outputDir, args.openLogin);
    console.log(JSON.stringify(report("not_logged_in", {
      chrome_port: args.port,
      courseware_url: login.page.url(),
      login_screenshot: login.screenshotPath,
      message: "CoursewareMaker 尚未登录，已打开登录页。请扫码登录后重试。",
    }), null, 2));
    process.exit(2);
  } finally {
    // Leave the user's CDP browser open; the Node process ending releases our connection.
  }
}

main().catch((error) => {
  console.log(JSON.stringify(report("error", {
    chrome_port: process.env.CHROME_PORT || "9222",
    message: error.message,
  }), null, 2));
  process.exit(2);
});
