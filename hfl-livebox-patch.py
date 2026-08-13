#!/usr/bin/env python3
"""LIVE BOX SCORE — a running stat panel during live sim.

Sits between the coordinator buttons and the play-by-play. Two parts:
  1. A broadcast-style comparison strip: each stat is a single row with the
     away number, the label, the home number, and a split bar underneath whose
     proportion IS the stat. The bar is the signature — it reads at a glance
     while a game is running, which a table of numbers does not.
  2. Game leaders: passing, rushing and receiving for each club, one line each.

Design deliberately stays inside the app's existing system (hfl-card, hfl-label,
font-display, tabular-nums, the offense/defense accent pair) rather than
introducing a new visual language mid-app.
"""
import sys, io
SRC='hfl-v9.html'; OUT='hfl-v10.html'
html=io.open(SRC,encoding='utf-8').read()
def sub(old,new,label):
    n=html.count(old)
    if n!=1: sys.exit(f'ANCHOR {label}: expected 1, found {n}')
    return html.replace(old,new,1)

ANCHOR = ("(0,I.jsxs)(`section`,{className:`mt-4`,children:[(0,I.jsx)(`p`,"
          "{className:`hfl-label mb-2`,children:`Play-by-play`})")

BOX = r"""((()=>{
var S=t.stats||{},HS=S.home||{},AS=S.away||{};
var ttl=function(x){return (x.passYards||0)+(x.rushYards||0)-(x.sackYards||0)};
var rows=[
 [`Total yards`,ttl(AS),ttl(HS),1],
 [`Passing`,AS.passYards||0,HS.passYards||0,1],
 [`Rushing`,AS.rushYards||0,HS.rushYards||0,1],
 [`First downs`,AS.firstDowns||0,HS.firstDowns||0,1],
 [`Third down`,(AS.thirdConv||0)+`/`+(AS.thirdAtt||0),(HS.thirdConv||0)+`/`+(HS.thirdAtt||0),0],
 [`Sacks`,AS.sacks||0,HS.sacks||0,1],
 [`Turnovers`,AS.turnovers||0,HS.turnovers||0,0]
];
var side={};
(t.home.players||[]).forEach(function(p){side[p.id]=`home`});
(t.away.players||[]).forEach(function(p){side[p.id]=`away`});
var ps=Object.keys(t.playerStats||{}).map(function(id){var v=t.playerStats[id];return Object.assign({_id:id,_s:side[id]},v)});
var best=function(s,k){var f=ps.filter(function(x){return x._s===s&&(x[k]||0)>0});
 f.sort(function(a,b){return (b[k]||0)-(a[k]||0)});return f[0]};
var lead=function(s){
 var q=best(s,`passYards`),r=best(s,`rushYards`),w=best(s,`recYards`);
 var out=[];
 if(q)out.push([`PASS`,q.name,(q.passComp||0)+`/`+(q.passAtt||0)+` · `+(q.passYards||0)+` yds`+((q.passTD||0)?` · `+q.passTD+` TD`:``)+((q.interceptions||0)?` · `+q.interceptions+` INT`:``)]);
 if(r)out.push([`RUSH`,r.name,(r.rushAtt||0)+` car · `+(r.rushYards||0)+` yds`+((r.rushTD||0)?` · `+r.rushTD+` TD`:``)]);
 if(w)out.push([`REC`,w.name,(w.rec||0)+` rec · `+(w.recYards||0)+` yds`+((w.recTD||0)?` · `+w.recTD+` TD`:``)]);
 return out;
};
var bar=function(a,h){
 var A=Number(a)||0,H=Number(h)||0,T=A+H;
 if(T<=0) return null;
 var pa=A/T*100;
 return (0,I.jsxs)(`div`,{className:`mt-1 flex h-1 overflow-hidden rounded-full bg-surface-2`,children:[
  (0,I.jsx)(`div`,{style:{width:pa+`%`,background:`oklch(70% .1 210)`}}),
  (0,I.jsx)(`div`,{style:{width:(100-pa)+`%`,background:`oklch(78% .12 78)`}})]});
};
var side_block=function(s,abbr){
 var L=lead(s);
 return (0,I.jsxs)(`div`,{className:`hfl-card p-2.5`,children:[
  (0,I.jsx)(`p`,{className:`hfl-label mb-1.5`,children:abbr}),
  L.length===0?(0,I.jsx)(`p`,{className:`text-[0.7rem] text-muted-foreground`,children:`No production yet`}):
  (0,I.jsx)(`div`,{className:`space-y-1.5`,children:L.map(function(x,i){
   return (0,I.jsxs)(`div`,{children:[
    (0,I.jsxs)(`p`,{className:`text-[0.7rem] font-semibold leading-tight`,children:[
      (0,I.jsx)(`span`,{className:`mr-1.5 font-display text-[0.6rem] tracking-widest text-muted-foreground`,children:x[0]}),x[1]]}),
    (0,I.jsx)(`p`,{className:`text-[0.66rem] tabular-nums text-muted-foreground`,children:x[2]})]},i)})})]});
};
return (0,I.jsxs)(`section`,{className:`mt-4`,children:[
 (0,I.jsx)(`p`,{className:`hfl-label mb-2`,children:`Box score`}),
 (0,I.jsxs)(`div`,{className:`hfl-card p-3`,children:[
  (0,I.jsxs)(`div`,{className:`mb-2 flex items-center justify-between font-display text-[0.68rem] uppercase tracking-widest`,children:[
   (0,I.jsx)(`span`,{className:`text-defense`,children:t.away.abbr}),
   (0,I.jsx)(`span`,{className:`text-muted-foreground`,children:`Team`}),
   (0,I.jsx)(`span`,{className:`text-primary`,children:t.home.abbr})]}),
  (0,I.jsx)(`div`,{className:`space-y-2`,children:rows.map(function(r,i){
   return (0,I.jsxs)(`div`,{children:[
    (0,I.jsxs)(`div`,{className:`flex items-baseline justify-between gap-2`,children:[
     (0,I.jsx)(`span`,{className:`w-12 text-left text-sm font-semibold tabular-nums`,children:r[1]}),
     (0,I.jsx)(`span`,{className:`flex-1 text-center text-[0.66rem] uppercase tracking-widest text-muted-foreground`,children:r[0]}),
     (0,I.jsx)(`span`,{className:`w-12 text-right text-sm font-semibold tabular-nums`,children:r[2]})]}),
    r[3]?bar(r[1],r[2]):null]},i)})})]}),
 (0,I.jsxs)(`div`,{className:`mt-2 grid grid-cols-2 gap-2`,children:[
   side_block(`away`,t.away.abbr),side_block(`home`,t.home.abbr)]})]});
})()),"""

html=sub(ANCHOR, BOX+ANCHOR, 'live sim play-by-play')
io.open(OUT,'w',encoding='utf-8').write(html)
print(f'wrote {OUT} ({len(html)} chars)')
