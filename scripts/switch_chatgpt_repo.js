#!/usr/bin/env node
import { readFile } from "node:fs/promises";
import { spawn, execSync } from "node:child_process";
import { existsSync } from "node:fs";
import { setTimeout as delay } from "node:timers/promises";

const CHROME_PATH = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
const USER_DATA_DIR = `${process.env.HOME}/Library/Application Support/Google/Chrome`;
const PROFILE_DIR = "Default";
const DOM_SCRIPT_PATH = "/Users/ted/komission/scripts/switch_chatgpt_repo_dom.js";
const TARGET_URL = "https://chatgpt.com/";

class PipeTransport {
  constructor(proc) {
    this.proc = proc;
    this.buffer = Buffer.alloc(0);
    this.listeners = new Set();

    proc.stdout.on("data", (chunk) => this._onData(chunk));
  }

  _onData(chunk) {
    this.buffer = Buffer.concat([this.buffer, chunk]);
    while (this.buffer.length >= 4) {
      const msgLen = this.buffer.readUInt32LE(0);
      if (this.buffer.length < 4 + msgLen) return;
      const payload = this.buffer.slice(4, 4 + msgLen).toString("utf8");
      this.buffer = this.buffer.slice(4 + msgLen);
      try {
        const msg = JSON.parse(payload);
        for (const listener of this.listeners) listener(msg);
      } catch {
        // Ignore malformed messages.
      }
    }
  }

  send(message) {
    const data = Buffer.from(JSON.stringify(message), "utf8");
    const buf = Buffer.alloc(4 + data.length);
    buf.writeUInt32LE(data.length, 0);
    data.copy(buf, 4);
    this.proc.stdin.write(buf);
  }

  onMessage(listener) {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }
}

function createCdpClient(transport) {
  let nextId = 1;
  const pending = new Map();

  transport.onMessage((msg) => {
    if (msg.id && pending.has(msg.id)) {
      const { resolve, reject } = pending.get(msg.id);
      pending.delete(msg.id);
      if (msg.error) reject(new Error(msg.error.message || "CDP error"));
      else resolve(msg.result);
    }
  });

  const send = (method, params = {}, sessionId) => {
    const id = nextId++;
    const payload = { id, method, params };
    if (sessionId) payload.sessionId = sessionId;
    transport.send(payload);
    return new Promise((resolve, reject) => {
      pending.set(id, { resolve, reject });
    });
  };

  return { send };
}

async function waitForReadyState(send, sessionId) {
  for (let i = 0; i < 40; i += 1) {
    const res = await send(
      "Runtime.evaluate",
      { expression: "document.readyState", returnByValue: true },
      sessionId
    );
    const state = res?.result?.value;
    if (state === "complete" || state === "interactive") return;
    await delay(500);
  }
}

async function ensureChromePipe() {
  if (!existsSync(CHROME_PATH)) {
    throw new Error(`Chrome not found at ${CHROME_PATH}`);
  }

  try {
    execSync("osascript -e 'tell application \"Google Chrome\" to quit'", {
      stdio: "ignore",
    });
  } catch {
    // Ignore if Chrome is not running.
  }

  const args = [
    "--remote-debugging-pipe",
    `--user-data-dir=${USER_DATA_DIR}`,
    `--profile-directory=${PROFILE_DIR}`,
  ];

  const proc = spawn(CHROME_PATH, args, {
    stdio: ["pipe", "pipe", "ignore"],
  });

  return proc;
}

async function run() {
  const proc = await ensureChromePipe();
  const transport = new PipeTransport(proc);
  const { send } = createCdpClient(transport);

  // Wait for CDP to be ready.
  for (let i = 0; i < 20; i += 1) {
    try {
      await send("Browser.getVersion");
      break;
    } catch {
      await delay(500);
    }
  }

  const targetsRes = await send("Target.getTargets");
  const targets = targetsRes.targetInfos || [];
  let target = targets.find(
    (t) =>
      t.type === "page" &&
      (t.url?.includes("chatgpt.com") || t.url?.includes("chat.openai.com"))
  );

  if (!target) {
    const created = await send("Target.createTarget", { url: TARGET_URL });
    target = { targetId: created.targetId, url: TARGET_URL };
  }

  const attachRes = await send("Target.attachToTarget", {
    targetId: target.targetId,
    flatten: true,
  });
  const sessionId = attachRes.sessionId;

  await send("Runtime.enable", {}, sessionId);
  await send("Page.enable", {}, sessionId);

  if (!target.url || (!target.url.includes("chatgpt.com") && !target.url.includes("chat.openai.com"))) {
    await send("Page.navigate", { url: TARGET_URL }, sessionId);
  }

  await waitForReadyState(send, sessionId);

  const domScript = await readFile(DOM_SCRIPT_PATH, "utf8");
  const evalRes = await send(
    "Runtime.evaluate",
    { expression: domScript, returnByValue: true, awaitPromise: true },
    sessionId
  );

  const result = evalRes?.result?.value || "unknown";
  console.log(`automation_result=${result}`);
}

run().catch((err) => {
  console.error(`automation_error=${err.message}`);
  process.exit(1);
});
