"use strict";
const el=id=>document.getElementById(id);
function showText(id, text) {
  const element=el(id);
  if(element.textContent!==text) element.textContent=text;
}
const canvas=el("harbour"), scene=harbourScene(canvas);
const fresh=()=>({...World.start,target:{...World.start}});
const state={playing:false,online:false,actor:fresh(),others:[],completed:[]};
let token="",generation=0,busy=false,nextMove=null,lastPoll=0,lastTime=0,peerCount=1;
async function request(path,method="GET",payload,credential=token) {
  const headers={}; if(credential)headers.Authorization="Bearer "+credential;
  if(payload)headers["Content-Type"]="application/json";
  const controller=new AbortController();
  const timer=setTimeout(()=>controller.abort(),5500);
  let response;
  try {
    response=await fetch("/api/"+path,{method,headers,body:payload?JSON.stringify(payload):undefined,cache:"no-store",signal:controller.signal});
  } finally { clearTimeout(timer); }
  if(!response.ok){
    const error=new Error(response.status===401?"Oturum sona erdi.":"Sunucu isteği tamamlanamadı.");
    error.status=response.status; throw error;
  }
  return response.json();
}
function accept(s){
  const self=s.players.find(p=>p.id===s.self);
  if(!self)throw Error("Oyuncu oturumu bulunamadı.");
  state.actor={...self,target:{...self.target}};
  state.others=s.players.filter(p=>p.id!==s.self);state.completed=s.completed;peerCount=s.players.length;
  if(state.completed.length===World.relays.length)win();
}
function view(playing){
  state.playing=playing;document.querySelector(".hud").hidden=!playing;
  document.querySelector(".playbar").hidden=!playing;el("cover").hidden=playing;el("won").hidden=true;
}
function reset(){
  if(token) request("session","DELETE",undefined,token).catch(()=>{});
  generation++;token="";busy=false;nextMove=null;lastPoll=0;peerCount=1;
  Object.assign(state,{playing:false,online:false,actor:fresh(),others:[],completed:[]});
  el("error").textContent="";el("feedback").textContent="";el("connect").hidden=true;
  el("solo").disabled=false;el("online").disabled=false;view(false);
}
function win(){
  state.playing=false;document.querySelector(".playbar").hidden=true;el("won").hidden=false;el("cover").hidden=true;
}
function warn(e){reset();el("error").textContent=e.message+" Tekrar bağlanabilir veya tek başına oynayabilirsin."}
el("solo").onclick=()=>{reset();view(true)};
async function join(){
  if(location.protocol==="file:"){el("connect").hidden=false;el("address").focus();return}
  reset();const gen=generation;el("solo").disabled=true;el("online").disabled=true;
  try{const s=await request("session","POST");if(gen!==generation)return;
    token=s.token;state.online=true;view(true);accept(s);
  }catch(e){if(gen===generation)warn(e)}
}
el("online").onclick=join;el("menu").onclick=reset;el("again").onclick=reset;
el("connect").onsubmit=e=>{
  e.preventDefault();
  try{const url=new URL(el("address").value);if(url.protocol!=="https:"||url.username||url.password)throw Error();
    location.href=url.origin+"/?play=online";
  }catch{el("error").textContent="Geçerli bir HTTPS adresi gir."}
};
async function networkStep(t,activate=false){
  if(busy||!state.online||!state.playing)return;
  if(!activate && !nextMove && t-lastPoll<230)return;
  const gen=generation;busy=true;lastPoll=t;
  try{let data;if(activate)data=await request("activate","POST");
    else if(nextMove){const point=nextMove;nextMove=null;data=await request("move","POST",point)}
    else data=await request("state");
    if(gen===generation)accept(data);
  }catch(e){if(gen===generation && e.status!==409)warn(e)}
  finally{if(gen===generation)busy=false}
}
canvas.addEventListener("pointerdown",e=>{
  if(!state.playing)return;const box=canvas.getBoundingClientRect();const p=scene.point(e.clientX-box.left,e.clientY-box.top);
  if(state.online){nextMove=p;networkStep(performance.now())}else state.actor.target=p;
});
el("activate").onclick=()=>{
  if(!state.playing)return;const r=World.nearest(state.actor,state.completed);if(!r)return;
  if(state.online){networkStep(performance.now(),true);return}
  state.completed.push(r.id);if(state.completed.length===World.relays.length)win();
};
function frame(t){
  const dt=Math.min(.12,(t-(lastTime||t))/1000);lastTime=t;
  if(state.playing){World.advance(state.actor,dt);for(const p of state.others)World.advance(p,dt);
    if(state.online)networkStep(t);
    const near=World.nearest(state.actor,state.completed);
    const disabled=!near||(state.online&&busy);
    if(el("activate").disabled!==disabled) el("activate").disabled=disabled;
    showText("mode",state.online?"Çevrim içi · "+peerCount+" oyuncu":"Tek oyuncu");
    showText("feedback",near?near.name+" rölesi yakında":"Yürümek için zemine dokun");
  }
  showText("counter",state.completed.length+" / "+World.relays.length);
  scene.draw(state,t);requestAnimationFrame(frame);
}
requestAnimationFrame(frame);
if(location.protocol!=="file:"&&new URLSearchParams(location.search).get("play")==="online")join();
