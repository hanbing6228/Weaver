import { Capacitor } from "@capacitor/core";
import { Haptics, ImpactStyle } from "@capacitor/haptics";
import { StatusBar, Style } from "@capacitor/status-bar";
import { SplashScreen } from "@capacitor/splash-screen";


function apiRoot() {
  const base = (window.WEAVER_API || "").replace(/\/$/, "");
  return base ? `${base}/api/v1` : "/api/v1";
}

const $=id=>document.getElementById(id);
function toast(m){const t=$('toast');t.textContent=m;t.classList.add('show');setTimeout(()=>t.classList.remove('show'),2300);}
function nav(scr,tab){
  document.querySelectorAll('.scr').forEach(s=>s.classList.remove('on'));
  $(scr).classList.add('on');$(scr).scrollTop=0;
  document.querySelectorAll('.tab').forEach(t=>t.classList.remove('on'));
  if(tab)$(tab).classList.add('on');
}
const HZ=['1小时后','今晚','明天','一周后','一个月后','一年后','五年后','十年后'];
let hIdx=1,thIdx=5,stats={d:0,r:0,nh:0};
function stepH(d){hIdx=Math.max(0,Math.min(HZ.length-1,hIdx+d));$('h-val').textContent=HZ[hIdx];}
function stepTH(d){thIdx=Math.max(0,Math.min(HZ.length-1,thIdx+d));$('th-val').textContent=HZ[thIdx];}
function fillAB(a,b,h){$('optA').value=a;$('optB').value=b;hIdx=h;$('h-val').textContent=HZ[h];toast('已填入灵感 · 可随意修改');}
function bumpStats(){$('st-decisions').textContent=stats.d;$('st-released').textContent=stats.r;$('st-neihao').textContent=stats.nh>0?stats.nh+'格':'—';}

async function callAI(system,user,mt){
  const res=await fetch(`${apiRoot()}/llm/json`,{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({system,user,max_tokens:mt||800})});
  if(!res.ok) throw new Error(await res.text());
  return res.json();
}


// ===== 程序化场景渲染（蓝色系配色）=====
function sceneSVG(s,H){
  H=H||330;
  const mood=Math.max(0,Math.min(10,s.mood??5)),energy=Math.max(0,Math.min(10,s.energy??5));
  let pal;
  if(mood>=7) pal={s1:'#CDDEFC',s2:'#EAF3FF',gr:'#A8C8F0',fig:'#588CE3',skin:'#F0C9A0',ac:'#FFFFFF',hair:'#3A4A66'};
  else if(mood>=4) pal={s1:'#7FA3D4',s2:'#A6C2E4',gr:'#6E8FBC',fig:'#4A6FA8',skin:'#E2B894',ac:'#D5E4F8',hair:'#2E3C58'};
  else pal={s1:'#14233F',s2:'#22365C',gr:'#1B2C4A',fig:'#3D5278',skin:'#C9A07E',ac:'#5C7BA8',hair:'#0E1830'};
  const gY=H-46, headY=(gY-78)-energy*2.2, leanX=180+(5-energy)*1.6, shY=headY+12;
  const w=s.weather||'cloud';let wx='';
  if(w==='rain')wx=`<g class="sc-rain" stroke="${pal.ac}" stroke-width="1.4" stroke-linecap="round" opacity="0.6">
    <line x1="40" y1="22" x2="36" y2="34"/><line x1="100" y1="44" x2="96" y2="56"/><line x1="160" y1="18" x2="156" y2="30"/>
    <line x1="240" y1="34" x2="236" y2="46"/><line x1="300" y1="20" x2="296" y2="32"/><line x1="330" y1="54" x2="326" y2="66"/></g>
    <ellipse class="sc-cloud" cx="90" cy="28" rx="36" ry="12" fill="${pal.ac}" opacity="0.3"/>
    <ellipse class="sc-cloud" cx="270" cy="38" rx="42" ry="13" fill="${pal.ac}" opacity="0.22"/>`;
  else if(w==='sun')wx=`<circle cx="294" cy="46" r="18" fill="#F5C96A"/>
    <g class="sc-ray" stroke="#F5C96A" stroke-width="2.4" stroke-linecap="round" opacity="0.8" style="transform-origin:294px 46px">
    <line x1="294" y1="18" x2="294" y2="10"/><line x1="294" y1="74" x2="294" y2="82"/>
    <line x1="266" y1="46" x2="258" y2="46"/><line x1="322" y1="46" x2="330" y2="46"/>
    <line x1="275" y1="27" x2="269" y2="21"/><line x1="313" y1="65" x2="319" y2="71"/></g>`;
  else if(w==='stars')wx=`<circle cx="60" cy="32" r="1.8" fill="#DCE8FA"/><circle cx="140" cy="20" r="1.4" fill="#DCE8FA"/>
    <circle cx="220" cy="40" r="1.8" fill="#DCE8FA"/><circle cx="306" cy="24" r="1.5" fill="#DCE8FA"/>
    <circle cx="276" cy="56" r="1.2" fill="#DCE8FA"/><circle cx="288" cy="42" r="12" fill="#E5EDF8" opacity="0.9"/>`;
  else if(w==='sunset')wx=`<circle cx="290" cy="64" r="21" fill="#F0A868" opacity="0.92"/><rect x="0" y="60" width="360" height="3" fill="#F0A868" opacity="0.3"/>`;
  else wx=`<ellipse class="sc-cloud" cx="96" cy="36" rx="40" ry="13" fill="${pal.ac}" opacity="0.45"/>
    <ellipse class="sc-cloud" cx="262" cy="28" rx="46" ry="14" fill="${pal.ac}" opacity="0.32"/>`;
  const sparks=mood>=8?`<g fill="#F5C96A"><circle class="sc-spark" cx="140" cy="${gY-40}" r="2.4"/>
    <circle class="sc-spark s2" cx="226" cy="${gY-56}" r="2"/><circle class="sc-spark s3" cx="160" cy="${gY-70}" r="1.8"/></g>`:'';
  const face=mood>=6?`<path d="M${leanX-5} ${headY+4} q5 4 10 0" stroke="#9A6A40" stroke-width="1.6" fill="none" stroke-linecap="round"/>`
    :mood<=3?`<path d="M${leanX-5} ${headY+6} q5 -3 10 0" stroke="#7A5638" stroke-width="1.5" fill="none" stroke-linecap="round"/>`:'';
  const prop=s.emoji?`<text class="sc-prop" x="${leanX+44}" y="${headY+8}" font-size="30">${s.emoji}</text>`:'';
  return `<rect width="360" height="${H}" fill="${pal.s2}"/><rect width="360" height="${gY-16}" fill="${pal.s1}"/>${wx}
    <rect x="0" y="${gY}" width="360" height="${H-gY}" fill="${pal.gr}"/>
    <circle cx="${leanX}" cy="${headY}" r="12" fill="${pal.skin}"/>
    <path d="M${leanX-12} ${headY-4} q12 -13 24 0 l0 -4 q-12 -10 -24 0 Z" fill="${pal.hair}"/>${face}
    <path d="M${leanX} ${shY} q-${15+(5-energy)*2} ${6+(5-energy)} -17 ${gY-shY} l34 0 q${2-(5-energy)} -${(gY-shY)*0.85} -17 -${gY-shY}" fill="${pal.fig}"/>
    <path d="M${leanX-13} ${shY+12} q-${8+(5-energy)*2} ${10+(5-energy)*2} -4 20" stroke="${pal.fig}" stroke-width="7" stroke-linecap="round" fill="none"/>
    <path d="M${leanX+13} ${shY+12} q${energy>=6?12:6} ${energy>=6?4:14} ${energy>=6?16:8} ${energy>=6?0:12}" stroke="${pal.fig}" stroke-width="7" stroke-linecap="round" fill="none"/>
    ${sparks}${prop}`;
}

// ===== 拔河 =====
let fightData=null,knotPos=50,adopted=0;
function summonBrains(){
  const a=$('optA').value.trim(),b=$('optB').value.trim();
  if(!a||!b){toast('先填好选项 A 和 B');return;}
  $('btn-fight').disabled=true;$('tk-fight').classList.add('show');
  callAI(`你是Weaver.AI左右脑辩论模块。生成理性脑与感性脑的辩论，判断哪个选项偏理性哪个偏感性。输出严格JSON无markdown：{"rational_side":"A或B","emotional_side":"A或B","rational":["理由1","理由2","理由3"],"emotional":["理由1","理由2","理由3"]}。理由口语化扎心具体，每条25字内，像脑内真实声音。`,
    `选项A：${a}；选项B：${b}；时间视角：${HZ[hIdx]}；情绪能量${$('e-range').value}/100，意志力${$('w-range').value}/100`,600)
  .then(r=>{fightData=r;renderFight(r);})
  .catch(()=>{fightData={rational_side:'B',emotional_side:'A',
    rational:['明早的你会感谢今晚收手的你','这股冲动30分钟后就会消失','长期账户比即时快感值钱'],
    emotional:['人生苦短，此刻的快乐也是真的','一直绷着迟早大反弹','你今天已经够辛苦了，值得犒赏']};renderFight(fightData);})
  .finally(()=>{$('btn-fight').disabled=false;$('tk-fight').classList.remove('show');});
}
function renderFight(r){
  knotPos=50;adopted=0;
  $('r-side').textContent=r.rational_side||'B';$('e-side').textContent=r.emotional_side||'A';
  $('args-l').innerHTML=(r.rational||[]).map(t=>`<div class="arg l" onclick="adoptArg(this,'l')">${t}<span class="at">✓ 已看清</span></div>`).join('');
  $('args-r').innerHTML=(r.emotional||[]).map(t=>`<div class="arg r" onclick="adoptArg(this,'r')">${t}<span class="at">✓ 已看清</span></div>`).join('');
  $('nh').textContent='100';$('nh').style.color='var(--bad)';updateKnot();
  nav('s-fight','t-crystal');
}
function adoptArg(el,side){
  const was=el.classList.contains('adopted');
  el.classList.toggle('adopted');
  knotPos=Math.max(12,Math.min(88,knotPos+(side==='l'?-9:9)*(was?-1:1)));
  adopted+=was?-1:1;updateKnot();
  const nh=Math.max(16,100-adopted*14);
  $('nh').textContent=nh;
  $('nh').style.color=nh<50?'var(--ok)':nh<80?'#C9A05A':'var(--bad)';
}
function updateKnot(){
  $('knot').style.left=knotPos+'%';
  const d=knotPos-50;
  $('lean').textContent=Math.abs(d)<6?'势均力敌 · 这就是你卡住的原因'
    :d<0?`理性脑领先 ${Math.abs(Math.round(d*2))}% · 倾向 ${fightData?.rational_side||'B'}`
    :`感性脑领先 ${Math.round(d*2)}% · 倾向 ${fightData?.emotional_side||'A'}`;
}

// ===== 隔板分镜 =====
let boardData=null,actIdx=0,patternCtx=null;
function castBoard(){
  const a=$('optA').value.trim(),b=$('optB').value.trim();
  $('btn-board').disabled=true;$('tk-board').classList.add('show');
  const lean=knotPos<44?'理性脑':knotPos>56?'感性脑':'均衡';
  callAI(`你是Weaver.AI水晶球分镜导演兼模式侦探。任务1：为两个选项各拍三幕短片推演到指定时间，每幕画面感强、具体到物件动作、不说教。任务2：侦测这个选择背后是否藏着反复出现的旧心理模式（如惯性回避、惯性讨好、惯性自我惩罚）——只有明显时才报，日常小事多数没有。输出严格JSON无markdown：
{"A":{"frames":[{"t":"·时间标签","caption":"旁白32字内","mood":0到10,"energy":0到10,"weather":"rain|cloud|sun|stars|sunset","emoji":"1个emoji"},{},{}]},"B":{"frames":[同3幕]},"verdict":"裁决，温柔但明确，55字内","lean":"A或B","confidence":55到95,"pattern":null或{"name":"模式名6字内","hint":"指出这个模式与建议去时光机找根源，45字内","when_guess":"猜测根源时期如·多年前的某段关系","scene_guess":"一句话猜测根源场景"}}`,
    `选项A：${a}；选项B：${b}。推演到${HZ[hIdx]}。情绪能量${$('e-range').value}/100，意志力${$('w-range').value}/100，拔河${lean}占优。三幕时间从现在渐进推到${HZ[hIdx]}。`,1300)
  .then(r=>renderBoard(r,a,b))
  .catch(()=>renderBoard(fbBoard(),a,b))
  .finally(()=>{$('btn-board').disabled=false;$('tk-board').classList.remove('show');});
}
function fbBoard(){return {A:{frames:[
    {t:'· 5分钟后',caption:'冰柜门打开，多巴胺先到货。第一口下去，今天的辛苦好像被承认了。',mood:8,energy:7,weather:'stars',emoji:'🍦'},
    {t:'· 40分钟后',caption:'糖分回落，有点撑，刷着手机吃完最后几口，睡意被推迟了。',mood:5,energy:4,weather:'cloud',emoji:'📱'},
    {t:'· 明早',caption:'闹钟响第三遍。空腹血糖高了一格，早晨第一个情绪是轻微自责。',mood:3,energy:3,weather:'rain',emoji:'⏰'}]},
  B:{frames:[
    {t:'· 5分钟后',caption:'不甘心地刷完牙。躺下时大脑还在抗议：就这？今天就这么结束？',mood:4,energy:4,weather:'stars',emoji:'🛏️'},
    {t:'· 20分钟后',caption:'抗议声变小。黑暗里呼吸慢下来，身体接管，比想象中快地沉下去。',mood:6,energy:5,weather:'stars',emoji:'🌙'},
    {t:'· 明早',caption:'闹钟第一遍就醒。血糖平稳，脸不肿，今天的意志力账户是满的。',mood:9,energy:9,weather:'sun',emoji:'☀️'}]},
  verdict:'意志力只剩40，硬抗不现实——但B的代价只有20分钟不甘心，A的代价是明天一整天。划算。',lean:'B',confidence:78,
  pattern:{name:'深夜补偿',hint:'你似乎习惯用深夜的放纵补偿白天的压抑。这个回路可能有更早的源头，建议去时光机看看。',when_guess:'·更早需要靠自己哄自己的时期',scene_guess:'某个没人安慰、只能自己想办法的夜晚'}};}
function renderBoard(r,a,b){
  boardData=r;actIdx=0;stats.d++;stats.nh+=adopted;bumpStats();
  $('wtag-a').textContent='A · '+a.slice(0,10);
  $('wtag-b').textContent='B · '+b.slice(0,10);
  $('ct-a').textContent='A · '+a.slice(0,12);
  $('ct-b').textContent='B · '+b.slice(0,12);
  $('board-sub').textContent=`推演至${HZ[hIdx]} · 上下拖隔板对比`;
  $('acts').innerHTML=[0,1,2].map(i=>`<button class="act${i===0?' on':''}" id="act-${i}" onclick="showAct(${i})">第${['一','二','三'][i]}幕 ${r.A.frames[i]?.t||''}</button>`).join('');
  $('vd').textContent=r.verdict||'';
  $('vd-c').textContent=`裁决倾向：选项 ${r.lean} · 置信度 ${r.confidence||75}% · 内耗已外包`;
  if(r.pattern){patternCtx=r.pattern;$('pt-text').textContent=`「${r.pattern.name}」— ${r.pattern.hint}`;$('pattern').classList.add('show');}
  else{patternCtx=null;$('pattern').classList.remove('show');}
  showAct(0);setWipe(50);
  nav('s-board','t-crystal');
}
function showAct(i){
  actIdx=i;
  [0,1,2].forEach(x=>$('act-'+x)?.classList.toggle('on',x===i));
  const fa=boardData.A.frames[i],fb=boardData.B.frames[i];
  $('svg-a').innerHTML=sceneSVG(fa,330);
  $('svg-b').innerHTML=sceneSVG(fb,330);
  $('cap-a').textContent=(fa.t?fa.t+' ':'')+fa.caption;
  $('cap-b').textContent=(fb.t?fb.t+' ':'')+fb.caption;
}
// 上下拉隔板
function makeWipe(zoneId,topId,divId,handleId){
  const zone=$(zoneId);
  function set(p){
    p=Math.max(6,Math.min(94,p));
    $(topId).style.clipPath=`inset(0 0 ${100-p}% 0)`;
    $(divId).style.top=p+'%';
    $(handleId).style.top=p+'%';
  }
  set(50);
  let drag=false;
  zone.addEventListener('pointerdown',e=>{drag=true;zone.setPointerCapture(e.pointerId);mv(e);});
  zone.addEventListener('pointermove',e=>{if(drag)mv(e);});
  zone.addEventListener('pointerup',()=>drag=false);
  zone.addEventListener('pointercancel',()=>drag=false);
  function mv(e){const r=zone.getBoundingClientRect();set((e.clientY-r.top)/r.height*100);}
  return set;
}
let setWipe,setTWipe;

// 打通：水晶球 → 时光机
function goHeal(){
  if(patternCtx){
    $('tm-when').value=patternCtx.when_guess?.replace(/^·\s?/,'')||'';
    $('tm-scene').value=patternCtx.scene_guess||'';
    toast('已带入水晶球检测到的线索');
  }
  nav('s-tin','t-time');
}
// 打通：时光机 → 水晶球
function backToCrystal(){
  const e=$('e-range');e.value=Math.min(100,parseInt(e.value)+15);$('e-val').textContent=e.value;
  const w=$('w-range');w.value=Math.min(100,parseInt(w.value)+15);$('w-val').textContent=w.value;
  toast('情绪能量与意志力 +15 · 用新参数重测');
  nav('s-cin','t-crystal');
}

// ===== 时光机 =====
function startGuide(){
  const when=$('tm-when').value.trim(),scene=$('tm-scene').value.trim();
  if(!when&&!scene){toast('先写下那个时刻，碎片也可以');return;}
  $('btn-guide').disabled=true;$('tk-guide').classList.add('show');
  callAI(`你是Weaver.AI时光机回溯引导师，融合催眠引导与系统排列，语言现代克制不玄学。定制回溯引导词。输出严格JSON无markdown：{"guide":["第1句","第2句","第3句","第4句","第5句"]}。每句20-35字。结构：1呼吸落地安全感 2观察者身份接近时刻 3看见当时的自己与细节 4确认情绪在身体的位置 5提醒她带着全部资源回来了可以开口了。第二人称缓慢温和。`,
    `时刻：${when}。场景：${scene}。残留情绪：${$('tm-e-range').value}/100`,500)
  .then(r=>renderGuide(r.guide))
  .catch(()=>renderGuide(['先让肩膀松下来，做一次比平时长一点的呼气，感觉椅子稳稳托着你。','像看一部旧电影那样慢慢靠近那个时刻——你只是观察者，随时可以暂停。','画面渐渐清晰：看见那时的你站在那里，看清她的表情、她的姿势。','注意身体哪里有感觉——胸口、喉咙还是胃？把手轻轻放上去。','今天的你带着她当年没有的一切回来了。她一直在等你开口。现在，说吧。']))
  .finally(()=>{$('btn-guide').disabled=false;$('tk-guide').classList.remove('show');});
}
function renderGuide(lines){
  $('glines').innerHTML=lines.map(l=>`<div class="gline">${l}</div>`).join('');
  $('rw-sec').style.display='none';
  nav('s-guide','t-time');
  const els=[...document.querySelectorAll('.gline')];
  els.forEach((el,i)=>{setTimeout(()=>{
    els.forEach(e=>e.classList.remove('now'));
    el.classList.add('vis','now');
    if(i===els.length-1)setTimeout(()=>{$('rw-sec').style.display='block';},2200);
  },i*3200+600);});
}
let tmFrames=null;
function doRelease(){
  const rw=$('tm-rw').value.trim();
  if(!rw){toast('再短都可以，说一句');$('tm-rw').focus();return;}
  $('btn-release').disabled=true;$('tk-release').classList.add('show');
  callAI(`你是Weaver.AI时光机级联重构模块。用户完成回溯并对过去的自己说了话。从那个历史时间戳重跑因果，生成三帧。输出严格JSON无markdown：
{"frames":[{"label":"过去·已改写","caption":"那个时刻被新话语重新照亮的画面32字内","mood":0到10,"energy":0到10,"weather":"rain|cloud|sun|stars|sunset","emoji":"emoji"},{"label":"现在·级联修正","caption":"今天身体与生活的具体变化32字内",...},{"label":"未来标签","caption":"指定时间后的画面32字内",...}],"release_line":"释放确认：承认她的勇气+一个具体级联数据，48字内"}`,
    `时刻：${$('tm-when').value}。场景：${$('tm-scene').value}。残留情绪${$('tm-e-range').value}/100。她说：「${rw}」。未来帧推演到${HZ[thIdx]}。`,900)
  .then(r=>renderTBoard(r))
  .catch(()=>renderTBoard({frames:[
    {label:'过去 · 已改写',caption:'同样的房间，但这次有人站在小小的你身边，手放在你肩上。你不再一个人扛。',mood:7,energy:6,weather:'sunset',emoji:'🕯️'},
    {label:'现在 · 级联修正',caption:'胸口常年发紧的那块松了一格。今晚呼吸更深，肩膀第一次落在枕头上。',mood:8,energy:7,weather:'stars',emoji:'🌙'},
    {label:HZ[thIdx],caption:'旧场景再被提起时只是经历，不再是开关。你的注意力终于全属于现在。',mood:9,energy:9,weather:'sun',emoji:'🌿'}],
    release_line:'你刚才做的事需要很大勇气。系统检测：该节点情绪负载下降约60%，综合胜率 +5.2%。'}))
  .finally(()=>{$('btn-release').disabled=false;$('tk-release').classList.remove('show');});
}
function renderTBoard(r){
  tmFrames=r.frames||[];stats.r++;bumpStats();
  const before={...tmFrames[0],mood:2,energy:2,weather:'rain',emoji:''};
  $('tsvg-before').innerHTML=sceneSVG(before,280);
  $('tsvg-after').innerHTML=sceneSVG(tmFrames[0],280);
  $('tcap-0').textContent=(tmFrames[0].label||'过去')+'：'+tmFrames[0].caption+'（上下拖隔板对比改写前后）';
  $('tm-vd').textContent=r.release_line||'';
  segTo(0);setTWipe(38);
  nav('s-tboard','t-time');
  toast('✓ 时间线已重织');
}
function segTo(i){
  [0,1,2].forEach(x=>$('seg-'+x).classList.toggle('on',x===i));
  if(i===0){$('tm-past-wipe').style.display='block';$('tm-single').style.display='none';}
  else{
    $('tm-past-wipe').style.display='none';$('tm-single').style.display='block';
    const f=tmFrames?.[i];if(!f)return;
    const svg=$('tsvg-single');svg.style.opacity='0';
    setTimeout(()=>{svg.innerHTML=sceneSVG(f,230);svg.style.opacity='1';},200);
    $('tcap-s').textContent=(f.label||'')+'：'+f.caption;
  }
}
setWipe=makeWipe('wipe','wl-top','wdiv','whandle');
setTWipe=makeWipe('twipe','twl-top','twdiv','twhandle');

function tickClock() {
  const el = document.getElementById("clock");
  if (!el) return;
  const now = new Date();
  el.textContent = now.toLocaleTimeString("zh-CN", {
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  });
}

async function initNative() {
  if (!Capacitor.isNativePlatform()) return;
  document.body.classList.add("is-native");
  try {
    await StatusBar.setStyle({ style: Style.Light });
    await StatusBar.setBackgroundColor({ color: "#F6FAFF" });
    await SplashScreen.hide();
  } catch {
    /* optional */
  }
}

tickClock();
setInterval(tickClock, 30_000);
void initNative();
