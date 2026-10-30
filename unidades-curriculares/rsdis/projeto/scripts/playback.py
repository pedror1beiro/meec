"""Write a standalone playback, with no server, account or network dependency."""

import json


def write_playback(directory, config, trace, summary):
    payload = json.dumps({"config": config, "trace": trace, "summary": summary}).replace(
        "<", "\\u003c"
    )
    html = r"""<!doctype html>
<html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width">
<title>RSDIS lunar mission rehearsal</title>
<style>
*{box-sizing:border-box}body{margin:0;background:#10131b;color:#e8e9ed;font:15px system-ui,sans-serif}
main{max-width:1160px;margin:auto;padding:32px}h1{font-size:30px;margin:8px 0}p{color:#aeb7ca;line-height:1.5}
.eyebrow{font:12px monospace;color:#9baeff;letter-spacing:2px}.notice{padding:12px 16px;background:#26283b;border-left:3px solid #aab6ff}
.layout{display:grid;grid-template-columns:minmax(0,1fr) 260px;gap:20px;margin:24px 0}canvas{width:100%;height:auto;border:1px solid #303746;border-radius:10px}
.card{background:#191e2a;border:1px solid #303746;border-radius:10px;padding:18px;margin-bottom:12px}
.label{color:#9eaac0;font-size:12px;text-transform:uppercase;letter-spacing:1px}.value{font-size:23px;margin:6px 0}
button{background:#aab6ff;color:#111629;border:0;border-radius:6px;padding:9px 15px;cursor:pointer;font-weight:650}button:focus-visible,input:focus-visible,select:focus-visible{outline:3px solid white}
.controls{display:flex;gap:12px;align-items:center;flex-wrap:wrap}input{flex:1;min-width:150px;accent-color:#aab6ff}select{padding:7px;border-radius:5px;background:#232a3b;color:#fff}
.bar{height:6px;background:#303747;border-radius:3px;overflow:hidden}.fill{height:100%;background:#aab6ff}
.legend{font-size:12px;color:#abb7cc}.rover-name{font-weight:650}.mode{font-size:13px;color:#b8c4dc;margin:8px 0}
@media(max-width:750px){main{padding:18px}.layout{grid-template-columns:1fr}.cards{display:grid;grid-template-columns:1fr 1fr;gap:10px}}
</style><main><div class="eyebrow">RSDIS / COOPERATIVE LUNAR EXPLORATION</div>
<h1>Mission rehearsal</h1><p class="notice">Offline kinematic rehearsal with oracle detections. This view checks mission logic; it does not demonstrate Gazebo physics, camera accuracy or lunar realism.</p>
<div class="layout"><section><canvas id="field" width="850" height="610" aria-label="Map showing rover paths, targets and charging bases"></canvas>
<p class="legend">R1: light blue &nbsp; R2: amber &nbsp; Dashed ring: discovered &nbsp; Check: confirmed &nbsp; Squares: charging pads</p>
<div class="controls"><button id="play" type="button">Play</button><input id="time" aria-label="Mission time" type="range" min="0" value="0"><span id="clock">0.0 s</span><select id="speed" aria-label="Playback speed"><option value="1">1×</option><option value="5" selected>5×</option><option value="15">15×</option></select></div>
</section><aside><div class="card"><div class="label">Allocation strategy</div><div class="value" id="strategy"></div><div class="label">Confirmed targets</div><div class="value" id="confirmed"></div><p id="result"></p></div><div class="cards" id="rovers"></div></aside></div>
<p>The actual ROS prototype uses camera images and a known-size colour marker detector. Ground-truth odometry and an accelerated synthetic battery are explicit prototype assumptions.</p></main>
<script id="mission-data" type="application/json">__DATA__</script><script>
const data=JSON.parse(document.getElementById('mission-data').textContent),frames=data.trace;
const canvas=document.getElementById('field'),ctx=canvas.getContext('2d'),slider=document.getElementById('time');
const colours=['#a9c7ff','#ffcc81','#c0e7b8'];let index=0,playing=false,last=null,acc=0;
slider.max=Math.max(0,frames.length-1);document.getElementById('strategy').textContent=data.summary.strategy;
document.getElementById('result').textContent='Run outcome: '+data.summary.reason.replaceAll('_',' ');
const b=data.config.map_bounds||[-18,18,-13,13],bounds={x0:b[0],x1:b[1],y0:b[2],y1:b[3]};
const scale=Math.min((canvas.width-90)/(b[1]-b[0]),(canvas.height-90)/(b[3]-b[2]));
function p(x,y){return [canvas.width/2+(x-(b[0]+b[1])/2)*scale,canvas.height/2-(y-(b[2]+b[3])/2)*scale]}
function circle(x,y,r,fill){ctx.beginPath();ctx.arc(x,y,r,0,Math.PI*2);ctx.fillStyle=fill;ctx.fill()}
function render(){if(!frames.length)return;const f=frames[index];ctx.fillStyle='#171c27';ctx.fillRect(0,0,canvas.width,canvas.height);ctx.lineWidth=1;
const grid=bounds.x1-bounds.x0>45?10:5;
for(let x=Math.ceil(bounds.x0/grid)*grid;x<=bounds.x1;x+=grid){let a=p(x,bounds.y0),b=p(x,bounds.y1);ctx.strokeStyle='#252d3d';ctx.beginPath();ctx.moveTo(...a);ctx.lineTo(...b);ctx.stroke();ctx.fillStyle='#71809a';ctx.font='11px monospace';ctx.fillText(x+' m',a[0]-10,a[1]+22)}
for(let y=Math.ceil(bounds.y0/grid)*grid;y<=bounds.y1;y+=grid){let a=p(bounds.x0,y),b=p(bounds.x1,y);ctx.beginPath();ctx.moveTo(...a);ctx.lineTo(...b);ctx.stroke()}
(data.config.hazards||[]).forEach(h=>{let q=p(...h.position);circle(...q,h.radius*scale,h.kind==='crater'?'#0c1018':'#444750');ctx.strokeStyle='#73757b';ctx.beginPath();ctx.arc(...q,h.radius*scale,0,2*Math.PI);ctx.stroke()});
(data.config.sectors||[]).forEach(s=>{let q=p(...s.position);ctx.fillStyle='#71809a';ctx.font='10px monospace';ctx.fillText(s.name,q[0]-35,q[1])});
data.config.rovers.forEach((r,k)=>{let a=p(...r.spawn);ctx.strokeStyle=colours[k%colours.length];ctx.strokeRect(a[0]-15,a[1]-15,30,30);ctx.fillStyle=colours[k%colours.length];ctx.fillText('BASE '+(k+1),a[0]-22,a[1]+30);
ctx.strokeStyle=colours[k%colours.length]+'66';ctx.lineWidth=2;ctx.beginPath();for(let j=0;j<=index;j++){let q=p(...frames[j].rovers[k].pose);j?ctx.lineTo(...q):ctx.moveTo(...q)}ctx.stroke()});
data.config.targets.forEach(t=>{let q=p(...t.position),state=f.targets[t.id],c=t.colour;circle(...q,8,'rgb('+c.slice(0,3).map(v=>Math.round(v*255)).join(',')+')');ctx.strokeStyle='#d6deed';ctx.lineWidth=1;ctx.setLineDash(state?[4,3]:[]);ctx.beginPath();ctx.arc(...q,14,0,Math.PI*2);ctx.stroke();ctx.setLineDash([]);ctx.fillStyle='#dce3f1';ctx.font='12px system-ui';ctx.fillText(t.id,q[0]+18,q[1]+4);if(state==='confirmed'){ctx.fillStyle='#b9edbf';ctx.font='bold 24px system-ui';ctx.fillText('✓',q[0]-9,q[1]-22)}});
f.rovers.forEach((r,k)=>{if(r.plan){ctx.setLineDash([5,4]);ctx.strokeStyle=colours[k%colours.length];ctx.beginPath();let a=p(...r.pose);ctx.moveTo(...a);r.plan.forEach(v=>ctx.lineTo(...p(...v)));ctx.stroke();ctx.setLineDash([])}let q=p(...r.pose),yaw=r.pose[2];ctx.save();ctx.translate(...q);ctx.rotate(-yaw);ctx.fillStyle=colours[k%colours.length];ctx.beginPath();ctx.moveTo(15,0);ctx.lineTo(-10,-9);ctx.lineTo(-10,9);ctx.closePath();ctx.fill();ctx.restore();ctx.fillStyle='#fff';ctx.font='bold 12px system-ui';ctx.fillText('R'+(k+1),q[0]-8,q[1]-16)});
document.getElementById('clock').textContent=f.time.toFixed(1)+' s';slider.value=index;
document.getElementById('confirmed').textContent=Object.values(f.targets).filter(x=>x==='confirmed').length+' / '+data.config.targets.length;
const list=document.getElementById('rovers');list.replaceChildren();f.rovers.forEach((r,k)=>{let card=document.createElement('div');card.className='card';let name=document.createElement('div');name.className='rover-name';name.textContent=r.id;name.style.color=colours[k%colours.length];let mode=document.createElement('div');mode.className='mode';mode.textContent=r.mode+' · '+Math.round(r.battery*100)+'%';let bar=document.createElement('div');bar.className='bar';let fill=document.createElement('div');fill.className='fill';fill.style.width=(r.battery*100)+'%';fill.style.background=colours[k%colours.length];bar.append(fill);card.append(name,mode,bar);list.append(card)})}
document.getElementById('play').onclick=()=>{if(index>=frames.length-1)index=0;playing=!playing;document.getElementById('play').textContent=playing?'Pause':'Play'};
slider.oninput=()=>{index=Number(slider.value);render()};
function animate(now){if(last!==null&&playing){acc+=(now-last)/1000*Number(document.getElementById('speed').value);while(acc>=0.5&&index<frames.length-1){index++;acc-=0.5}if(index>=frames.length-1){playing=false;document.getElementById('play').textContent='Play'}render()}last=now;requestAnimationFrame(animate)}render();requestAnimationFrame(animate);
</script></html>"""
    (directory / "playback.html").write_text(html.replace("__DATA__", payload), encoding="utf-8")
