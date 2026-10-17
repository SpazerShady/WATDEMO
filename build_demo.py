#!/usr/bin/env python3
"""Build the standalone WAT-Monk interactive design prototype."""

from __future__ import annotations

import base64
import io
import json
import re
import unicodedata
from pathlib import Path

from PIL import Image


ROOT = Path("/workspace")
PAGE_MAP = ROOT / "attachments/eac841ff-bc4d-4a17-9f4b-a8d0b6e732d8/WAT-Monk Page Map.html"
DESIGNS = ROOT / "design_refs"
OUTPUT = ROOT / "WATDEMO/WAT_MONK_DEMO.html"


def normalize(value: str) -> str:
    value = unicodedata.normalize("NFKC", value).lower()
    value = value.replace(".png", "")
    value = re.sub(r"[·/<>“”\"'().:–—→+]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def read_map() -> dict:
    text = PAGE_MAP.read_text(encoding="utf-8")
    match = re.search(r"const D=(\{.*?\});\s*\n", text, re.S)
    if not match:
        raise RuntimeError("Could not find page-map data")
    return json.loads(match.group(1))


def find_images() -> tuple[dict[str, Path], dict[str, Path]]:
    exact: dict[str, Path] = {}
    normalized: dict[str, Path] = {}
    # UX is the complete fallback; UI replaces it where polished work exists.
    for folder in ("Ux_1", "Ux_2", "Ux_3", "UI_1", "UI_2"):
        for path in sorted((DESIGNS / folder).glob("*.png")):
            exact[path.stem] = path
            normalized[normalize(path.stem)] = path
    return exact, normalized


def image_for(title: str, exact: dict[str, Path], normalized: dict[str, Path]) -> Path | None:
    if title in exact:
        return exact[title]
    return normalized.get(normalize(title))


def encode_screen(path: Path) -> tuple[str, int, int]:
    with Image.open(path) as original:
        image = original.convert("RGB")
        buffer = io.BytesIO()
        image.save(buffer, "WEBP", quality=76, method=5, optimize=True)
        return base64.b64encode(buffer.getvalue()).decode("ascii"), image.width, image.height


def build() -> None:
    page_map = read_map()
    exact, normalized = find_images()
    rows = []
    missing = []
    for index, row in enumerate(page_map["rows"], 1):
        path = image_for(row["title"], exact, normalized)
        if not path:
            missing.append(row["title"])
            continue
        encoded, width, height = encode_screen(path)
        rows.append(
            {
                "id": row["f"],
                "code": row["code"],
                "title": row["title"],
                "group": row["g"],
                "sub": row.get("sub", ""),
                "out": row.get("out", []),
                "incoming": row.get("in", []),
                "image": f"data:image/webp;base64,{encoded}",
                "width": width,
                "height": height,
                "source": "UI" if path.parent.name.startswith("UI_") else "UX",
            }
        )
        if index % 25 == 0:
            print(f"Encoded {index}/{len(page_map['rows'])} screens", flush=True)

    if missing:
        raise RuntimeError("Missing screens: " + ", ".join(missing))

    payload = json.dumps(rows, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    html = TEMPLATE.replace("__SCREEN_DATA__", payload).replace("__SCREEN_COUNT__", str(len(rows)))
    OUTPUT.write_text(html, encoding="utf-8")
    print(f"Built {OUTPUT} ({OUTPUT.stat().st_size / 1024 / 1024:.1f} MiB)")


TEMPLATE = r'''<!doctype html>
<html lang="th">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="theme-color" content="#221c17">
<title>WAT-Monk · Interactive Demo</title>
<style>
:root{--ink:#2b211a;--muted:#796d63;--paper:#fffdf9;--cream:#fbf2e4;--line:#e6d8c7;--gold:#ba7625;--gold2:#e4972a;--dark:#211d19;--success:#2c7253;--shadow:0 18px 60px rgba(70,42,17,.14);--sidebar:330px;--inspect:320px}
*{box-sizing:border-box}html,body{margin:0;min-height:100%;font-family:"Noto Sans Thai","Leelawadee UI",Tahoma,Arial,sans-serif;color:var(--ink);background:#eee8df}button,input{font:inherit}button{cursor:pointer}.app{height:100vh;display:grid;grid-template-columns:var(--sidebar) minmax(360px,1fr) var(--inspect);overflow:hidden}.side,.inspect{background:rgba(255,253,249,.96);backdrop-filter:blur(18px);position:relative;z-index:3}.side{border-right:1px solid var(--line);display:flex;flex-direction:column}.inspect{border-left:1px solid var(--line);display:flex;flex-direction:column}.brand{display:flex;align-items:center;gap:12px;padding:22px 22px 16px}.brand-mark{width:48px;height:48px;border-radius:16px;background:linear-gradient(145deg,#fff,#f7e8d4);box-shadow:0 7px 20px rgba(126,75,22,.12);display:grid;place-items:center;flex:none}.brand-mark svg{width:30px}.brand h1{font-size:22px;line-height:1;margin:0;color:#8d571c}.brand p{font-size:12px;color:var(--muted);margin:6px 0 0}.search{margin:0 18px 12px;position:relative}.search svg{position:absolute;left:13px;top:12px;width:18px;color:#8f8277}.search input{width:100%;height:42px;border:1px solid var(--line);border-radius:13px;background:#fff;padding:0 12px 0 40px;outline:0;color:var(--ink)}.search input:focus{border-color:var(--gold);box-shadow:0 0 0 3px rgba(186,118,37,.12)}.quick{display:flex;gap:7px;overflow:auto;padding:0 18px 14px;scrollbar-width:none}.quick button,.chip{border:1px solid var(--line);background:#fff;color:#675b51;border-radius:999px;padding:7px 11px;white-space:nowrap;font-size:12px}.quick button.active,.quick button:hover{background:var(--gold);border-color:var(--gold);color:#fff}.screen-list{overflow:auto;padding:0 10px 30px}.group{border-top:1px solid #eee4d8}.group>button{width:100%;padding:13px 10px;border:0;background:transparent;text-align:left;display:flex;align-items:center;gap:8px;color:#5e5148;font-size:13px;font-weight:700}.group>button span:first-child{flex:1}.count{font-size:10px;color:#9b8e81;background:#f3ece3;padding:3px 7px;border-radius:9px}.group-items{display:none;padding:0 4px 10px}.group.open .group-items{display:block}.screen-btn{width:100%;display:grid;grid-template-columns:47px 1fr;gap:8px;border:0;background:transparent;text-align:left;padding:9px;border-radius:10px;color:#64584f}.screen-btn:hover{background:#f8efe3}.screen-btn.active{background:#f5e3c9;color:#754714}.screen-code{font-size:10px;font-weight:800;color:#ae702c}.screen-name{font-size:12px;line-height:1.4;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.stage{min-width:0;display:flex;flex-direction:column;position:relative;background:radial-gradient(circle at 50% 12%,#faf5ec 0,#eee7dd 50%,#e8e0d5 100%)}.topbar{height:72px;display:flex;align-items:center;gap:12px;padding:0 24px;background:rgba(255,253,249,.72);border-bottom:1px solid rgba(220,204,184,.8);backdrop-filter:blur(15px);z-index:2}.mobile-menu{display:none}.titlebox{min-width:0;flex:1}.eyebrow{font-size:11px;color:#a16a2d;font-weight:800;text-transform:uppercase;letter-spacing:.08em}.current-title{font-weight:700;font-size:15px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.top-actions{display:flex;gap:8px}.icon-btn{width:38px;height:38px;border-radius:12px;border:1px solid var(--line);background:#fff;display:grid;place-items:center;color:#6b5e53}.icon-btn:hover{border-color:var(--gold);color:var(--gold)}.icon-btn svg{width:19px}.viewport{flex:1;min-height:0;overflow:auto;display:flex;justify-content:center;align-items:flex-start;padding:28px 30px 90px;scroll-behavior:smooth}.phone{width:min(390px,100%);background:#fff;border-radius:38px;box-shadow:0 25px 80px rgba(55,34,15,.22),0 0 0 10px #24211e,0 0 0 11px rgba(255,255,255,.28);overflow:hidden;position:relative;flex:none}.phone::before{content:"";position:absolute;z-index:2;top:8px;left:50%;transform:translateX(-50%);width:88px;height:22px;border-radius:16px;background:#24211e;opacity:.96}.screen-image{display:block;width:100%;height:auto;background:#fff;transition:opacity .16s ease}.screen-image.loading{opacity:.35}.phone-hint{position:fixed;bottom:22px;left:calc(var(--sidebar) + (100vw - var(--sidebar) - var(--inspect))/2);transform:translateX(-50%);z-index:2;background:rgba(34,29,24,.9);color:#fff;border-radius:999px;padding:10px 16px;font-size:12px;box-shadow:0 10px 30px rgba(0,0,0,.22);display:flex;gap:10px;align-items:center}.phone-hint button{border:0;background:var(--gold2);color:#fff;padding:5px 10px;border-radius:999px}.inspect-head{padding:23px 20px 15px;border-bottom:1px solid var(--line)}.inspect-head .status{display:flex;align-items:center;gap:7px;font-size:11px;color:var(--success);font-weight:800;margin-bottom:8px}.dot{width:7px;height:7px;border-radius:50%;background:#3b966d;box-shadow:0 0 0 4px rgba(59,150,109,.12)}.inspect-head h2{font-size:18px;margin:0 0 6px;line-height:1.35}.meta{font-size:12px;color:var(--muted);display:flex;gap:6px;flex-wrap:wrap}.inspect-body{overflow:auto;padding:18px 18px 40px}.section-label{font-size:11px;text-transform:uppercase;letter-spacing:.09em;color:#9a897a;font-weight:800;margin:0 0 10px}.actions{display:grid;gap:8px;margin-bottom:22px}.action{border:1px solid var(--line);background:#fff;text-align:left;border-radius:13px;padding:11px 12px;color:#54483f;display:grid;grid-template-columns:1fr auto;align-items:center;gap:8px;line-height:1.35;font-size:12px}.action:hover{border-color:var(--gold);background:#fff9f1;color:#8a541a}.action b{font-size:10px;color:#b47731}.empty{padding:14px;border:1px dashed #dac7b1;border-radius:13px;color:#8c7e72;font-size:12px;line-height:1.5}.flow-grid{display:grid;gap:8px;margin-bottom:22px}.flow{border:0;border-radius:13px;background:#f7eee3;padding:11px;text-align:left;color:#68584a}.flow:hover{background:#efdbc0}.flow strong{font-size:12px;display:block}.flow span{font-size:10px;color:#8c7968}.progress{height:5px;background:#eee4d8;border-radius:99px;overflow:hidden;margin-top:8px}.progress i{display:block;height:100%;width:0;background:linear-gradient(90deg,var(--gold),#e9a542);border-radius:inherit}.help{font-size:11px;line-height:1.55;color:#8a7c70;padding:12px;background:#faf5ee;border-radius:12px}.mobile-actions{display:none}.toast{position:fixed;z-index:20;left:50%;bottom:26px;transform:translate(-50%,20px);background:#211d19;color:#fff;padding:10px 14px;border-radius:11px;font-size:12px;opacity:0;pointer-events:none;transition:.2s}.toast.show{opacity:1;transform:translate(-50%,0)}
@media(max-width:1100px){:root{--inspect:285px;--sidebar:280px}.brand{padding-left:16px;padding-right:16px}.brand-mark{width:42px;height:42px}.brand h1{font-size:19px}.search,.quick{margin-left:12px;margin-right:12px}.quick{padding-left:12px}}
@media(max-width:860px){.app{display:block}.side{position:fixed;inset:0 auto 0 0;width:min(88vw,360px);transform:translateX(-105%);transition:.25s;box-shadow:20px 0 60px rgba(0,0,0,.18)}.side.open{transform:none}.inspect{display:none}.stage{height:100vh}.mobile-menu{display:grid}.topbar{height:62px;padding:0 12px}.viewport{padding:22px 16px 110px}.phone{width:min(390px,100%);border-radius:32px;box-shadow:0 18px 50px rgba(55,34,15,.18),0 0 0 6px #24211e}.phone-hint{display:none}.mobile-actions{position:fixed;display:flex;z-index:4;bottom:0;left:0;right:0;background:rgba(255,253,249,.95);border-top:1px solid var(--line);padding:10px max(12px,env(safe-area-inset-right)) calc(10px + env(safe-area-inset-bottom)) max(12px,env(safe-area-inset-left));gap:8px;overflow:auto;backdrop-filter:blur(15px)}.mobile-actions button{border:1px solid var(--line);background:#fff;color:#6b5848;border-radius:999px;padding:9px 13px;white-space:nowrap;font-size:12px}.mobile-actions button.primary{background:var(--gold);border-color:var(--gold);color:#fff}.screen-image{min-height:400px}.toast{bottom:76px}}
@media(max-width:430px){.viewport{padding-left:7px;padding-right:7px}.phone{border-radius:25px}.current-title{font-size:13px}.eyebrow{font-size:10px}.top-actions .icon-btn:last-child{display:none}}
</style>
</head>
<body>
<div class="app">
  <aside class="side" id="side">
    <div class="brand">
      <div class="brand-mark"><svg viewBox="0 0 48 48" aria-hidden="true"><path fill="#e59a2b" d="M24 4l4 12h-8z"/><path fill="#c65d2b" d="M8 22l16-10 16 10z"/><path fill="#a96725" d="M13 24h22v17H13z"/><path fill="#fff3df" d="M21 30h6v11h-6z"/></svg></div>
      <div><h1>WAT-Monk</h1><p>Interactive design prototype</p></div>
    </div>
    <label class="search"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="7"/><path d="m20 20-4-4"/></svg><input id="search" type="search" placeholder="ค้นหาหน้าจอ รหัส หรือคำสำคัญ"></label>
    <div class="quick" id="quick"></div>
    <div class="screen-list" id="screenList"></div>
  </aside>
  <main class="stage">
    <header class="topbar">
      <button class="icon-btn mobile-menu" id="menuBtn" aria-label="เปิดรายการหน้าจอ"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 6h16M4 12h16M4 18h16"/></svg></button>
      <div class="titlebox"><div class="eyebrow" id="groupTitle">WAT-MONK</div><div class="current-title" id="currentTitle"></div></div>
      <div class="top-actions">
        <button class="icon-btn" id="backBtn" title="ย้อนกลับ"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="m15 18-6-6 6-6"/></svg></button>
        <button class="icon-btn" id="nextBtn" title="หน้าถัดไป"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="m9 18 6-6-6-6"/></svg></button>
        <button class="icon-btn" id="copyBtn" title="คัดลอกลิงก์หน้าจอ"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="8" y="8" width="11" height="11" rx="2"/><path d="M16 8V5a2 2 0 0 0-2-2H5a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h3"/></svg></button>
      </div>
    </header>
    <div class="viewport" id="viewport"><div class="phone"><img id="screenImage" class="screen-image" alt=""></div></div>
    <div class="phone-hint"><span>เลือกการทำงานด้านขวา หรือ</span><button id="primaryNext">ไปขั้นถัดไป</button></div>
    <div class="mobile-actions" id="mobileActions"></div>
  </main>
  <aside class="inspect">
    <div class="inspect-head">
      <div class="status"><span class="dot"></span><span>__SCREEN_COUNT__ SCREENS READY</span></div>
      <h2 id="inspectTitle"></h2>
      <div class="meta"><span class="chip" id="codeChip"></span><span class="chip" id="sourceChip"></span></div>
    </div>
    <div class="inspect-body">
      <p class="section-label">ทางไปจากหน้านี้</p><div class="actions" id="actions"></div>
      <p class="section-label">ตัวอย่างเส้นทางหลัก</p><div class="flow-grid" id="flows"></div>
      <p class="section-label">วิธีใช้งาน</p><div class="help">เลือกหน้าจอจากรายการทางซ้าย หรือกดการทำงานด้านบน ใช้ปุ่มลูกศรซ้าย–ขวาบนคีย์บอร์ดเพื่อย้อนกลับและไปต่อ ทุกหน้าจอมาจากไฟล์ออกแบบ WAT-Monk โดยตรง</div>
    </div>
  </aside>
</div>
<div class="toast" id="toast"></div>
<script>
const screens=__SCREEN_DATA__;
const byId=new Map(screens.map(s=>[s.id,s]));
const groups=[...new Set(screens.map(s=>s.group))];
const state={current:null,history:[],filter:'ทั้งหมด',query:'',flow:null,flowStep:0};
const categories={
  'ทั้งหมด':()=>true,
  'ผู้ใช้งาน':s=>!/^(TM|DM|AD)/.test(s.id),
  'วัด':s=>/^TM|^F\d|^G\d/.test(s.id),
  'กองบุญ':s=>/^D|^DM/.test(s.id),
  'ปฏิทิน':s=>/^BC/.test(s.id),
  'ค้นหา':s=>/^GS/.test(s.id)
};
const flows=[
 {name:'จองพิธีมงคล',hint:'ผู้จอง · ตั้งแต่หน้าแรกถึงจองสำเร็จ',ids:['Main','B02-MG','S03','S04','S05-A1','S06','S07','S08','S09','S13','S14','S15']},
 {name:'จัดงานศพ',hint:'แพ็กเกจหลายวันและเพิ่มเมรุ',ids:['Main','B02-AV','F03','F04','F05','F06','F07','F08','F09','F10','F11','F12']},
 {name:'ร่วมกองบุญ',hint:'เลือกโครงการ ชำระ และติดตามผล',ids:['D01','D02','D03','D03-S','D04','D05','D06','D07','D08','D09']},
 {name:'ปฏิทินศาสนา',hint:'สำรวจกิจกรรมวันสำคัญ',ids:['BC01-OCT','BC03-UPO','BC06-CH','BC07-CH-1','BC07-CH-2','BC07-CH-3','BC08-CH','BC09-CH']},
 {name:'จัดการงานของวัด',hint:'แดชบอร์ด คิว กิจกรรม และตั้งค่า',ids:['TM00','TM01','TM02','TM04','TM05','TM06','TM07','TM09','TM10','TM11']},
 {name:'ค้นหาทั้งแอป',hint:'ค้นหา กรอง และดูรายละเอียดวัด',ids:['GS01','GS01-TYPE','GS02','GS03','GS04','GS06-T01']}
].map(f=>({...f,ids:f.ids.filter(id=>byId.has(id))}));
const $=id=>document.getElementById(id);

function shortTitle(s){return s.title.replace(/^\S+\s*/, '').replace(/^·\s*/, '')}
function groupLabel(g){return g.replace(/^\d+\s*/, '')}
function route(id,push=true){
 const screen=byId.get(id)||screens[0]; if(!screen)return;
 if(push&&state.current&&state.current.id!==screen.id)state.history.push(state.current.id);
 state.current=screen; location.hash=encodeURIComponent(screen.id);
 $('screenImage').classList.add('loading'); $('screenImage').src=screen.image; $('screenImage').alt=screen.title;
 $('screenImage').onload=()=>{$('screenImage').classList.remove('loading');$('viewport').scrollTo({top:0})};
 $('currentTitle').textContent=screen.title;$('groupTitle').textContent=groupLabel(screen.group);
 $('inspectTitle').textContent=shortTitle(screen);$('codeChip').textContent=screen.code;$('sourceChip').textContent=screen.source==='UI'?'Polished UI':'UX reference';
 renderActions(); highlightCurrent(); updateFlows(); $('side').classList.remove('open');
}
function goBack(){const id=state.history.pop();if(id)route(id,false)}
function primaryTarget(){
 if(state.flow){const f=flows[state.flow];const at=f.ids.indexOf(state.current.id);if(at>=0&&at<f.ids.length-1)return f.ids[at+1]}
 return state.current.out.find(([id])=>byId.has(id))?.[0]||nextInGroup(1);
}
function nextInGroup(direction){const list=screens.filter(s=>s.group===state.current.group);const i=list.findIndex(s=>s.id===state.current.id);return list[(i+direction+list.length)%list.length]?.id}
function renderActions(){
 const valid=state.current.out.filter(([id])=>byId.has(id));
 const html=valid.length?valid.map(([id,label])=>`<button class="action" data-go="${esc(id)}"><span>${esc(label||shortTitle(byId.get(id)))}</span><b>${esc(byId.get(id).code)} →</b></button>`).join(''):'<div class="empty">หน้านี้เป็นจุดสิ้นสุดของเส้นทาง เลือกหน้าจอหรือเส้นทางใหม่ได้จากเมนู</div>';
 $('actions').innerHTML=html;$('actions').querySelectorAll('[data-go]').forEach(b=>b.onclick=()=>route(b.dataset.go));
 const mobile=valid.slice(0,5).map(([id,label],i)=>`<button class="${i===0?'primary':''}" data-go="${esc(id)}">${esc(label||byId.get(id).code)}</button>`).join('');
 $('mobileActions').innerHTML=mobile||'<button class="primary" data-menu>เลือกหน้าจออื่น</button>';
 $('mobileActions').querySelectorAll('[data-go]').forEach(b=>b.onclick=()=>route(b.dataset.go));
 $('mobileActions').querySelector('[data-menu]')?.addEventListener('click',()=> $('side').classList.add('open'));
}
function renderList(){
 const query=state.query.trim().toLowerCase();const predicate=categories[state.filter]||categories['ทั้งหมด'];
 const visible=screens.filter(s=>predicate(s)&&(!query||`${s.id} ${s.code} ${s.title} ${s.group}`.toLowerCase().includes(query)));
 $('screenList').innerHTML=groups.map(g=>{const list=visible.filter(s=>s.group===g);if(!list.length)return'';const open=query||list.some(s=>s.id===state.current?.id);return `<section class="group ${open?'open':''}" data-group="${esc(g)}"><button><span>${esc(groupLabel(g))}</span><span class="count">${list.length}</span></button><div class="group-items">${list.map(s=>`<button class="screen-btn ${s.id===state.current?.id?'active':''}" data-go="${esc(s.id)}"><span class="screen-code">${esc(s.code)}</span><span class="screen-name">${esc(shortTitle(s))}</span></button>`).join('')}</div></section>`}).join('');
 $('screenList').querySelectorAll('.group>button').forEach(b=>b.onclick=()=>b.parentElement.classList.toggle('open'));
 $('screenList').querySelectorAll('[data-go]').forEach(b=>b.onclick=()=>route(b.dataset.go));
}
function highlightCurrent(){renderList()}
function renderQuick(){
 $('quick').innerHTML=Object.keys(categories).map(c=>`<button class="${state.filter===c?'active':''}" data-filter="${c}">${c}</button>`).join('');
 $('quick').querySelectorAll('button').forEach(b=>b.onclick=()=>{state.filter=b.dataset.filter;renderQuick();renderList()});
}
function renderFlows(){
 $('flows').innerHTML=flows.map((f,i)=>`<button class="flow" data-flow="${i}"><strong>${esc(f.name)}</strong><span>${esc(f.hint)} · ${f.ids.length} หน้า</span><div class="progress"><i id="flowbar${i}"></i></div></button>`).join('');
 $('flows').querySelectorAll('[data-flow]').forEach(b=>b.onclick=()=>{state.flow=Number(b.dataset.flow);route(flows[state.flow].ids[0]);updateFlows()});
 updateFlows();
}
function updateFlows(){flows.forEach((f,i)=>{const bar=$(`flowbar${i}`);if(!bar)return;const at=f.ids.indexOf(state.current?.id);bar.style.width=at<0?'0%':`${((at+1)/f.ids.length)*100}%`})}
function esc(v){return String(v).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}
function toast(message){$('toast').textContent=message;$('toast').classList.add('show');setTimeout(()=>$('toast').classList.remove('show'),1600)}
$('search').addEventListener('input',e=>{state.query=e.target.value;renderList()});
$('menuBtn').onclick=()=>$('side').classList.toggle('open');
$('backBtn').onclick=goBack;
$('nextBtn').onclick=()=>route(primaryTarget()||nextInGroup(1));
$('primaryNext').onclick=()=>route(primaryTarget()||nextInGroup(1));
$('copyBtn').onclick=async()=>{try{await navigator.clipboard.writeText(location.href);toast('คัดลอกลิงก์หน้าจอแล้ว')}catch{toast('เปิดลิงก์ #'+state.current.id)}};
document.addEventListener('keydown',e=>{if(e.target.matches('input'))return;if(e.key==='ArrowLeft')goBack();if(e.key==='ArrowRight')route(primaryTarget()||nextInGroup(1));if(e.key==='/'){e.preventDefault();$('search').focus()}});
window.addEventListener('hashchange',()=>{const id=decodeURIComponent(location.hash.slice(1));if(id&&id!==state.current?.id&&byId.has(id))route(id,false)});
renderQuick();renderFlows();route(byId.has(decodeURIComponent(location.hash.slice(1)))?decodeURIComponent(location.hash.slice(1)):'Main',false);
</script>
</body>
</html>'''


if __name__ == "__main__":
    build()
