#!/usr/bin/env python3
"""Adds AUTO-FILL to the personnel packages screen.

Two edits, each anchor asserted to appear EXACTLY ONCE:
 1. prelude: define G.__HFLAUTOFILL (role leverage + role-specific attribute scoring)
 2. ev() JSX: an "Auto-fill" button beside the "+ Package" button
"""
import re, sys, io

SRC = 'hfl-draft-room.html'
OUT = 'hfl-v3.html'

html = io.open(SRC, encoding='utf-8', errors='strict').read()

def once(anchor, name):
    n = html.count(anchor)
    if n != 1:
        sys.exit(f'ANCHOR {name}: expected 1 occurrence, found {n}')
    return anchor

# ---------------------------------------------------------------- 1. prelude
PRELUDE_ANCHOR = "G.__HFL_HFA = 0.060;"
once(PRELUDE_ANCHOR, 'prelude')

AUTOFILL = r"""
// ---- AUTO-FILL: build the best eleven for a package -------------------
// Leverage = measured per-player win impact (QB >> EDGE/CB > RB > LB ~ WR > OL).
G.__HFL_LEVERAGE = {QB:3.00,EDGE:1.62,DE:1.55,DT:1.20,NT:1.10,CB:1.50,S:1.22,
  FS:1.22,SS:1.20,RB:1.30,FB:0.70,WR:1.16,X:1.20,Z:1.14,SLOT:1.08,TE:1.02,
  MIKE:1.12,WILL:1.06,SAM:1.04,LB:1.08,LT:1.05,RT:0.98,LG:0.92,C:0.95,RG:0.92,
  OL:0.95,OT:1.02,K:0.50,P:0.45};
// Role-specific attribute emphasis — what actually wins that job.
G.__HFL_ROLEKEYS = {
  QB:['processing','accuracyShort','accuracyDeep','armStrength','pressureHandling'],
  RB:['vision','elusiveness','power','hands'], FB:['runBlocking','power'],
  X:['separation','contestedCatch','routeCraft','hands'],
  Z:['separation','routeCraft','hands','speed'],
  SLOT:['routeCraft','hands','separation'],
  WR:['separation','routeCraft','hands'],
  TE:['hands','routeCraft','runBlocking'],
  LT:['passSet','anchor','handTechnique'], RT:['passSet','anchor','handTechnique'],
  OT:['passSet','anchor','handTechnique'],
  LG:['runBlocking','anchor','power'], RG:['runBlocking','anchor','power'],
  C:['awareness','anchor','handTechnique'], OL:['passSet','anchor','runBlocking'],
  EDGE:['passRush','firstStep','bend','motor'], DE:['passRush','firstStep','power'],
  DT:['power','blockShedding','passRush'], NT:['runDefense','power','blockShedding'],
  MIKE:['diagnosis','tackling','runFit'], WILL:['range','tackling','coverage'],
  SAM:['runFit','tackling','coverage'], LB:['tackling','runFit','coverage'],
  CB:['manCoverage','recovery','zoneCoverage'],
  S:['deepEye','range','tackling'], FS:['deepEye','range','zoneCoverage'],
  SS:['tackling','hitPower','runFit'],
  K:['placement','clutch'], P:['placement']
};
G.__HFL_ROLELEV = function(role){
  var t = String(role||'').trim().toUpperCase();
  if (G.__HFL_LEVERAGE[t] != null) return G.__HFL_LEVERAGE[t];
  var keys = Object.keys(G.__HFL_LEVERAGE);
  for (var i=0;i<keys.length;i++) if (t.indexOf(keys[i])===0) return G.__HFL_LEVERAGE[keys[i]];
  if (/TECH/.test(t)) return 1.15;
  return 1.0;
};
// score one player for one role. sim = converted SimPlayer, sameGroup = role group matches his
G.__HFL_ATTR = function(p,k){
  if(!p) return null;
  var v = p.attrs && p.attrs[k];    if (typeof v==='number') return v;
  v = p.attributes && p.attributes[k]; if (typeof v==='number') return v;
  return null;   // NO fallback to overall rating — a QB has no 'vision'
};
G.__HFL_ROLESCORE = function(sim, role, sameGroup){
  if (!sim) return -1;
  var base = (typeof sim.rating==='number' ? sim.rating : 55);
  var t = String(role||'').trim().toUpperCase(), keys = null, kk = Object.keys(G.__HFL_ROLEKEYS);
  if (G.__HFL_ROLEKEYS[t]) keys = G.__HFL_ROLEKEYS[t];
  else for (var i=0;i<kk.length;i++) if (t.indexOf(kk[i])===0) { keys = G.__HFL_ROLEKEYS[kk[i]]; break; }
  var spec = base;
  if (keys && keys.length) {
    var sum=0, n=0;
    for (var j=0;j<keys.length;j++){ var v = G.__HFL_ATTR(sim, keys[j]); if (typeof v==='number'){ sum+=v; n++; } }
    if (n) spec = sum/n;
  }
  // 65% what the job asks for, 35% overall quality; out-of-position costs a fit penalty
  var score = spec*0.65 + base*0.35;
  if (!sameGroup) score -= 34;   // out of position is a real cost, not a rounding error
  return score;
};
// Greedy assignment: highest-leverage roles pick first from the whole roster.
// slots: [{id, role}], pool: [{id, sim, group}], returns {slotId: playerId}
G.__HFLAUTOFILL = function(slots, pool){
  var order = slots.map(function(s,i){ return {s:s, lev:G.__HFL_ROLELEV(s.role), i:i}; })
                   .sort(function(a,b){ return b.lev-a.lev || a.i-b.i; });
  var used = {}, out = {};
  for (var k=0;k<order.length;k++){
    var slot = order[k].s, best=null, bestScore=-1e9;
    // pass 1 = only players who actually play this position; pass 2 = anyone left
    var native = [];
    for (var q=0;q<pool.length;q++) if (!used[pool[q].id] && pool[q].sameGroup(slot.role)) native.push(pool[q]);
    var cand = native.length ? native : pool;
    for (var m=0;m<cand.length;m++){
      var p = cand[m];
      if (used[p.id]) continue;
      var sc = G.__HFL_ROLESCORE(p.sim, slot.role, p.sameGroup(slot.role));
      // leverage-weighted: a star is worth more where the job matters
      sc = sc * (0.88 + 0.12*order[k].lev);
      if (sc > bestScore){ bestScore = sc; best = p; }
    }
    if (best){ used[best.id] = 1; out[slot.id] = best.id; }
  }
  return out;
};
"""

html = html.replace(PRELUDE_ANCHOR, AUTOFILL + PRELUDE_ANCHOR, 1)

# ---------------------------------------------------------------- 2. the button
BTN_ANCHOR = ("`ml-auto inline-flex items-center gap-1 rounded-md border border-border "
              "bg-surface-2 px-2.5 py-1.5 font-display text-[0.68rem] uppercase tracking-widest "
              "text-muted-foreground`,children:[(0,I.jsx)(Ia,{className:`h-3.5 w-3.5`}),` Package`]})")
once(BTN_ANCHOR, 'package button')

# Auto-fill handler, written in the *local* scope of ev():
#   s = team, c = packages on this side, l = roster, d = groupOf(player), Rl = roleGroup,
#   jd(teamId, packId, slotId, playerId) = assign, $f = SimPlayer converter
AUTOFILL_BTN = (
    "`ml-auto inline-flex items-center gap-1 rounded-md border border-border "
    "bg-surface-2 px-2.5 py-1.5 font-display text-[0.68rem] uppercase tracking-widest "
    "text-muted-foreground`,children:[(0,I.jsx)(Ia,{className:`h-3.5 w-3.5`}),` Package`]}),"
    "(0,I.jsx)(`button`,{onClick:()=>{"
    "try{"
    "let pool=l.map(p=>({id:p.id,sim:$f(p),grp:d(p),"
    "sameGroup:(role)=>{let g=Rl(role);return !g||g===d(p);}}));"
    "for(let pk of c){"
    "let asg=globalThis.__HFLAUTOFILL(pk.slots.map(x=>({id:x.id,role:x.role})),pool);"
    "for(let sl of pk.slots){let pid=asg[sl.id]??null;jd(s.id,pk.id,sl.id,pid);}"
    "}"
    "}catch(err){console.error(`autofill`,err);}"
    "},"
    "className:`inline-flex items-center gap-1 rounded-md border border-primary/60 "
    "bg-primary/15 px-2.5 py-1.5 font-display text-[0.68rem] uppercase tracking-widest text-primary`,"
    "children:`Auto-fill`})"
)

html = html.replace(BTN_ANCHOR, AUTOFILL_BTN, 1)


# ------------------------------------------------- 3. CB1/CB2 mis-mapped to OL
# Rl() tested /^(LT|LG|C|...)/ before the CB branch, so "CB1" matched the centre
# rule and every corner slot offered offensive linemen. Require C not be followed
# by another letter.
ROLE_ANCHOR = "/^(LT|LG|C|RG|RT|OL|OT|OG)/.test(t)?`OL`:"
once(ROLE_ANCHOR, 'role mapper')
html = html.replace(ROLE_ANCHOR, "(/^(LT|LG|RG|RT|OL|OT|OG)/.test(t)||/^C(?![A-Z])/.test(t))?`OL`:", 1)


# ------------------------------------------------- 4. cross-position slot lists
# The slot dropdown only offered the role's own group, so an EDGE or a safety
# could never be listed at LB. Widen it with the app's own adjacency map
# (Qg: LB <-> CB/S, LB <-> DL/EDGE, WR/TE <-> RB, OL <-> DL/EDGE): natives first,
# then the cross-position options, then everyone else as a last resort.
SLOT_ANCHOR = ("f=(e,t)=>{let n=Rl(e);if(!n)return l;let r=l.filter(e=>d(e)===n),"
               "i=t?l.find(e=>e.id===t):void 0;return i&&!r.some(e=>e.id===i.id)?[i,...r]:r}")
once(SLOT_ANCHOR, 'slot eligibility')
SLOT_NEW = ("f=(e,t)=>{let n=Rl(e);if(!n)return l;"
            "let nat=l.filter(x=>d(x)===n),"
            "cross=l.filter(x=>d(x)!==n&&Qg(n,d(x))),"
            "rest=l.filter(x=>d(x)!==n&&!Qg(n,d(x))),"
            "r=[...nat,...cross,...rest],"
            "i=t?l.find(x=>x.id===t):void 0;"
            "return i&&!r.some(x=>x.id===i.id)?[i,...r]:r}")
html = html.replace(SLOT_ANCHOR, SLOT_NEW, 1)

io.open(OUT, 'w', encoding='utf-8').write(html)
print(f'wrote {OUT}  ({len(html)} bytes, was {len(io.open(SRC,encoding="utf-8").read())})')
