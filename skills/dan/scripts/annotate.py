#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
annotate.py — Mode kolaboratif: lapisan komentar/annotasi pada deliverable HTML.

Menyuntikkan lapisan review ringan (vanilla JS, tanpa server) ke HTML apa pun yang
dihasilkan DAN (infografik, dashboard, slide, summary):
  - tiap kartu insight/chart/KPI mendapat tombol 💬 saat mode review aktif,
  - komentar disimpan di localStorage per file + bisa diekspor/impor sebagai JSON
    (berisi reviewer + timestamp) sehingga loop review tim berjalan tanpa tool luar,
  - panel samping menampilkan semua komentar + status resolve.

PAKAI
  python3 annotate.py --src deliverables/infographic.html \
      --out deliverables/infographic_review.html
  # tim membuka berkas _review.html, menulis komentar, ekspor JSON, kirim ke penulis;
  # penulis impor JSON untuk melihat semua masukan pada berkas yang sama.
"""
from __future__ import annotations

import argparse
import os
import sys

LAYER_CSS = """
#annBar{position:fixed;left:12px;bottom:12px;z-index:99;background:#0F172A;color:#F1F5F9;
border:1px solid #24344F;border-radius:14px;padding:10px 12px;font:12px/1.4 system-ui;
display:flex;gap:8px;align-items:center;box-shadow:0 6px 24px rgba(0,0,0,.35)}
#annBar input{background:#16233F;border:1px solid #24344F;color:#F1F5F9;border-radius:8px;
padding:6px 8px;font:12px system-ui;width:120px}
#annBar button{background:#16233F;border:1px solid #24344F;color:#F1F5F9;border-radius:8px;
padding:6px 10px;font:12px system-ui;cursor:pointer}
#annBar button.on{background:#38BDF8;color:#06283c;border-color:#38BDF8}
.annBtn{position:absolute;top:6px;right:6px;z-index:5;background:#16233F;color:#F1F5F9;
border:1px solid #24344F;border-radius:8px;padding:2px 7px;font:11px system-ui;
cursor:pointer;display:none}
body.annOn .annBtn{display:block}
.annHas{outline:2px solid #FBBF24;outline-offset:2px}
#annPanel{position:fixed;right:12px;top:12px;bottom:64px;width:300px;z-index:98;
background:#0F172A;color:#F1F5F9;border:1px solid #24344F;border-radius:14px;
padding:12px;font:12px/1.5 system-ui;overflow:auto;display:none}
body.annOn #annPanel{display:block}
#annPanel .c{border:1px solid #24344F;border-radius:10px;padding:8px;margin-bottom:8px}
#annPanel .m{color:#94A3B8;font-size:10.5px}
#annPanel textarea{width:100%;background:#16233F;border:1px solid #24344F;color:#F1F5F9;
border-radius:8px;font:12px system-ui;min-height:54px}
"""

LAYER_JS = """
(function(){
 var KEY='dan-ann-'+location.pathname.split('/').pop();
 var st={on:false,reviewer:localStorage.getItem(KEY+'-rev')||'',
         comments:JSON.parse(localStorage.getItem(KEY)||'[]')};
 function save(){localStorage.setItem(KEY,JSON.stringify(st.comments));}
 var bar=document.createElement('div');bar.id='annBar';
 bar.innerHTML='<input id=annRev placeholder="nama reviewer">'+
  '<button id=annToggle>💬 Mode review</button><button id=annExport>⬇ ekspor</button>'+
  '<button id=annImport>⬆ impor</button><span id=annCount></span>';
 document.body.appendChild(bar);
 var panel=document.createElement('div');panel.id='annPanel';
 document.body.appendChild(panel);
 document.getElementById('annRev').value=st.reviewer;
 document.getElementById('annRev').onchange=function(){
   st.reviewer=this.value;localStorage.setItem(KEY+'-rev',st.reviewer);};
 var targets=[].slice.call(document.querySelectorAll('.in,.card,.kpi,section.slide'));
 targets.forEach(function(el,i){
   el.style.position='relative';
   var b=document.createElement('button');b.className='annBtn';b.textContent='💬';
   b.onclick=function(ev){ev.stopPropagation();openBox(i,el,ev);};
   el.appendChild(b);
   if(st.comments.some(function(c){return c.idx===i&&!c.resolved;}))el.classList.add('annHas');
 });
 function openBox(i,el,ev){
   var ex=st.comments.filter(function(c){return c.idx===i;});
   panel.innerHTML='<b>Komentar #'+i+'</b>'+(ex.length?(' ('+ex.length+')'):'');
   ex.forEach(function(c,j){
     var d=document.createElement('div');d.className='c';
     d.innerHTML='<div class=m>'+esc(c.reviewer)+' · '+c.ts+
       (c.resolved?' · ✅ resolved':'')+'</div><div>'+esc(c.text)+'</div>'+
       '<button data-r='+j+'>tandai resolve</button>';
     d.querySelector('button').onclick=function(){c.resolved=!c.resolved;save();render();
       openBox(i,el,ev);};
     panel.appendChild(d);
   });
   var ta=document.createElement('textarea');ta.placeholder='tulis komentar…';
   panel.appendChild(ta);
   var sb=document.createElement('button');sb.textContent='simpan';
   sb.onclick=function(){
     if(!st.reviewer){alert('isi nama reviewer dulu');return;}
     st.comments.push({idx:i,reviewer:st.reviewer,text:ta.value,
       ts:new Date().toISOString().slice(0,16),resolved:false});
     save();el.classList.add('annHas');render();openBox(i,el,ev);};
   panel.appendChild(sb);
 }
 function esc(s){return String(s).replace(/[&<>]/g,function(c){
   return {'&':'&amp;','<':'&lt;','>':'&gt;'}[c];});}
 function render(){
   var open=st.comments.filter(function(c){return !c.resolved;}).length;
   document.getElementById('annCount').textContent=
     st.comments.length?('💬 '+st.comments.length+' ('+open+' open)'):'';
 }
 document.getElementById('annToggle').onclick=function(){
   st.on=!st.on;document.body.classList.toggle('annOn',st.on);
   this.classList.toggle('on',st.on);};
 document.getElementById('annExport').onclick=function(){
   var blob=new Blob([JSON.stringify({file:KEY,reviewer:st.reviewer,
     comments:st.comments},null,2)],{type:'application/json'});
   var a=document.createElement('a');a.href=URL.createObjectURL(blob);
   a.download='review_'+KEY.replace(/[^a-z0-9]/gi,'_')+'.json';a.click();};
 document.getElementById('annImport').onclick=function(){
   var t=prompt('tempel JSON komentar:');if(!t)return;
   try{var d=JSON.parse(t);st.comments=st.comments.concat(d.comments||[]);
     save();render();alert('impor '+((d.comments||[]).length)+' komentar');}
   catch(e){alert('JSON tidak valid');}};
 render();
})();
"""


def inject(src: str, out: str) -> int:
    html = open(src, encoding="utf-8", errors="replace").read()
    if "</body>" not in html:
        print("[DAN] HTML tanpa </body>; tidak bisa menyuntik lapisan review.")
        return 2
    layer = f"<style>{LAYER_CSS}</style><script>{LAYER_JS}</script></body>"
    html = html.replace("</body>", layer, 1)
    os.makedirs(os.path.dirname(os.path.abspath(out)) or ".", exist_ok=True)
    open(out, "w", encoding="utf-8").write(html)
    print(f"[DAN] lapisan review disuntik -> {out} "
          f"(buka, aktifkan '💬 Mode review', tulis & ekspor komentar)")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="DAN · collaborative annotation layer")
    ap.add_argument("--src", required=True)
    ap.add_argument("--out", default="")
    a = ap.parse_args(argv)
    out = a.out or os.path.splitext(a.src)[0] + "_review.html"
    return inject(a.src, out)


if __name__ == "__main__":
    raise SystemExit(main())
