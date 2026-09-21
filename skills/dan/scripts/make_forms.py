#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
make_forms.py — Form interaktif Monitoring / Controlling / Progress (sub-skill DAN #07).

Menghasilkan SATU file HTML self-contained (tanpa internet/CDN) berisi 3 form:
  1. FORM PROGRESS    — update progres tugas (% aktual, effort, blocker, status)
  2. FORM MONITORING  — catatan tinjauan berkala (RAG, KPI, risiko, budget, ringkasan)
  3. FORM CONTROLLING — tindakan korektif/preventif saat variance melewati ambang

Cara pakai form:
  - muat projects.json lewat tombol "Muat projects.json" (atau contoh bawaan),
  - isi form → "Tambah ke batch" → kumpulkan beberapa record,
  - salin/unduh batch sebagai JSON, lalu jalankan:
        python3 project_monitor.py apply projects.json batch.json

PAKAI:
  python3 make_forms.py --projects ../templates/projects.example.json \
      --out ../../../deliverables/forms.html
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any, Dict, Optional, Sequence

HERE = os.path.dirname(os.path.abspath(__file__))

HTML = r"""<!doctype html><html lang="id"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>DAN · Form Monitoring / Controlling / Progress</title>
<style>
:root{--bg:#0F172A;--card:#16233F;--panel:#111C33;--text:#F1F5F9;--muted:#94A3B8;
--grid:#24344F;--accent:#38BDF8;--good:#34D399;--warn:#FBBF24;--bad:#FB7185;}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--text);font-family:-apple-system,
BlinkMacSystemFont,'Segoe UI',Roboto,'Helvetica Neue',Arial,'Noto Sans',sans-serif;padding:24px}
.wrap{max-width:1180px;margin:0 auto}
h1{font-size:26px;margin:0 0 4px;letter-spacing:-.6px}
.sub{color:var(--muted);font-size:13px;margin:0 0 18px;line-height:1.5}
.bar{display:flex;flex-wrap:wrap;gap:10px;align-items:center;margin-bottom:16px}
button{background:var(--card);color:var(--text);border:1px solid var(--grid);border-radius:10px;
padding:9px 14px;font-size:12.5px;cursor:pointer;font-weight:600}
button.primary{background:var(--accent);color:#06283c;border-color:var(--accent)}
button:hover{filter:brightness(1.12)}
.tabs{display:flex;gap:6px;margin-bottom:14px;flex-wrap:wrap}
.tab{padding:9px 16px;border-radius:999px;border:1px solid var(--grid);background:var(--panel);
color:var(--muted);font-size:12.5px;cursor:pointer;font-weight:700}
.tab.on{background:var(--accent);color:#06283c;border-color:var(--accent)}
.card{background:var(--card);border:1px solid var(--grid);border-radius:16px;padding:18px;margin-bottom:16px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:12px}
label{display:block;font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:.6px;
margin:0 0 5px}
input,select,textarea{width:100%;background:var(--panel);border:1px solid var(--grid);color:var(--text);
border-radius:10px;padding:9px 11px;font-size:13px;font-family:inherit}
textarea{min-height:64px;resize:vertical}
input[type=range]{padding:0;height:26px}
.row{display:flex;gap:8px;align-items:center}
.preview{margin-top:14px;padding:12px 14px;border-radius:12px;background:var(--panel);
border:1px dashed var(--grid);font-size:13px;line-height:1.6}
.rag{display:inline-block;padding:2px 10px;border-radius:999px;font-size:11px;font-weight:800;
letter-spacing:.6px}
.rag.good{background:rgba(52,211,153,.16);color:var(--good)}
.rag.warn{background:rgba(251,191,36,.16);color:var(--warn)}
.rag.bad{background:rgba(251,113,133,.16);color:var(--bad)}
table{width:100%;border-collapse:collapse;font-size:12px;margin-top:8px}
th,td{text-align:left;padding:7px 8px;border-bottom:1px solid var(--grid);vertical-align:top}
th{color:var(--muted);font-size:10.5px;text-transform:uppercase;letter-spacing:.6px}
pre{background:var(--panel);border:1px solid var(--grid);border-radius:12px;padding:12px;
font-size:11.5px;overflow:auto;max-height:260px;color:#CFE8FF}
.hint{font-size:11.5px;color:var(--muted);line-height:1.6;margin-top:8px}
.dyn{border:1px solid var(--grid);border-radius:12px;padding:10px;margin-top:8px}
.kv{display:grid;grid-template-columns:1.4fr 1fr 1fr;gap:8px;margin-bottom:8px}
@media(max-width:760px){.kv{grid-template-columns:1fr}}
</style></head><body><div class="wrap">
<h1>DAN · Form Monitoring / Controlling / Progress</h1>
<p class="sub">Isi form di bawah, kumpulkan ke <b>batch</b>, lalu terapkan dengan
<code>python3 project_monitor.py apply projects.json batch.json</code>.
Semua berjalan offline di browser Anda; tidak ada data yang dikirim ke mana pun.</p>

<div class="bar">
  <input type="file" id="file" accept=".json,application/json" style="display:none">
  <button class="primary" onclick="document.getElementById('file').click()">Muat projects.json</button>
  <button onclick="loadSample()">Muat contoh bawaan</button>
  <button onclick="showPaste()">Tempel JSON</button>
  <span class="hint" id="loadState" style="margin:0"></span>
</div>
<textarea id="paste" style="display:none" placeholder='{"projects":[...]}'></textarea>

<div class="tabs">
  <div class="tab on" data-t="progress" onclick="tab('progress')">1 · Form Progress</div>
  <div class="tab" data-t="monitoring" onclick="tab('monitoring')">2 · Form Monitoring</div>
  <div class="tab" data-t="controlling" onclick="tab('controlling')">3 · Form Controlling</div>
  <div class="tab" data-t="batch" onclick="tab('batch')">Batch (<span id="bn">0</span>)</div>
</div>

<!-- ============================ FORM PROGRESS ============================ -->
<div class="card" id="p-progress">
  <div class="grid">
    <div><label>Proyek</label><select id="p_project" onchange="fillTasks()"></select></div>
    <div><label>Tugas</label><select id="p_task" onchange="preview()"></select></div>
    <div><label>Tanggal update</label><input type="date" id="p_date"></div>
    <div><label>Owner</label><input id="p_owner" placeholder="otomatis dari tugas"></div>
  </div>
  <div class="grid" style="margin-top:12px">
    <div><label>Progres aktual (%) — <span id="p_pv">0</span>%</label>
      <input type="range" id="p_prog" min="0" max="100" step="5" value="0"
             oninput="document.getElementById('p_progn').value=this.value;preview()">
      <input type="number" id="p_progn" min="0" max="100" value="0" style="margin-top:6px"
             oninput="document.getElementById('p_prog').value=this.value;preview()"></div>
    <div><label>Effort aktual (orang-hari)</label><input type="number" id="p_effort" step="0.5"></div>
    <div><label>Status</label><select id="p_status">
      <option value="">(tetap)</option><option>on-track</option><option>blocked</option>
      <option>stalled</option><option>done</option></select></div>
  </div>
  <div style="margin-top:12px"><label>Blocker (pisahkan dengan koma)</label>
    <input id="p_blockers" placeholder="mis. menunggu aset foto, approval belum turun"></div>
  <div style="margin-top:12px"><label>Catatan / bukti kemajuan</label>
    <textarea id="p_notes" placeholder="apa yang selesai minggu ini, tautan bukti, dsb."></textarea></div>
  <div class="preview" id="p_preview">Muat projects.json untuk melihat rencana vs aktual.</div>
  <div style="margin-top:12px"><button class="primary" onclick="addProgress()">Tambah ke batch</button></div>
</div>

<!-- ============================ FORM MONITORING ============================ -->
<div class="card" id="p-monitoring" style="display:none">
  <div class="grid">
    <div><label>Proyek</label><select id="m_project"></select></div>
    <div><label>Tanggal tinjauan</label><input type="date" id="m_date"></div>
    <div><label>Status RAG pekan ini</label><select id="m_rag">
      <option value="green">Green / on-track</option><option value="yellow">Yellow / waspada</option>
      <option value="red">Red / kritis</option></select></div>
    <div><label>Biaya aktual kumulatif</label><input type="number" id="m_budget" step="1000000"></div>
  </div>
  <div class="dyn"><label>KPI (nama · target · aktual)</label><div id="m_kpis"></div>
    <button onclick="addKpi()">+ Tambah KPI</button></div>
  <div class="dyn"><label>Risiko (deskripsi · prob 1-5 · dampak 1-5 · mitigasi · owner)</label>
    <div id="m_risks"></div><button onclick="addRisk()">+ Tambah risiko</button></div>
  <div style="margin-top:12px"><label>Ringkasan tinjauan (3 kalimat)</label>
    <textarea id="m_summary" placeholder="apa yang berjalan, apa yang tersendat, keputusan pekan ini"></textarea></div>
  <div style="margin-top:12px"><button class="primary" onclick="addMonitoring()">Tambah ke batch</button></div>
</div>

<!-- ============================ FORM CONTROLLING ============================ -->
<div class="card" id="p-controlling" style="display:none">
  <div class="grid">
    <div><label>Proyek</label><select id="c_project"></select></div>
    <div><label>Tanggal</label><input type="date" id="c_date"></div>
    <div><label>Owner tindakan</label><input id="c_owner"></div>
    <div><label>Tenggat tindakan</label><input type="date" id="c_due"></div>
  </div>
  <div style="margin-top:12px"><label>Masalah / penyimpangan</label>
    <input id="c_issue" placeholder="mis. progres landing page 40% dari rencana 75%"></div>
  <div class="grid" style="margin-top:12px">
    <div><label>Metrik variance</label><select id="c_metric">
      <option>progress</option><option>budget</option><option>scope</option>
      <option>schedule</option><option>quality</option></select></div>
    <div><label>Rencana</label><input type="number" id="c_plan"></div>
    <div><label>Aktual</label><input type="number" id="c_act"></div>
  </div>
  <div style="margin-top:12px"><label>Akar masalah (bukan gejala)</label>
    <textarea id="c_root" placeholder="kenapa ini terjadi? gali sampai penyebab yang bisa ditindak"></textarea></div>
  <div style="margin-top:12px"><label>Tindakan korektif (perbaiki yang sudah terjadi)</label>
    <textarea id="c_corr"></textarea></div>
  <div style="margin-top:12px"><label>Tindakan preventif (cegah terulang)</label>
    <textarea id="c_prev"></textarea></div>
  <div class="grid" style="margin-top:12px">
    <div><label>Status</label><select id="c_status"><option>open</option><option>in-progress</option>
      <option>done</option><option>cancelled</option></select></div>
  </div>
  <div style="margin-top:12px"><button class="primary" onclick="addControlling()">Tambah ke batch</button></div>
</div>

<!-- ============================ BATCH ============================ -->
<div class="card" id="p-batch" style="display:none">
  <div class="bar">
    <button class="primary" onclick="copyBatch()">Salin JSON batch</button>
    <button onclick="downloadBatch()">Unduh batch.json</button>
    <button onclick="clearBatch()">Kosongkan</button>
    <span class="hint" id="copyState" style="margin:0"></span>
  </div>
  <table><thead><tr><th>#</th><th>Form</th><th>Proyek</th><th>Inti</th><th></th></tr></thead>
    <tbody id="batchRows"></tbody></table>
  <pre id="batchJson">[]</pre>
  <p class="hint">Terapkan dengan:
  <code>python3 project_monitor.py apply projects.json batch.json</code> lalu buat ulang laporan:
  <code>python3 project_monitor.py report projects_updated.json</code></p>
</div>

<script>
var DOC=null, BATCH=[];
try{BATCH=JSON.parse(localStorage.getItem('dan_batch')||'[]');}catch(e){BATCH=[];}
var SAMPLE=__SAMPLE_JSON__;

function el(id){return document.getElementById(id);}
function today(){return new Date().toISOString().slice(0,10);}
function saveBatch(){localStorage.setItem('dan_batch',JSON.stringify(BATCH));renderBatch();}
function tab(t){
  document.querySelectorAll('.tab').forEach(function(x){x.classList.toggle('on',x.dataset.t===t);});
  ['progress','monitoring','controlling','batch'].forEach(function(k){
    el('p-'+k).style.display=(k===t)?'':'none';});
  if(t==='batch')renderBatch();
}
function projects(){return (DOC&&DOC.projects)||[];}
function fillSelects(){
  ['p_project','m_project','c_project'].forEach(function(id){
    var s=el(id);s.innerHTML='';
    projects().forEach(function(p){var o=document.createElement('option');
      o.value=p.id;o.textContent=p.id+' · '+p.name;s.appendChild(o);});});
  fillTasks();addKpi();addRisk();
}
function fillTasks(){
  var pid=el('p_project').value,s=el('p_task');s.innerHTML='';
  var p=projects().filter(function(x){return x.id===pid;})[0];
  if(!p)return;
  (p.tasks||[]).forEach(function(t){var o=document.createElement('option');
    o.value=t.id||t.name;o.textContent=(t.id?t.id+' · ':'')+t.name;s.appendChild(o);});
  preview();
}
function planned(t,now){
  if(t.planned_progress!=null)return +t.planned_progress;
  var s=new Date(t.start),e=new Date(t.end||t.start);
  if(!s||!e||e<=s)return (t.progress>=100)?100:0;
  return Math.max(0,Math.min(100,(now-s)/(e-s)*100));
}
function ragOf(plan,act,over){
  if(act>=100)return 'good';
  var v=act-plan;
  if(over>3||v<-20)return 'bad';
  if(over>0||v<-5)return 'warn';
  return 'good';
}
function preview(){
  var pid=el('p_project').value,tid=el('p_task').value;
  var p=projects().filter(function(x){return x.id===pid;})[0];if(!p)return;
  var t=(p.tasks||[]).filter(function(x){return (x.id||x.name)===tid;})[0];if(!t)return;
  el('p_owner').value=t.owner||'';
  var now=el('p_date').value?new Date(el('p_date').value):new Date();
  var plan=planned(t,now),act=+el('p_progn').value;
  var e=new Date(t.end||t.start);
  var over=(act<100&&now>e)?Math.floor((now-e)/86400000):0;
  var rag=ragOf(plan,act,over),v=act-plan;
  el('p_preview').innerHTML=
    'Rencana hari ini <b>'+plan.toFixed(0)+'%</b> · Aktual <b>'+act+'%</b> · '+
    'Variance <b>'+(v>=0?'+':'')+v.toFixed(0)+' pp</b>'+
    (over? ' · Terlambat <b>'+over+' hari</b>':'')+
    ' · <span class="rag '+rag+'">'+({good:'ON-TRACK',warn:'WASPADA',bad:'KRITIS'})[rag]+'</span>'+
    '<div class="hint">Ambang: var ≥ −5 = on-track · −20 ≤ var < −5 atau telat ≤3 hari = waspada · ' +
    'var < −20 atau telat >3 hari = kritis.</div>';
}
function rec(form,extra){
  var r={form:form,date:today()};for(var k in extra)r[k]=extra[k];return r;
}
function addProgress(){
  var bl=el('p_blockers').value.split(',').map(function(s){return s.trim();})
          .filter(function(s){return s;});
  BATCH.push(rec('progress',{project:el('p_project').value,task:el('p_task').value,
    date:el('p_date').value||today(),progress:+el('p_progn').value,
    effort_actual:el('p_effort').value?+el('p_effort').value:null,
    status:el('p_status').value||null,blockers:bl,notes:el('p_notes').value,
    owner:el('p_owner').value}));
  saveBatch();flash('Record progress masuk batch.');
}
function addMonitoring(){
  var kpis=[],risks=[];
  el('m_kpis').querySelectorAll('.kv').forEach(function(r){
    var i=r.querySelectorAll('input');
    if(i[0].value)kpis.push({name:i[0].value,target:+i[1].value||null,actual:+i[2].value||null});});
  el('m_risks').querySelectorAll('.kv').forEach(function(r){
    var i=r.querySelectorAll('input');
    if(i[0].value)risks.push({desc:i[0].value,prob:+i[1].value||1,impact:+i[2].value||1,
      mitigation:i[3].value,owner:i[4].value});});
  BATCH.push(rec('monitoring',{project:el('m_project').value,date:el('m_date').value||today(),
    rag:el('m_rag').value,budget_actual:el('m_budget').value?+el('m_budget').value:null,
    kpi:kpis,risks:risks,summary:el('m_summary').value}));
  saveBatch();flash('Record monitoring masuk batch.');
}
function addControlling(){
  BATCH.push(rec('controlling',{project:el('c_project').value,date:el('c_date').value||today(),
    issue:el('c_issue').value,variance:{metric:el('c_metric').value,
    planned:+el('c_plan').value||null,actual:+el('c_act').value||null},
    root_cause:el('c_root').value,corrective_action:el('c_corr').value,
    preventive:el('c_prev').value,owner:el('c_owner').value,due:el('c_due').value,
    status:el('c_status').value}));
  saveBatch();flash('Record controlling masuk batch.');
}
function addKpi(){
  var d=document.createElement('div');d.className='kv';
  d.innerHTML='<input placeholder="nama KPI"><input type="number" placeholder="target">'+
              '<input type="number" placeholder="aktual">';
  el('m_kpis').appendChild(d);
}
function addRisk(){
  var d=document.createElement('div');d.className='kv';
  d.style.gridTemplateColumns='2fr .6fr .6fr 2fr 1fr';
  d.innerHTML='<input placeholder="deskripsi risiko"><input type="number" min="1" max="5" value="3">'+
    '<input type="number" min="1" max="5" value="3"><input placeholder="mitigasi">'+
    '<input placeholder="owner">';
  el('m_risks').appendChild(d);
}
function renderBatch(){
  el('bn').textContent=BATCH.length;
  var tb=el('batchRows');tb.innerHTML='';
  BATCH.forEach(function(r,i){
    var core=r.form==='progress'?(r.task+' → '+r.progress+'%'):
             r.form==='monitoring'?(r.rag+' · '+(r.summary||'').slice(0,40)):
             (r.issue||'').slice(0,40);
    var tr=document.createElement('tr');
    tr.innerHTML='<td>'+(i+1)+'</td><td>'+r.form+'</td><td>'+(r.project||'')+'</td><td>'+core+
      '</td><td><button onclick="rm('+i+')">hapus</button></td>';
    tb.appendChild(tr);});
  el('batchJson').textContent=JSON.stringify(BATCH,null,2);
}
function rm(i){BATCH.splice(i,1);saveBatch();}
function clearBatch(){if(confirm('Kosongkan batch?')){BATCH=[];saveBatch();}}
function copyBatch(){
  var t=JSON.stringify(BATCH,null,2);
  if(navigator.clipboard&&navigator.clipboard.writeText){
    navigator.clipboard.writeText(t).then(function(){flash('JSON tersalin.');},
      function(){fallbackCopy(t);});
  }else fallbackCopy(t);
}
function fallbackCopy(t){
  var ta=document.createElement('textarea');ta.value=t;document.body.appendChild(ta);
  ta.select();try{document.execCommand('copy');flash('JSON tersalin.');}
  catch(e){flash('Salin manual dari kotak di bawah.');}document.body.removeChild(ta);
}
function downloadBatch(){
  var b=new Blob([JSON.stringify(BATCH,null,2)],{type:'application/json'});
  var a=document.createElement('a');a.href=URL.createObjectURL(b);
  a.download='batch.json';document.body.appendChild(a);a.click();
  document.body.removeChild(a);flash('batch.json diunduh.');
}
function flash(m){var s=el('copyState');s.textContent=m;setTimeout(function(){s.textContent='';},2600);}
function setDoc(d){DOC=d;el('loadState').textContent='Termuat: '+projects().length+' proyek · '+
  projects().reduce(function(a,p){return a+(p.tasks||[]).length;},0)+' tugas';
  fillSelects();
  ['p_date','m_date','c_date'].forEach(function(id){el(id).value=today();});
  preview();
}
function loadSample(){setDoc(SAMPLE);}
function showPaste(){var p=el('paste');p.style.display=p.style.display?'none':'block';
  p.onchange=function(){try{setDoc(JSON.parse(p.value));}catch(e){alert('JSON tidak valid: '+e);}};}
el('file').addEventListener('change',function(ev){
  var f=ev.target.files[0];if(!f)return;var r=new FileReader();
  r.onload=function(){try{setDoc(JSON.parse(r.result));}catch(e){alert('JSON tidak valid: '+e);}};
  r.readAsText(f);});
renderBatch();
</script></body></html>
"""


def main(argv: Optional[Sequence[str]] = None) -> int:
    root = os.environ.get("DAN_ROOT") or os.path.abspath(os.path.join(HERE, "..", "..", ".."))
    ap = argparse.ArgumentParser(description="DAN · Form Monitoring/Controlling/Progress")
    ap.add_argument("--projects", default=os.path.join(root, "skills", "dan", "templates",
                                                        "projects.example.json"),
                    help="projects.json untuk dijadikan contoh bawaan di dalam form")
    ap.add_argument("--out", default=os.path.join(root, "deliverables", "forms.html"))
    a = ap.parse_args(argv)

    sample: Dict[str, Any] = {"projects": []}
    if a.projects and os.path.exists(a.projects):
        with open(a.projects, encoding="utf-8") as f:
            sample = json.load(f)
    html = HTML.replace("__SAMPLE_JSON__", json.dumps(sample, ensure_ascii=False))
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with open(a.out, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"[DAN] forms -> {a.out} ({len(html) // 1024} KB, self-contained)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
