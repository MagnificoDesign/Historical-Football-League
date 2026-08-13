#!/usr/bin/env python3
"""Two of Nick's calls: Stafford and Roethlisberger to 89, and the tier-cap
toggle moved onto the league setup screen next to the player-pool control.

Tier caps were already built and working (v4) — the toggle just lived on the
draft board, which is after the point you'd want to decide it.
"""
import sys, io
SRC='hfl-v16.html'; OUT='hfl-v17.html'
html=io.open(SRC,encoding='utf-8').read()
def sub(old,new,label):
    n=html.count(old)
    if n!=1: sys.exit(f'ANCHOR {label}: expected 1, found {n}')
    return html.replace(old,new,1)

# 1. Nick: "keep Stafford and Roethlisberger at 89, keep all those guys there"
html = sub("G.__HFL_QBFIX = {\n  'Tom Brady':95, 'Peyton Manning':94, 'Brett Favre':90, 'Dan Marino':90,",
           "G.__HFL_QBFIX = {\n  'Tom Brady':95, 'Peyton Manning':94, 'Brett Favre':90, 'Dan Marino':90,\n"
           "  'Matthew Stafford':89, 'Ben Roethlisberger':89,",
           'stafford/roethlisberger')

# 2. tier-cap toggle on the setup screen, under the player-pool control
TOGGLE_ANCHOR = (" ready?null:(0,I.jsx)(`p`,{className:`mt-1 text-[0.62rem] text-muted-foreground`,"
                 "children:`Modern pool still loading…`})]});\n})()),")
TOGGLE = r""" ready?null:(0,I.jsx)(`p`,{className:`mt-1 text-[0.62rem] text-muted-foreground`,children:`Modern pool still loading…`}),
 (0,I.jsxs)(`div`,{className:`mt-2.5 border-t border-border pt-2.5`,children:[
  (0,I.jsxs)(`label`,{className:`flex items-start gap-2`,children:[
   (0,I.jsx)(`input`,{type:`checkbox`,defaultChecked:!!globalThis.__HFL_TIERMODE,
     onChange:function(ev){
       globalThis.__HFL_TIERMODE=ev.target.checked;
       try{localStorage.setItem(`hfl.tiercaps`,ev.target.checked?`1`:`0`);}catch(_e){}
     },
     className:`mt-0.5 h-4 w-4 accent-primary`}),
   (0,I.jsxs)(`span`,{className:`text-xs`,children:[
     (0,I.jsx)(`span`,{className:`hfl-label block`,children:`Tier caps`}),
     (0,I.jsx)(`span`,{className:`text-muted-foreground`,
       children:`Limit how many stars a club can draft — 1 Legend, 3 Elite, 4 Star, 5 Quality, 8 Solid. Every club obeys it, and the board shows a tier badge instead of a rating.`})]})]})]})]});
})()),"""
html = sub(TOGGLE_ANCHOR, TOGGLE, 'tier toggle')

io.open(OUT,'w',encoding='utf-8').write(html)
print(f'wrote {OUT} ({len(html)} chars)')

# ---------------------------------------------------------------------------
# 3. The tier system read the RAW rating (Qf) while the game and the badges use
# the corrected one, so a corrected 90 was counted as a Star and clubs sailed
# past their caps. Give the tier code the same rating everything else sees.
html2 = io.open(OUT, encoding='utf-8').read()
def sub2(old, new, label, count=1):
    global html2
    n = html2.count(old)
    if n != count: sys.exit(f'ANCHOR {label}: expected {count}, found {n}')
    html2 = html2.replace(old, new, count)

RATEOF = r"""
// The rating the tier caps must use: the same one the sim, the board and the
// badges see. Mirrors __HFL_APPLYFIX without needing a SimPlayer.
G.__HFL_RATEOF = function(p, raw){
  if (!p) return 0;
  var r = null;
  try { r = raw ? raw(p) : (G.__HFL_QFRAW ? G.__HFL_QFRAW(p) : null); } catch(e) {}
  if (typeof G.__HFL_MODRATE[p.id] === 'number') r = G.__HFL_MODRATE[p.id];
  var f = G.__HFL_RATEFIX[p.name];
  if (f && typeof f.r === 'number') r = f.r;
  if ((p.primaryPosition === 'QB') && G.__HFL_QBFIX[p.name] != null) r = G.__HFL_QBFIX[p.name];
  var st = G.__HFL_CAREER;
  if (st && st.players) {
    var cr = st.players[p.id];
    if (cr && typeof cr.delta === 'number' && typeof r === 'number')
      r = Math.max(30, Math.min(99, Math.round(r + cr.delta)));
  }
  return r;
};
"""
sub2("G.__HFL_HFA = 0.060;", RATEOF + "G.__HFL_HFA = 0.060;", 'rateof')

# hand the raw rating fn to the prelude, then point every tier call at __HFL_RATEOF
sub2("function $f(e){let _s=", "function $f(e){globalThis.__HFL_QFRAW||(globalThis.__HFL_QFRAW=Qf);let _s=", 'qfraw')
sub2("globalThis.__HFL_CAPOK(e,t,n,Qf)", "globalThis.__HFL_CAPOK(e,t,n,function(p){return globalThis.__HFL_RATEOF(p,Qf)})", 'capok ai')
sub2("globalThis.__HFL_CAPOK(e,e.teams.find(x=>x.isHuman)?.id,j,Qf)",
     "globalThis.__HFL_CAPOK(e,e.teams.find(x=>x.isHuman)?.id,j,function(p){return globalThis.__HFL_RATEOF(p,Qf)})", 'capok human')
sub2("globalThis.__HFL_TIERUSED(e,hu.id,Qf)", "globalThis.__HFL_TIERUSED(e,hu.id,function(p){return globalThis.__HFL_RATEOF(p,Qf)})", 'tierused ui')

io.open(OUT,'w',encoding='utf-8').write(html2)
print(f'tier ratings unified ({len(html2)} chars)')
