#!/usr/bin/env python3
"""PHASE 0 — wins count toward MVP.

Base value already scales by 0.72 + 0.55*winPct (a 13-3 club is worth ~17% more
than a .500 one). Nick wants team success to matter more in the AWARD without
distorting the production numbers everything else reads.

Two edits:
 1. wv() attaches the club's win pct to each candidate entry.
 2. __HFL_MVPPICK multiplies by (1 + MVPWIN*(pct-0.5)) on top of the position
    weight — MVP only. OPOY/DPOY/All-HFL untouched.
"""
import sys, io
SRC='hfl-v6.html'; OUT='hfl-v7.html'
html=io.open(SRC,encoding='utf-8').read()
def sub(old,new,label):
    n=html.count(old)
    if n!=1: sys.exit(f'ANCHOR {label}: expected 1, found {n}')
    return html.replace(old,new,1)

# 1. expose win pct on each candidate
html=sub("value:Sv(t)*(.72+.55*(i.get(t.teamId)??.5)),line:Cv(e,t)",
         "value:Sv(t)*(.72+.55*(i.get(t.teamId)??.5)),pct:(i.get(t.teamId)??.5),line:Cv(e,t)",
         'wv pct')

# 2. win term in the MVP pick
html=sub("""G.__HFL_MVPPICK = function(list){
  if(!list || !list.length) return null;
  var best=null, bestV=-1e9;
  for(var i=0;i<list.length;i++){
    var e=list[i];
    var w=G.__HFL_MVPW[e.pos];
    if(w==null) w=1.0;
    var v=e.value*w;
    if(v>bestV){ bestV=v; best=e; }
  }
  return best;
};""",
"""G.__HFL_MVPWIN = 1.15;   // extra weight on team success, MVP only
G.__HFL_MVPW.RB = G.__HFL_MVPW.FB = 1.312; G.__HFL_MVPW.WR = 1.353;
G.__HFL_MVPW.TE = 1.474;
G.__HFL_MVPPICK = function(list){
  if(!list || !list.length) return null;
  var best=null, bestV=-1e9;
  for(var i=0;i<list.length;i++){
    var e=list[i];
    var w=G.__HFL_MVPW[e.pos];
    if(w==null) w=1.0;
    var pct=(typeof e.pct==='number')?e.pct:0.5;
    var v=e.value*w*(1+G.__HFL_MVPWIN*(pct-0.5));
    if(v>bestV){ bestV=v; best=e; }
  }
  return best;
};""", 'mvp win term')

io.open(OUT,'w',encoding='utf-8').write(html)
print(f'wrote {OUT} ({len(html)} chars)')
