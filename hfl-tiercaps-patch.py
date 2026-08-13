#!/usr/bin/env python3
"""TIER-CAP DRAFT MODE — hfl-v3.html -> hfl-v4.html

Legend 95+ / Elite 90-94 / Star 85-89 / Quality 80-84 / Solid 75-79, caps 1/3/4/5/8.
Five anchors, each asserted unique:
  1. prelude   — tier maths, caps, mode flag (localStorage-backed)
  2. Ou()      — AI candidate score returns -1e9 when that tier is full for the club
  3. ce()      — human pick blocked with a toast when the tier is full
  4. board row — LEGEND/ELITE/STAR/... badge beside the position line
  5. pool head — mode toggle + live cap counter
"""
import io, sys

SRC='hfl-v3.html'; OUT='hfl-v4.html'
html=io.open(SRC,encoding='utf-8').read()

def once(a,label):
    n=html.count(a)
    if n!=1: sys.exit(f'ANCHOR {label}: found {n}, expected 1')
    return a

# ---------------------------------------------------------------- 1. prelude
A1=once("G.__HFL_HFA = 0.060;",'prelude')
PRE = r"""
// ---- TIER-CAP DRAFT MODE ------------------------------------------------
G.__HFL_TIERS = [
  {k:'L', lo:95, name:'LEGEND',  cap:1, cls:'border-amber-300/70 bg-amber-300/20 text-amber-200'},
  {k:'E', lo:90, name:'ELITE',   cap:3, cls:'border-primary/60 bg-primary/20 text-primary'},
  {k:'S', lo:85, name:'STAR',    cap:4, cls:'border-sky-400/50 bg-sky-400/15 text-sky-300'},
  {k:'Q', lo:80, name:'QUALITY', cap:5, cls:'border-emerald-400/40 bg-emerald-400/12 text-emerald-300'},
  {k:'D', lo:75, name:'SOLID',   cap:8, cls:'border-border bg-surface-2 text-muted-foreground'}
];
G.__HFL_TIER = function(r){
  if (typeof r !== 'number') return null;
  for (var i=0;i<G.__HFL_TIERS.length;i++) if (r >= G.__HFL_TIERS[i].lo) return G.__HFL_TIERS[i];
  return null;   // under 75 is uncapped depth and carries no badge
};
G.__HFL_TIERMODE = (function(){
  try { return localStorage.getItem('hfl.tiercaps') === '1'; } catch(e){ return false; }
})();
G.__HFL_SETTIERMODE = function(on){
  G.__HFL_TIERMODE = !!on;
  try { localStorage.setItem('hfl.tiercaps', on ? '1' : '0'); } catch(e){}
};
// how many of each tier a club has already taken. ratingOf must be supplied by
// the caller (the rating function lives in a lazy module scope).
G.__HFL_TIERUSED = function(league, teamId, ratingOf){
  var used = {L:0,E:0,S:0,Q:0,D:0};
  if (!league || !league.picks) return used;
  var byId = G.__HFL_IDX && G.__HFL_IDX.league === league ? G.__HFL_IDX.map : null;
  if (!byId) {
    byId = new Map();
    for (var i=0;i<league.players.length;i++) byId.set(league.players[i].id, league.players[i]);
    G.__HFL_IDX = {league: league, map: byId};
  }
  for (var j=0;j<league.picks.length;j++){
    var p = league.picks[j];
    if (p.teamId !== teamId) continue;
    var pl = byId.get(p.playerId);
    if (!pl) continue;
    var t = G.__HFL_TIER(ratingOf(pl));
    if (t) used[t.k]++;
  }
  return used;
};
G.__HFL_CAPOK = function(league, teamId, player, ratingOf){
  if (!G.__HFL_TIERMODE) return true;
  var t = G.__HFL_TIER(ratingOf(player));
  if (!t) return true;                       // depth is unlimited
  return G.__HFL_TIERUSED(league, teamId, ratingOf)[t.k] < t.cap;
};
"""
html=html.replace(A1, PRE+A1, 1)

# ---------------------------------------------------------------- 2. AI score
A2=once("x+c*C+w+S+Math.random()*.4}",'ai score')
html=html.replace(A2,
  "(globalThis.__HFL_TIERMODE&&!globalThis.__HFL_CAPOK(e,t,n,Qf)?-1e9:"
  "(x+c*C+w+S+Math.random()*.4))}", 1)

# ---------------------------------------------------------------- 3. human pick
A3=once("let t=Su(j.id,u);if(!t.ok){uf.error(t.reason);return}",'human pick')
html=html.replace(A3,
  "if(globalThis.__HFL_TIERMODE&&!globalThis.__HFL_CAPOK(e,e.teams.find(x=>x.isHuman)?.id,j,Qf))"
  "{let tt=globalThis.__HFL_TIER(Qf(j));"
  "uf.error(`${tt.name} limit reached — you already have ${tt.cap}.`);return}"
  + A3, 1)

# ---------------------------------------------------------------- 4. board badge
A4=once("(0,I.jsxs)(`span`,{className:`hfl-label`,children:[e.primaryPosition,e.startYear?` · ${e.startYear}-${e.endYear??``}`:``]})",'board row')
html=html.replace(A4,
  "(0,I.jsxs)(`span`,{className:`hfl-label`,children:[e.primaryPosition,"
  "e.startYear?` · ${e.startYear}-${e.endYear??``}`:``]}),"
  "(()=>{if(!globalThis.__HFL_TIERMODE)return null;"
  "let tt=globalThis.__HFL_TIER(Qf(e));if(!tt)return null;"
  "return (0,I.jsx)(`span`,{className:`ml-1 rounded-sm border px-1 py-0.5 font-display "
  "text-[0.52rem] uppercase tracking-widest `+tt.cls,children:tt.name})})()", 1)

# ---------------------------------------------------------------- 5. toggle + counter
A5=once("(0,I.jsxs)(`span`,{className:`shrink-0 text-[0.65rem] text-muted-foreground`,children:[ie.length,` available`]})",'pool header')
html=html.replace(A5,
  A5 + ",(()=>{"
  "let hu=e.teams.find(x=>x.isHuman);"
  "let used=globalThis.__HFL_TIERMODE&&hu?globalThis.__HFL_TIERUSED(e,hu.id,Qf):null;"
  "return (0,I.jsxs)(`div`,{className:`mt-1 flex w-full flex-wrap items-center gap-1.5`,children:["
  "(0,I.jsx)(`button`,{onClick:()=>{globalThis.__HFL_SETTIERMODE(!globalThis.__HFL_TIERMODE);"
  "uf.success(globalThis.__HFL_TIERMODE?`Tier caps ON — 1 Legend / 3 Elite / 4 Star / 5 Quality / 8 Solid`:`Tier caps off.`);"
  "r(n+` `);setTimeout(()=>r(n),0)},"
  "className:globalThis.__HFL_TIERMODE"
  "?`rounded-md border border-primary bg-primary px-2 py-1 font-display text-[0.6rem] uppercase tracking-widest text-primary-foreground`"
  ":`rounded-md border border-border bg-surface-2 px-2 py-1 font-display text-[0.6rem] uppercase tracking-widest text-muted-foreground`,"
  "children:`Tier caps`}),"
  "...(used?globalThis.__HFL_TIERS.map(t=>(0,I.jsxs)(`span`,{"
  "className:(used[t.k]>=t.cap?`opacity-45 `:``)+`rounded-sm border px-1 py-0.5 font-display text-[0.55rem] uppercase tracking-widest `+t.cls,"
  "children:[t.name.slice(0,3),` `,used[t.k],`/`,t.cap]},t.k)):[])"
  "]})})()", 1)

io.open(OUT,'w',encoding='utf-8').write(html)
print(f'wrote {OUT} ({len(html)} chars)')
