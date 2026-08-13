#!/usr/bin/env python3
"""QB RATING CORRECTIONS — Nick's call, plus an override-ordering fix.

Also raises the elite-QB draft flag from 88 to 90 at Nick's instruction: a
quarterback is only protected from the need filter if he is genuinely elite.

Nick reviewed the elite QB list and set these by hand. The all-time DB's QB
ratings had never been audited: Matt Ryan was tied for the highest-rated
quarterback in the game, Manning sat below Cam Newton, and Brady was an 87.

  Brady 87 -> 95      Ryan 94 -> 82       Prescott 89 -> 82
  Manning 89 -> 94    Newton 91 -> 82     Cousins 89 -> 82
  Lamar 90 -> 88      Goff 90 -> 83       Wilson 89 -> 85

ORDERING BUG FIXED IN THE SAME PASS: __HFL_APPLYFIX applied the name-keyed
rating override AFTER the career delta, so in a franchise league an ageing
Brady would snap back to 95 every single season — aging would never touch any
corrected player. Base overrides now resolve first, then aging applies on top.
"""
import sys, io
SRC='hfl-v14.html'; OUT='hfl-v15.html'
html=io.open(SRC,encoding='utf-8').read()
def sub(old,new,label):
    n=html.count(old)
    if n!=1: sys.exit(f'ANCHOR {label}: expected 1, found {n}')
    return html.replace(old,new,1)

OLD = """G.__HFL_APPLYFIX = function(sim){
  if(!sim) return sim;
  var mr = G.__HFL_MODRATE[sim.id];
  if (typeof mr === 'number') sim.rating = mr;
  var st = G.__HFL_CAREER;
  if (st && st.players) {
    var cr = st.players[sim.id];
    if (cr && typeof cr.delta === 'number' && typeof sim.rating === 'number')
      sim.rating = Math.max(30, Math.min(99, Math.round(sim.rating + cr.delta)));
  }
  var f = G.__HFL_RATEFIX[sim.name];
  if(!f) return sim;
  if(typeof f.r === 'number') sim.rating = f.r;
  if(f.a && sim.attrs) for(var k in f.a) if(k in sim.attrs) sim.attrs[k] = f.a[k];
  return sim;
};"""

NEW = """G.__HFL_QBFIX = {
  'Tom Brady':95, 'Peyton Manning':94, 'Brett Favre':90, 'Dan Marino':90,
  'Matt Ryan':82, 'Cam Newton':82, 'Jared Goff':83, 'Lamar Jackson':88,
  'Dak Prescott':82, 'Kirk Cousins':82, 'Russell Wilson':85,
  'Philip Rivers':86, 'Joe Flacco':78
};
G.__HFL_APPLYFIX = function(sim){
  if(!sim) return sim;
  // 1. base rating: modern pool by id, then the named corrections
  var mr = G.__HFL_MODRATE[sim.id];
  if (typeof mr === 'number') sim.rating = mr;
  var f = G.__HFL_RATEFIX[sim.name];
  if (f && typeof f.r === 'number') sim.rating = f.r;
  if (sim.pos === 'QB' && G.__HFL_QBFIX[sim.name] != null) sim.rating = G.__HFL_QBFIX[sim.name];
  // 2. attributes
  if (f && f.a && sim.attrs) for (var k in f.a) if (k in sim.attrs) sim.attrs[k] = f.a[k];
  // 3. aging LAST, so a corrected player still ages instead of snapping back
  var st = G.__HFL_CAREER;
  if (st && st.players) {
    var cr = st.players[sim.id];
    if (cr && typeof cr.delta === 'number' && typeof sim.rating === 'number')
      sim.rating = Math.max(30, Math.min(99, Math.round(sim.rating + cr.delta)));
  }
  return sim;
};"""
html = sub(OLD, NEW, 'applyfix reorder + QB fixes')

# MANDATORY DRAFTS — Nick named exactly five. The need-filter bypass now
# applies to these men only, rather than to any 90+ player. A club that
# already has one of them still skips the next (the upgrade gate handles it:
# Brady 95 vs Manning 94 is not a +5 upgrade).
html = sub("G.__HFL_ELITE_MIN = {QB:88, RB:90, 'WR/TE':90, OL:90, 'DL/EDGE':90, LB:90, 'CB/S':90};",
  "G.__HFL_MANDATORY = {'Tom Brady':1,'Aaron Rodgers':1,'Peyton Manning':1,'Joe Montana':1,'Steve Young':1};\n"
  "G.__HFL_ELITE_MIN = {};", 'mandatory list')

# only the named men bypass the need filter
html = sub("      var min = G.__HFL_ELITE_MIN[cg];\n      if (min == null) continue;\n      var cr = ratingOf(cand);\n      if (typeof cr !== 'number' || cr < min) continue;",
  "      if (!G.__HFL_MANDATORY[cand.name]) continue;\n      var cr = ratingOf(cand);\n      if (typeof cr !== 'number') continue;\n      if (cg === 'QB' && G.__HFL_HASMANDATORY(league, teamId, 'QB', byId.map, groupOf)) continue;\n      if (needList.indexOf(cand) === -1) extra.push(cand);\n      continue;", 'mandatory gate')
# ---- the helpers the mandatory gate calls, injected into the bundle ----
HELPERS = """G.__HFL_HASMANDATORY = function(league, teamId, group, byId, groupOf){
  for (var i=0;i<league.picks.length;i++){
    var pk = league.picks[i];
    if (pk.teamId !== teamId) continue;
    var pl = byId[pk.playerId];
    if (!pl) continue;
    if (groupOf(pl.primaryPosition) !== group) continue;
    if (G.__HFL_MANDATORY[pl.name]) return true;
  }
  return false;
};
// Nick's rule: hold one of the five and you do not draft another QB above 85.
// A backup is fine; a second starter-grade arm is not.
G.__HFL_BACKUP_CAP = 85;
// ONE rule, stated two ways by Nick and equivalent: a club never ends up with
// two quarterbacks above 85. So a club holding Brady won't add Marino, and a
// club that already took Marino won't be handed Montana by the bypass either.
G.__HFL_BESTQB = function(league, teamId, byId, groupOf, ratingOf){
  var best = -1;
  for (var i=0;i<league.picks.length;i++){
    var pk = league.picks[i];
    if (pk.teamId !== teamId) continue;
    var pl = byId[pk.playerId];
    if (!pl || groupOf(pl.primaryPosition) !== 'QB') continue;
    var r = ratingOf(pl);
    if (typeof r === 'number' && r > best) best = r;
  }
  return best;
};
G.__HFL_CAPQB = function(league, teamId, list, byId, groupOf, ratingOf){
  var best = G.__HFL_BESTQB(league, teamId, byId, groupOf, ratingOf);
  var hasMand = G.__HFL_HASMANDATORY(league, teamId, 'QB', byId, groupOf);
  if (best <= G.__HFL_BACKUP_CAP && !hasMand) return list;
  var out = [];
  for (var i=0;i<list.length;i++){
    var p = list[i];
    if (groupOf(p.primaryPosition) === 'QB') {
      var r = ratingOf(p);
      var isMand = !!G.__HFL_MANDATORY[p.name];
      // a club may still upgrade to one of the five — but never holds two of
      // them, and never adds an ordinary starter behind a legend
      if (isMand ? hasMand : (typeof r === 'number' && r > G.__HFL_BACKUP_CAP)) continue;
    }
    out.push(p);
  }
  return out.length ? out : list;
};
G.__HFL_ELITEADD = function(league, teamId, needList, allCands, side, groupOf, ratingOf){"""
html = sub("G.__HFL_ELITEADD = function(league, teamId, needList, allCands, side, groupOf, ratingOf){",
           HELPERS, 'helpers')

# and cap the returned list
html = sub("    return extra.length ? needList.concat(extra) : needList;",
           "    var res = extra.length ? needList.concat(extra) : needList;\n"
           "    return G.__HFL_CAPQB(league, teamId, res, byId.map, groupOf, ratingOf);",
           'qb cap')

# Apply the QB cap to the FINAL candidate list, not just to the elite bypass.
# Late in the draft every roster minimum is satisfied, the need filter returns
# nothing, and the whole pool goes live — which is where second quarterbacks
# were slipping through.
html = sub("let r=a[0];if(n){let n=-1/0;",
  "if(n&&globalThis.__HFL_CAPQB){try{a=globalThis.__HFL_CAPQB(e,t.team.id,a,"
  "Object.fromEntries(e.players.map(p=>[p.id,p])),$s,Qf);}catch(_e){}}"
  "let r=a[0];if(n){let n=-1/0;", 'final cap')

io.open(OUT,'w',encoding='utf-8').write(html)
print(f'wrote {OUT} ({len(html)} chars)')
