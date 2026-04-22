#!/usr/bin/env node
import crypto from "node:crypto";
import fs from "node:fs/promises";
import path from "node:path";

const BUCKET = "courseware-maker-1252161091";
const REGION = "ap-beijing";
const COS_HOST = `${BUCKET}.cos.${REGION}.myqcloud.com`;
const COS_AK_URL =
  "https://sci-gateway-pre.speiyou.com/config/argument/storage/ops/cos/v1/ak?channel=courseware-maker-1252161091";
const RESOURCE_URL = "https://sszt-gateway.speiyou.com/beibo/game/config/resource";

const TYPE_BY_CATEGORY = {
  image: 1,
  audio: 2,
  video: 3,
  spine: 4,
};

function parseArgs(argv) {
  const args = {
    port: 9222,
    category: "image",
    ext: ".png",
    topicId: 1,
    tagId: 7,
    concurrency: 5,
  };
  for (let i = 0; i < argv.length; i++) {
    const arg = argv[i];
    if (!arg.startsWith("--")) {
      args.folder = arg;
      continue;
    }
    const key = arg.slice(2);
    const value = argv[++i];
    if (value == null) throw new Error(`Missing value for --${key}`);
    if (["port", "topic-id", "tag-id", "concurrency"].includes(key)) {
      args[key.replace(/-([a-z])/g, (_, c) => c.toUpperCase())] = Number(value);
    } else {
      args[key.replace(/-([a-z])/g, (_, c) => c.toUpperCase())] = value;
    }
  }
  if (!args.folder) {
    throw new Error(
      [
        "Usage:",
        "  node scripts/courseware_bulk_upload_assets.mjs <folder> [--ext .png] [--topic-id 1] [--tag-id 7]",
        "",
        "Defaults: --category image --ext .png --topic-id 1(通用) --tag-id 7(贴画)",
        "Requires a logged-in controllable Chrome at http://127.0.0.1:9222",
      ].join("\n"),
    );
  }
  if (!TYPE_BY_CATEGORY[args.category]) throw new Error(`Unsupported category: ${args.category}`);
  args.ext = args.ext.startsWith(".") ? args.ext.toLowerCase() : `.${args.ext.toLowerCase()}`;
  return args;
}

async function cdpEvaluate(port, expression) {
  const tabs = await fetch(`http://127.0.0.1:${port}/json/list`).then((r) => r.json());
  const tab = tabs.find((t) => t.url?.startsWith("https://coursewaremaker.speiyou.com/"));
  if (!tab) throw new Error(`No coursewaremaker tab found on port ${port}`);

  const ws = new WebSocket(tab.webSocketDebuggerUrl);
  let nextId = 0;
  const pending = new Map();
  ws.onmessage = (ev) => {
    const msg = JSON.parse(ev.data);
    if (!msg.id || !pending.has(msg.id)) return;
    const { resolve, reject } = pending.get(msg.id);
    pending.delete(msg.id);
    msg.error ? reject(new Error(JSON.stringify(msg.error))) : resolve(msg.result);
  };
  await new Promise((resolve, reject) => {
    ws.onopen = resolve;
    ws.onerror = reject;
  });
  const send = (method, params = {}) =>
    new Promise((resolve, reject) => {
      const id = ++nextId;
      pending.set(id, { resolve, reject });
      ws.send(JSON.stringify({ id, method, params }));
    });
  try {
    await send("Runtime.enable");
    const result = await send("Runtime.evaluate", {
      expression,
      awaitPromise: true,
      returnByValue: true,
    });
    return result.result.value;
  } finally {
    ws.close();
  }
}

async function getBrowserAuth(port) {
  const state = await cdpEvaluate(
    port,
    `JSON.stringify({
      token: localStorage.getItem("GAMEMAKER_TOKEN"),
      user: JSON.parse(localStorage.getItem("GAMEMAKER_USER_INFO") || "{}")
    })`,
  );
  const parsed = JSON.parse(state || "{}");
  if (!parsed.token) throw new Error("Could not read GAMEMAKER_TOKEN from the controlled browser");
  if (!parsed.user?.empNo) throw new Error("Could not read user empNo from the controlled browser");
  return parsed;
}

async function listFiles(folder, ext) {
  const entries = await fs.readdir(folder, { withFileTypes: true });
  return entries
    .filter((entry) => entry.isFile() && path.extname(entry.name).toLowerCase() === ext)
    .map((entry) => path.join(folder, entry.name))
    .sort((a, b) => a.localeCompare(b, "zh-Hans-CN"));
}

async function getCosCredential(token) {
  const res = await fetch(COS_AK_URL, {
    headers: {
      beibotoken: token,
      referer: "https://coursewaremaker.speiyou.com/",
      origin: "https://coursewaremaker.speiyou.com",
    },
  });
  const json = await res.json();
  if (!res.ok || json.code !== 0) {
    throw new Error(`Failed to get COS credential: HTTP ${res.status} ${JSON.stringify(json)}`);
  }
  return json.result;
}

function hmacSha1(key, value) {
  return crypto.createHmac("sha1", key).update(value).digest("hex");
}

function sha1(value) {
  return crypto.createHash("sha1").update(value).digest("hex");
}

function signCosPut({ key, length, credential }) {
  const now = Math.floor(Date.now() / 1000);
  const end = Math.floor(new Date(credential.expiration).getTime() / 1000);
  const keyTime = `${now};${end}`;
  const headers = {
    "content-length": String(length),
    host: COS_HOST,
    "x-cos-storage-class": "STANDARD",
  };
  const headerList = Object.keys(headers).sort().join(";");
  const httpHeaders = Object.keys(headers)
    .sort()
    .map((name) => `${encodeURIComponent(name)}=${encodeURIComponent(headers[name])}`)
    .join("&");
  const httpString = ["put", `/${key}`, "", httpHeaders, ""].join("\n");
  const stringToSign = ["sha1", keyTime, sha1(httpString), ""].join("\n");
  const signKey = hmacSha1(credential.accessKeySecret, keyTime);
  const signature = hmacSha1(signKey, stringToSign);
  return [
    "q-sign-algorithm=sha1",
    `q-ak=${credential.accessKeyId}`,
    `q-sign-time=${keyTime}`,
    `q-key-time=${keyTime}`,
    `q-header-list=${headerList}`,
    "q-url-param-list=",
    `q-signature=${signature}`,
  ].join("&");
}

async function putCosObject({ file, key, credential }) {
  const body = await fs.readFile(file);
  const authorization = signCosPut({ key, length: body.length, credential });
  const res = await fetch(`https://${COS_HOST}/${key}`, {
    method: "PUT",
    body,
    headers: {
      authorization,
      "content-type": "image/png",
      "content-length": String(body.length),
      "x-cos-storage-class": "STANDARD",
      "x-cos-security-token": credential.securityToken,
      referer: "https://coursewaremaker.speiyou.com/",
      origin: "https://coursewaremaker.speiyou.com",
    },
  });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`COS PUT failed for ${path.basename(file)}: HTTP ${res.status} ${text}`);
  }
  return `https://${COS_HOST}/${key}`;
}

async function createResources({ token, items }) {
  const res = await fetch(RESOURCE_URL, {
    method: "POST",
    body: JSON.stringify(items),
    headers: {
      beibotoken: token,
      "content-type": "application/json;charset=UTF-8",
      referer: "https://coursewaremaker.speiyou.com/",
      origin: "https://coursewaremaker.speiyou.com",
    },
  });
  const json = await res.json().catch(async () => ({ raw: await res.text() }));
  if (!res.ok || json.code !== 0) {
    throw new Error(`Resource create failed: HTTP ${res.status} ${JSON.stringify(json)}`);
  }
  return json;
}

async function mapLimit(items, limit, worker) {
  const results = new Array(items.length);
  let index = 0;
  await Promise.all(
    Array.from({ length: Math.min(limit, items.length) }, async () => {
      while (index < items.length) {
        const current = index++;
        results[current] = await worker(items[current], current);
      }
    }),
  );
  return results;
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const files = await listFiles(args.folder, args.ext);
  if (!files.length) throw new Error(`No ${args.ext} files found in ${args.folder}`);

  const { token, user } = await getBrowserAuth(args.port);
  const credential = await getCosCredential(token);
  const date = new Date().toISOString().slice(0, 10);
  console.log(`Uploading ${files.length} file(s) as ${user.name || user.empNo} (${user.empNo})`);

  const uploaded = await mapLimit(files, args.concurrency, async (file, i) => {
    const ext = path.extname(file).toLowerCase();
    const key = `assets/${args.category}/${user.empNo}/${date}/${crypto.randomBytes(16).toString("hex")}${ext}`;
    const url = await putCosObject({ file, key, credential });
    console.log(`[${i + 1}/${files.length}] ${path.basename(file)} -> ${url}`);
    return {
      name: path.basename(file, ext),
      url,
      tag: [args.tagId],
      type: TYPE_BY_CATEGORY[args.category],
      topic: [args.topicId],
      desc: "",
      category: args.category,
      subject: [],
    };
  });

  await createResources({ token, items: uploaded });
  console.log(`Done. Registered ${uploaded.length} resource(s).`);
}

main().catch((error) => {
  console.error(error.message);
  process.exitCode = 1;
});
