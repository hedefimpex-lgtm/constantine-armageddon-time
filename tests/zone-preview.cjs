"use strict";
const { chromium } = require("playwright-core");
const path = require("node:path");
const assert = require("node:assert/strict");
const { pathToFileURL } = require("node:url");

(async () => {
  const folder = process.argv[2];
  const browser = await chromium.launch({executablePath:process.env.CHROME_BIN});
  try {
    const page = await browser.newPage({viewport:{width:390,height:844},hasTouch:true,isMobile:true});
    const errors = [];
    page.on("pageerror",e=>errors.push(String(e)));
    await page.goto(pathToFileURL(path.join(folder,"zone00.html")).href);
    const pixels = () => page.locator("canvas").evaluate(c=>c.toDataURL());
    const initial = await pixels();
    const statistics = await page.evaluate(() => {
      const c=document.querySelector("canvas");
      const raw=c.getContext("2d").getImageData(0,0,c.width,c.height).data;
      let drawn=0;
      for(let i=0;i<raw.length;i+=4){if(raw[i]!==19 || raw[i+1]!==33 || raw[i+2]!==39) drawn++;}
      const m=JSON.parse(document.getElementById("mesh").textContent);
      return {drawn,vertices:m.vertices.length,triangles:m.triangles.length};
    });
    assert(statistics.drawn>1200 && statistics.vertices>100 && statistics.triangles>100);
    await page.screenshot({path:path.join(folder,"zone00-preview.png")});
    await page.getByRole("button",{name:"Yaklaştır",exact:true}).tap();
    assert.notEqual(await pixels(),initial);
    await page.getByRole("button",{name:"İlk görünüm",exact:true}).tap();
    assert.equal(await pixels(),initial);
    await page.mouse.move(190,300);await page.mouse.down();await page.mouse.move(260,330,{steps:5});await page.mouse.up();
    assert.notEqual(await pixels(),initial);assert.deepEqual(errors,[]);
    console.log("Original terrain preview:",statistics);
  } finally { await browser.close(); }
})().catch(err=>{console.error(err);process.exitCode=1;});
