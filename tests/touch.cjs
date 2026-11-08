"use strict";
const assert = require("node:assert/strict");
const { once } = require("node:events");
const { spawn } = require("node:child_process");
const { mkdtemp } = require("node:fs/promises");
const os = require("node:os");
const path = require("node:path");
const { pathToFileURL } = require("node:url");
const { chromium } = require("playwright-core");

async function finishQuest(page) {
  // At the map's native dimensions each world coordinate is a screen coordinate.
  for (const [index, point] of [[137,356],[343,220],[592,385]].entries()) {
    await page.touchscreen.tap(...point);
    await page.waitForFunction(() => !document.getElementById("activate").disabled, null, {timeout:10000});
    await page.locator("#activate").tap();
    await page.waitForFunction(n => document.getElementById("counter").textContent === n+" / 3", index+1);
  }
  assert(await page.locator("#won").isVisible());
}

async function run() {
  const proc = spawn(process.execPath,[require.resolve("../server/server.cjs")],{env:{...process.env,PORT:"0",HOST:"127.0.0.1"}});
  let browser;
  try {
    const [line] = await once(proc.stdout,"data");
    const origin = "http://127.0.0.1:"+line.toString().match(/port: (\d+)/)[1];
    browser = await chromium.launch({executablePath:process.env.CHROME_BIN});
    const options = {viewport:{width:720,height:520},hasTouch:true,isMobile:true};
    const page = await browser.newPage(options);
    const errors = [];
    page.on("pageerror", err => errors.push(String(err)));
    const fileURL = pathToFileURL(path.join(__dirname,"../mobile/index.html")).href;
    await page.goto(fileURL);
    await page.locator("#solo").tap();
    await finishQuest(page);
    await page.locator("#again").tap();
    await page.locator("#online").tap();
    assert(await page.locator("#address").isVisible());

    const peer = await browser.newPage(options);
    await peer.goto(origin+"/?play=online");
    await page.goto(origin);
    await page.locator("#online").tap();
    await page.waitForFunction(() => document.getElementById("mode").textContent.includes("2 oyuncu"));
    await finishQuest(page);
    await peer.close();

    await page.locator("#again").tap();
    await page.setViewportSize({width:390,height:844});
    const dir = process.env.PREVIEW_DIR || await mkdtemp(path.join(os.tmpdir(),"constantine-touch-"));
    await page.screenshot({path:path.join(dir,"menu.png")});
    await page.locator("#solo").tap();
    await page.screenshot({path:path.join(dir,"rihtim.png")});
    assert(await page.locator("#activate").isVisible());
    assert.deepEqual(errors,[]);
    console.log("Offline file, two online clients, all three relays and portrait controls passed.");
  } finally {
    if(browser) await browser.close();
    proc.kill();
  }
}
run().catch(err => {console.error(err);process.exitCode=1});
