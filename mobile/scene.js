"use strict";
function harbourScene(canvas) {
  const c=canvas.getContext("2d");
  const bg=document.createElement("canvas"); bg.width=World.width; bg.height=World.height;
  const g=bg.getContext("2d");
  const rect=(ctx,col,x,y,w,h)=>{ctx.fillStyle=col;ctx.fillRect(x,y,w,h)};
  const line=(ctx,col,x,y,xx,yy,width=1)=>{ctx.strokeStyle=col;ctx.lineWidth=width;ctx.beginPath();ctx.moveTo(x,y);ctx.lineTo(xx,yy);ctx.stroke()};
  const poly=(ctx,col,pts)=>{ctx.fillStyle=col;ctx.beginPath();pts.forEach(([x,y],i)=>i?ctx.lineTo(x,y):ctx.moveTo(x,y));ctx.closePath();ctx.fill()};
  const dot=(ctx,col,x,y,r)=>{ctx.fillStyle=col;ctx.beginPath();ctx.arc(x,y,r,0,Math.PI*2);ctx.fill()};
  let seed=81452;
  function random(){seed=(1664525*seed+1013904223)>>>0;return seed/4294967296}
  const sky=g.createLinearGradient(0,0,0,174);sky.addColorStop(0,"#192d3c");sky.addColorStop(1,"#87968b");
  g.fillStyle=sky;g.fillRect(0,0,720,190);
  dot(g,"#dbcfa1",537,45,18);
  for(let i=0;i<60;i++) dot(g,"#c4cbb98a",random()*720,random()*65,random()+0.25);
  // A distant city skyline, a tower and the shoreline across the water.
  for(let i=0;i<76;i++){const x=i*10,h=11+random()*24;rect(g,"#4b6667",x,110-h,13,h)}
  rect(g,"#334e54",111,58,13,48);poly(g,"#334e54",[[106,60],[118,36],[128,60]]);line(g,"#334e54",118,38,118,28);
  for(let i=0;i<37;i++){
    const x=i*20+random()*7,h=12+random()*22;
    rect(g,"#365356",x,111-h,20,h);poly(g,"#365356",[[x,111-h],[x+12,104-h],[x+20,111-h]]);
    for(let j=0;j<3;j++) if(random()>.48) rect(g,"#d6a95390",x+3+j*5,106-h+8,2,3);
  }
  const sea=g.createLinearGradient(0,106,0,183);sea.addColorStop(0,"#486c70");sea.addColorStop(1,"#203f4d");
  g.fillStyle=sea;g.fillRect(0,110,720,74);
  for(let i=0;i<360;i++){const x=random()*720,y=113+random()*64;line(g,random()>.7?"#9ab3a870":"#78979755",x,y,x+2+random()*17,y);}
  rect(g,"#5b675f",0,181,720,9);rect(g,"#d0ab71",0,182,720,2);
  const ground=g.createLinearGradient(0,185,0,520);ground.addColorStop(0,"#536057");ground.addColorStop(1,"#293c40");
  g.fillStyle=ground;g.fillRect(0,191,720,329);
  for(let j=0;j<37;j++){
    const y=191+j*10;line(g,"#80908725",0,y,720,y);
    for(let i=0;i<30;i++){const x=i*28+(j%2)*14;line(g,"#0d242828",x,y,x-3,y+10)}
  }
  for(let i=0;i<900;i++){let x=random()*720,y=193+random()*327;rect(g,random()>.5?"#d6c39a26":"#14282d4a",x,y,random()*5+1,1)}
  for(const x of [39,214,435,675]){
    rect(g,"#233a3f",x,163,3,26);rect(g,"#243c41",x-3,177,9,3);
    dot(g,"#eec97c",x+1.5,160,3.2);
  }
  for(let x=8;x<720;x+=20) {rect(g,"#263d40",x,177,3,11);line(g,"#40565a",x,178,x+20,178)}
  function warehouse(x,y,w,h){
    poly(g,"#23363b",[[x+7,y+2],[x+w+27,y+8],[x+w+31,y+h+14],[x+14,y+h+9]]);
    rect(g,"#3c4a49",x,y,w,h);rect(g,"#212f35",x+w-7,y,7,h);
    poly(g,"#53625b",[[x-8,y+3],[x+w/2,y-17],[x+w+7,y+3]]);
    line(g,"#bcaa76",x-8,y+3,x+w/2,y-17,1.5);
    for(let wx=x+7;wx<x+w-10;wx+=16){rect(g,"#253d40",wx,y+9,9,14);rect(g,"#c4a465",wx+2,y+11,5,8);line(g,"#435552",wx+4,y+9,wx+4,y+23)}
  }
  warehouse(-34,208,82,45);warehouse(668,231,81,51);warehouse(18,481,99,44);warehouse(553,492,108,40);
  for(const [x,y] of [[26,283],[41,299],[682,337],[680,354]]){rect(g,"#625d4b",x,y,16,16);line(g,"#ab976d",x+1,y+1,x+15,y+15);line(g,"#222f30",x,y+15,x+17,y+15,2)}
  let scale=1,ox=0,oy=0;
  function draw(state,t){
    const w=canvas.clientWidth,h=canvas.clientHeight,dpr=Math.min(window.devicePixelRatio||1,2);
    if(canvas.width!==Math.round(w*dpr)||canvas.height!==Math.round(h*dpr)){canvas.width=Math.round(w*dpr);canvas.height=Math.round(h*dpr)}
    const a=state.actor;
    scale=Math.min(Math.max(w/720,h/520),Math.max(w/410,h/600));
    if(w/720>scale)scale=w/720;
    if(h/520>scale)scale=h/520;
    const fx=state.playing?a.x:445,fy=state.playing?a.y:255;
    ox=Math.min(0,Math.max(w-720*scale,w/2-fx*scale)); oy=Math.min(0,Math.max(h-520*scale,h/2-fy*scale));
    c.setTransform(dpr,0,0,dpr,0,0);c.fillStyle="#243941";c.fillRect(0,0,w,h);
    c.translate(ox,oy);c.scale(scale,scale);c.drawImage(bg,0,0);
    for(let i=0;i<12;i++){
      const x=(i*77+t*.008)%735-15,y=116+(i*19)%59;
      line(c,"#bbd4c45a",x,y,x+11,y);
    }
    for(const [i,r] of World.relays.entries()){
      const on=state.completed.includes(r.id), col=on?"#ffe28a":"#e5b461";
      const halo=c.createRadialGradient(r.x,r.y,1,r.x,r.y,on?56:25);
      halo.addColorStop(0,on?"#f6d47787":"#ecc67636");halo.addColorStop(1,"#ffd87d00");c.fillStyle=halo;c.fillRect(r.x-60,r.y-60,120,120);
      line(c,"#344448",r.x+1,r.y,r.x+10,r.y+6,4);rect(c,"#162d32",r.x-4,r.y-13,8,14);
      rect(c,col,r.x-3,r.y-12,6,5);rect(c,"#728078",r.x-5,r.y-15,10,3);
      c.strokeStyle=on?"#f6d68093":"#d0c09b70";c.lineWidth=1;c.beginPath();c.ellipse(r.x,r.y+2,12+Math.sin(t/600+i),5,0,0,Math.PI*2);c.stroke();
      c.textAlign="center";c.font="bold 9px sans-serif";c.fillStyle="#f3e4b7";c.fillText(r.name,r.x,r.y+18);
    }
    if(state.playing && Math.hypot(a.target.x-a.x,a.target.y-a.y)>6){
      const {x,y}=a.target;line(c,"#dfcb93",x-3,y,x+3,y);line(c,"#dfcb93",x,y-3,x,y+3);
    }
    function actor(p,own){
      const {x,y}=p;dot(c,"#0d222967",x+2,y,7);rect(c,"#172830",x-3,y-4,2,5);rect(c,"#172830",x+1,y-4,2,5);
      poly(c,own?"#ce9b57":"#76b8af",[[x-4,y-10],[x+3,y-10],[x+5,y-2],[x-5,y-2]]);
      dot(c,"#cab796",x,y-12,3);rect(c,"#283b41",x-3,y-16,6,3);
      if(own){poly(c,"#ffe189",[[x-3,y-22],[x+3,y-22],[x,y-19]])}
    }
    for(const p of state.others) actor(p,false);
    actor(a,true);
  }
  return {draw,point:(x,y)=>World.destination((x-ox)/scale,(y-oy)/scale)};
}
