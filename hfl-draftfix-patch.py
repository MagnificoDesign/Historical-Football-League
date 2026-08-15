#!/usr/bin/env python3
"""THREE FIXES FROM NICK'S DRAFT SESSION.

  1. BLOCKER — "Choose a franchise for this pick first." The human pick handler
     `Su()` refuses any selection unless the round has a franchise drawn. In a
     32-club franchise league there IS no franchise, so every pick was
     rejected. Nick could see the board and couldn't draft from it.
  2. "Sim to my pick" — one button that runs the AI clubs straight to his turn,
     instead of "auto this round" / "auto entire draft".
  3. AGES on the board, and the career-span line removed. Real birth years for
     12,071 of 12,626 players from the nflverse record; the rest are inferred
     from debut year at 22.
"""
import sys, io, re
SRC='hfl-v47.html'; OUT='hfl-v48.html'
html=io.open(SRC,encoding='utf-8').read()
B64=io.open('timeline_payload.b64').read().strip()
def sub(old,new,label):
    n=html.count(old)
    if n!=1: sys.exit(f'ANCHOR {label}: expected 1, found {n}')
    return html.replace(old,new,1)

# refreshed payload — now carries birth years
m = re.search(r'G\.__HFL_TIMELINE_B64 = "([^"]*)";', html)
if not m: sys.exit('payload not found')
html = html[:m.start(1)] + B64 + html[m.end(1):]

# 1. THE BLOCKER — no franchise means no franchise check
html = sub("r.franchiseId?mu(i,r.franchiseId,r.round.side)?"
           "(xu(n,r.team,r.round,r.pickInRound,i.id,t,r.franchiseId),au(),{ok:!0})"
           ":{ok:!1,reason:`${i.name} never played for this franchise.`,code:`ineligible`}"
           ":{ok:!1,reason:`Choose a franchise for this pick first.`,code:`no-franchise`}",
           "(globalThis.__HFL_SNAKE&&globalThis.__HFL_SNAKE())?"
           "(xu(n,r.team,r.round,r.pickInRound,i.id,t,null),au(),{ok:!0})"
           ":r.franchiseId?mu(i,r.franchiseId,r.round.side)?"
           "(xu(n,r.team,r.round,r.pickInRound,i.id,t,r.franchiseId),au(),{ok:!0})"
           ":{ok:!1,reason:`${i.name} never played for this franchise.`,code:`ineligible`}"
           ":{ok:!1,reason:`Choose a franchise for this pick first.`,code:`no-franchise`}",
           'no franchise gate on the human pick')

# 3. ages on the board instead of the career span
G_AGE = r"""
// A player's age in the league's current calendar year. Real birth years for
// 12,071 of 12,626 men; the rest inferred from debut at 22.
G.__HFL_AGE_OF = function(player, league){
  try {
    var key = String(player.externalId||'').replace('nflverse:','');
    var rec = G.__HFL_TIMELINE ? G.__HFL_TIMELINE[key] : null;
    if (!rec || !rec.b) return null;
    var st = G.__HFL_CAREER;
    var yr = (G.__HFL_STARTYEAR || 0) + (((st && st.year) || 1) - 1);
    if (!G.__HFL_STARTYEAR) return null;
    return yr - rec.b;
  } catch(e) { return null; }
};
"""
html = sub("G.__HFL_HFA = 0.060;", G_AGE + "G.__HFL_HFA = 0.060;", 'age helper')

# the board row specifically — the career span also renders in a roster list,
# which is left alone
html = sub("children:[e.primaryPosition,e.startYear?` · ${e.startYear}-${e.endYear??``}`:``]",
           "children:[e.primaryPosition,(()=>{var a=globalThis.__HFL_AGE_OF?globalThis.__HFL_AGE_OF(e):null;"
           "return a?` · age ${a}`:(e.startYear?` · ${e.startYear}-${e.endYear??``}`:``);})()]",
           'age on the board row')

io.open(OUT,'w',encoding='utf-8').write(html)
print(f'wrote {OUT} ({len(html)} chars)')

# 2. ONE BUTTON. In a franchise league "auto this round" and "auto entire draft"
# both mean the same thing now that the loop stops at the human's pick: run the
# AI clubs until it is my turn. So show a single "Sim to my pick".
html2 = io.open(OUT, encoding='utf-8').read()
def sub2(old, new, label):
    global html2
    n = html2.count(old)
    if n != 1: sys.exit(f'ANCHOR {label}: expected 1, found {n}')
    html2 = html2.replace(old, new, 1)

sub2("(0,I.jsxs)(`div`,{className:`flex gap-2`,children:["
     "(0,I.jsx)(`button`,{onClick:()=>{Pu(),uf.info(`Auto-drafting your pick this round.`)},"
     "className:`flex-1 rounded-md border border-primary/50 bg-surface-2 py-2.5 font-display text-xs font-semibold uppercase tracking-[0.14em] text-primary`,"
     "children:`Auto this round`}),"
     "(0,I.jsx)(`button`,{onClick:()=>y(!0),"
     "className:`flex-1 rounded-md border border-border bg-surface-2 py-2.5 font-display text-xs font-semibold uppercase tracking-[0.14em] text-muted-foreground`,"
     "children:`Auto entire draft`})]})",
     "((globalThis.__HFL_SNAKE&&globalThis.__HFL_SNAKE())?"
     "(0,I.jsx)(`button`,{onClick:()=>{Fu();Iu();},"
     "className:`w-full rounded-md border border-primary bg-primary py-3 font-display text-xs font-semibold uppercase tracking-[0.16em] text-primary-foreground`,"
     "children:`Sim to my pick`})"
     ":(0,I.jsxs)(`div`,{className:`flex gap-2`,children:["
     "(0,I.jsx)(`button`,{onClick:()=>{Pu(),uf.info(`Auto-drafting your pick this round.`)},"
     "className:`flex-1 rounded-md border border-primary/50 bg-surface-2 py-2.5 font-display text-xs font-semibold uppercase tracking-[0.14em] text-primary`,"
     "children:`Auto this round`}),"
     "(0,I.jsx)(`button`,{onClick:()=>y(!0),"
     "className:`flex-1 rounded-md border border-border bg-surface-2 py-2.5 font-display text-xs font-semibold uppercase tracking-[0.14em] text-muted-foreground`,"
     "children:`Auto entire draft`})]}))",
     'one sim button')

io.open(OUT,'w',encoding='utf-8').write(html2)
print('single sim-to-my-pick button')
