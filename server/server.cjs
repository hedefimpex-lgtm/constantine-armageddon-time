"use strict";
const http = require("node:http");
const path = require("node:path");
const fs = require("node:fs/promises");
const crypto = require("node:crypto");
const world = require("../mobile/world.js");
const sessions = new Map();
const ttl = 5 * 60 * 1000;
const files = new Map([["/",["index.html","text/html"]],["/world.js",["world.js","text/javascript"]],
  ["/scene.js",["scene.js","text/javascript"]],["/game.js",["game.js","text/javascript"]],["/style.css",["style.css","text/css"]]]);
function expire(now) {
  for (const [token,p] of sessions) if (now - p.lastSeen > ttl) sessions.delete(token);
}
function sync(p, now) {
  world.advance(p,(now - p.updated) / 1000);
  p.updated = now;
}
function snapshot(p, now) {
  const players = [];
  for (const other of sessions.values()) {
    sync(other,now);
    players.push({id:other.id,x:other.x,y:other.y,target:other.target});
  }
  return {self:p.id,players,completed:p.completed};
}
async function body(req) {
  const chunks=[]; let size=0;
  for await (const chunk of req) {
    size+=chunk.length;
    if(size>2048) throw new Error("body");
    chunks.push(chunk);
  }
  return JSON.parse(Buffer.concat(chunks).toString("utf8")||"{}");
}
function json(res,status,value) {
  res.writeHead(status,{"Content-Type":"application/json; charset=utf-8","Cache-Control":"no-store"});
  res.end(JSON.stringify(value));
}
const server=http.createServer(async (req,res)=>{
  const url = (req.url||"/").split("?")[0];
  res.setHeader("X-Content-Type-Options","nosniff");
  try {
    if(req.method==="GET" && url==="/health") return json(res,200,{ok:true,version:1});
    if(req.method==="GET" && files.has(url)) {
      const [file,mime]=files.get(url);
      const data=await fs.readFile(path.join(__dirname,"../mobile",file));
      res.writeHead(200,{"Content-Type":mime+"; charset=utf-8"}); return res.end(data);
    }
    if(!url.startsWith("/api/")) return json(res,404,{error:"Bulunamadı"});
    const now=Date.now(); expire(now);
    if(url==="/api/session" && req.method==="POST") {
      if(sessions.size>=64) return json(res,503,{error:"Oda dolu"});
      const token=crypto.randomBytes(24).toString("hex");
      const p={id:crypto.randomBytes(8).toString("hex"),...world.start,target:{...world.start},
        completed:[],lastSeen:now,updated:now};
      sessions.set(token,p); return json(res,201,{token,...snapshot(p,now)});
    }
    const p=sessions.get((req.headers.authorization||"").replace(/^Bearer /,""));
    if(!p) return json(res,401,{error:"Oturum sona erdi"});
    p.lastSeen=now;
    if(url==="/api/session" && req.method==="DELETE") {
      sessions.delete(req.headers.authorization.slice(7)); return json(res,200,{ok:true});
    }
    if(url==="/api/state" && req.method==="GET") return json(res,200,snapshot(p,now));
    if(url==="/api/move" && req.method==="POST") {
      const input=await body(req);
      if(!input || !Number.isFinite(input.x)||!Number.isFinite(input.y)) return json(res,400,{error:"Geçersiz hedef"});
      sync(p,Date.now()); p.target=world.destination(input.x,input.y);
      return json(res,200,snapshot(p,Date.now()));
    }
    if(url==="/api/activate" && req.method==="POST") {
      sync(p,now); const relay=world.nearest(p,p.completed);
      if(!relay) return json(res,409,{error:"Bir röleye yaklaş"});
      p.completed.push(relay.id); return json(res,200,snapshot(p,now));
    }
    return json(res,404,{error:"Bulunamadı"});
  } catch (err) {
    if(!res.writableEnded) json(res,err instanceof SyntaxError || err.message==="body"?400:500,{error:"İstek tamamlanamadı"});
  }
});
server.requestTimeout=10000;
server.listen(Number(process.env.PORT||8787),process.env.HOST||"127.0.0.1",()=>{
  console.log("Constantine sunucusu hazır",server.address());
});
