#!/usr/bin/env python3
"""hfl-integrity-patch.py — v66 -> v67. The franchise integrity pass.

Implements the P0 items from the independent v65 audit, all verified in
source before patching:

F-06/F-07  RELEASE (retirement) and CUTDOWN dropped roster picks but never
           touched st.deals — 224 orphan deals after the very first
           offseason, 6,588 by year 25.  ->  __HFL_CLOSEDEAL, called from
           both paths: retirement closes the deal at zero (AAV-only deals,
           no proration to strand), a cut books half the AAV as dead money
           exactly like the existing COMPLY rule, then deletes the deal.
F-08       SIGNALL skipped any player who already had a deal, so a cut man
           re-signed elsewhere kept a deal naming his old club (337
           wrong-team deals by year 25).  ->  a matching-team deal still
           skips; a stale mismatched deal is deleted and re-signed fresh
           at the destination club.
F-03/F-04  CLASS_OF(cal) is empty after 2025 and ROOKIE_DRAFT returned
           silently, while the scarcity generator never fired because
           thousands of historical leftovers kept the pool large.  ->
           __HFL_GENCLASS: a deterministic 372-man future class (canon per
           calendar year, league-independent), class-shaped ratings capped
           at 83 so a generated man never outclasses a real legend, mr
           stamped on the row (v63 discipline).  ROOKIE_DRAFT now reports
           an explicit class mode: historical | historical-oversize |
           generated | empty.
F-10       Eleven catch blocks inside ADVANCE, five completely empty, and
           ok:true returned after any partial failure.  ->  every stage
           failure accumulates; any unrecovered error (awards excepted,
           documented cosmetic) blocks the commit and returns
           {ok:false, stage, errors}.  Five mid-offseason CAREER_SAVE
           calls are suppressed during the transaction (__HFL_TXN) so a
           failed offseason cannot half-commit the career book.
F-09       Cap compliance is not contract integrity.  ->  __HFL_LEDGER_AUDIT
           runs before every commit: zero orphans, zero wrong-team deals,
           every rostered player exactly one deal (econ leagues), no
           duplicate picks.  A failed audit blocks the commit.
Migration  __HFL_MIGRATE_BOOK runs once per book (schemaVersion 67):
           orphan deals deleted (no retroactive dead money — booking 25
           years of it would wreck existing caps), wrong-team deals
           retargeted to the roster club, missing deals created at the
           veteran minimum.
Bug C #3   A third calendar site (thisClass in REPLENISH) still read the
           page-load global; now league-scoped like the other two.

Anchors asserted unique before every replacement.
"""
import re, sys

SRC = sys.argv[1] if len(sys.argv) > 1 else 'hfl-v66.html'
DST = sys.argv[2] if len(sys.argv) > 2 else 'hfl-v67.html'
html = open(SRC).read()
applied = []

def patch(anchor, replacement, name, regex=False):
    global html
    if regex:
        hits = re.findall(anchor, html)
        assert len(hits) == 1, f'{name}: regex x{len(hits)}'
        html = re.sub(anchor, replacement, html, count=1)
    else:
        n = html.count(anchor)
        assert n == 1, f'{name}: anchor x{n}'
        html = html.replace(anchor, replacement)
    applied.append(name)

# ---------------------------------------------------------------- helpers
DEFS = r"""
// ---- v67 INTEGRITY LAYER ----------------------------------------------
// One place closes a contract, however the player leaves the roster.
G.__HFL_CLOSEDEAL = function(st, playerId, teamId, mode){
  if (!st || !st.deals) return;
  var d = st.deals[playerId];
  if (!d) return;
  if (mode === 'cut'){
    // the documented cut rule, identical to cap compliance:
    // half the remaining first year stays on the books
    var dead = Math.round(d.aav * 0.5 * 10)/10;
    if (!st.dead) st.dead = {};
    var t = teamId || d.team;
    st.dead[t] = Math.round(((st.dead[t]||0) + dead)*10)/10;
  }
  // retirement closes at zero: deals are AAV-only, nothing prorated to strand
  delete st.deals[playerId];
};

// The contract book must be one-to-one with the roster. Run before commit.
G.__HFL_LEDGER_AUDIT = function(league, st){
  var errs = [], roster = {}, seen = {}, i, pid;
  for (i=0;i<league.picks.length;i++){
    var pk = league.picks[i];
    if (seen[pk.playerId]) errs.push('duplicate pick ' + pk.playerId);
    seen[pk.playerId] = 1;
    roster[pk.playerId] = pk.teamId;
  }
  var deals = (st && st.deals) || {};
  var orphan = 0, wrong = 0, missing = 0;
  for (pid in deals){
    if (!(pid in roster)) orphan++;
    else if (deals[pid].team !== roster[pid]) wrong++;
  }
  if (G.__HFL_ECON_ON && G.__HFL_ECON_ON(league))
    for (pid in roster) if (!deals[pid]) missing++;
  if (orphan) errs.push(orphan + ' orphan deals');
  if (wrong) errs.push(wrong + ' wrong-team deals');
  if (missing) errs.push(missing + ' rostered players without a deal');
  return {ok: errs.length === 0, errors: errs, orphan: orphan,
          wrongTeam: wrong, missing: missing,
          deals: Object.keys(deals).length, picks: league.picks.length};
};

// One-time repair of a v65-era book. Orphans are deleted without
// retroactive dead money (booking 25 years of it would wreck saved caps);
// wrong-team deals retarget to the roster club; missing deals get the
// veteran minimum so the one-to-one invariant holds immediately.
G.__HFL_MIGRATE_BOOK = function(league, st){
  if (!st || st.schemaVersion === 67) return null;
  var roster = {}, i, pid;
  for (i=0;i<league.picks.length;i++) roster[league.picks[i].playerId] = league.picks[i].teamId;
  if (!st.deals) st.deals = {};
  var orphans = 0, retargeted = 0, created = 0;
  for (pid in st.deals){
    if (!(pid in roster)) { delete st.deals[pid]; orphans++; }
    else if (st.deals[pid].team !== roster[pid]) { st.deals[pid].team = roster[pid]; retargeted++; }
  }
  if (G.__HFL_ECON_ON && G.__HFL_ECON_ON(league)){
    var min = G.__HFL_MIN_SALARY || 1.2;
    for (i=0;i<league.picks.length;i++){
      var pk = league.picks[i];
      if (!st.deals[pk.playerId]){
        st.deals[pk.playerId] = {aav: min, yrs: 1, left: 1, team: pk.teamId};
        created++;
      }
    }
  }
  st.schemaVersion = 67;
  return {orphans: orphans, retargeted: retargeted, created: created};
};

// A deterministic future rookie class for calendar years past the real
// timeline. Canon per calendar year (no league salt): every franchise that
// reaches 2026 meets the same fictional class, the way every franchise
// meets the same real 2005. Ratings are class-shaped and capped at 83 so a
// generated prospect never quietly outclasses a real legend.
G.__HFL_GENCLASS_N = 372;
G.__HFL_GENCLASS = function(league, cal){
  var COUNTS = {'OL':81, 'DL/EDGE':65, 'WR/TE':66, 'CB/S':59, 'LB':44,
                'RB':28, 'QB':17, 'K':6, 'P':6};
  var bag = [], g, i, k;
  for (g in COUNTS) for (i=0;i<COUNTS[g];i++) bag.push(g);
  var rs = function(k){ var x = Math.sin(cal * 7919 + 999 * 12.9898 + k * 78.233) * 43758.5453; return x - Math.floor(x); };
  for (i=bag.length-1;i>0;i--){ var j = Math.floor(rs(i) * (i+1)); var t = bag[i]; bag[i] = bag[j]; bag[j] = t; }
  var out = [];
  for (i=0;i<bag.length;i++){
    var rnd = function(k){ var x = Math.sin(cal * 7919 + i * 12.9898 + k * 78.233) * 43758.5453; return x - Math.floor(x); };
    var rating;
    if (i < 3) rating = 79 + Math.floor(rnd(1) * 5);
    else if (i < 12) rating = 74 + Math.floor(rnd(1) * 6);
    else if (i < 40) rating = 68 + Math.floor(rnd(1) * 7);
    else if (i < 120) rating = 60 + Math.floor(rnd(1) * 9);
    else rating = 50 + Math.floor(rnd(1) * 11);
    g = bag[i];
    var posList = G.__HFL_GENPOS[g] || ['LB'];
    var pos = posList[Math.floor(rnd(2) * posList.length) % posList.length];
    var attrs = {}, keys = G.__HFL_GENATTRS[g] || [];
    for (k=0;k<keys.length;k++) attrs[keys[k]] = Math.max(35, Math.min(92,
      Math.round(rating + (rnd(10 + k) - 0.5) * 16)));
    var nm = G.__HFL_FIRST[Math.floor(rnd(4) * G.__HFL_FIRST.length) % G.__HFL_FIRST.length] + ' ' +
             G.__HFL_LAST[Math.floor(rnd(5) * G.__HFL_LAST.length) % G.__HFL_LAST.length];
    var id = 'p-gcls-' + cal + '-' + i;
    var rec = {id: id, name: nm, primaryPosition: pos, group: g,
      eligibility: [], status: 'Generated', custom: false, source: 'generated-class',
      startYear: cal, endYear: cal + 3 + Math.floor(rnd(7) * 9) + (rating >= 76 ? 2 : 0),
      attributes: attrs, mr: rating};
    G.__HFL_MODRATE[id] = rating;
    out.push(rec);
  }
  return out;
};

G.__HFL_ADVANCE = function(F){"""

patch("G.__HFL_ADVANCE = function(F){", DEFS, 'A1 integrity defs')

# ------------------------------------------------- F-06 RELEASE closes deals
patch(
    "yrs: rec.yrs || 0});\n      rec.released = true;",
    "yrs: rec.yrs || 0});\n      rec.released = true;\n"
    "      if (G.__HFL_CLOSEDEAL) G.__HFL_CLOSEDEAL(st, pk.playerId, pk.teamId, 'retire');",
    'A2 RELEASE closedeal')

# ------------------------------------------------- F-07 CUTDOWN closes deals
patch(
    "var keep = [];\n  for (i=0;i<league.picks.length;i++) if (!drop[league.picks[i].id]) keep.push(league.picks[i]);",
    "var keep = [];\n  var st0 = G.__HFL_CAREER;\n"
    "  for (i=0;i<league.picks.length;i++){\n"
    "    var pk0 = league.picks[i];\n"
    "    if (!drop[pk0.id]) { keep.push(pk0); continue; }\n"
    "    if (st0 && G.__HFL_CLOSEDEAL) G.__HFL_CLOSEDEAL(st0, pk0.playerId, pk0.teamId, 'cut');\n"
    "  }",
    'A3 CUTDOWN closedeal')

# ------------------------------------------------- F-08 SIGNALL stale deals
patch(
    "if (st.deals[pk.playerId]) continue;",
    "var d0 = st.deals[pk.playerId];\n"
    "    if (d0 && d0.team === pk.teamId) continue;      // already under contract here\n"
    "    if (d0) delete st.deals[pk.playerId];           // stale deal from an unclosed path — re-sign fresh below",
    'A4 SIGNALL mismatch')

# ------------------------------------------- F-03 annual class + class mode
patch(
    re.escape("var klass = G.__HFL_CLASS_OF(calendarYear);") + r"\s*" +
    re.escape("if (!klass.length) return {picked:[], undrafted:[], year:calendarYear};"),
    "var klass = G.__HFL_CLASS_OF(calendarYear);\n"
    "  var _kmode = 'historical';\n"
    "  if (!klass.length && G.__HFL_GENCLASS) { klass = G.__HFL_GENCLASS(league, calendarYear); _kmode = 'generated'; }\n"
    "  else if (klass.length > 500) _kmode = 'historical-oversize';\n"
    "  var _ksize = klass.length;\n"
    "  if (!klass.length) return {picked:[], undrafted:[], year:calendarYear, mode:'empty', classSize:0};",
    'A5 class mode + genclass fallback', regex=True)

patch(
    "return {picked: picked, undrafted: avail, year: calendarYear}",
    "return {picked: picked, undrafted: avail, year: calendarYear, mode: _kmode, classSize: _ksize}",
    'A6 rookie draft return mode')

# --------------------------------------- bug-C hygiene: third calendar site
patch(
    "var thisClass = G.__HFL_STARTYEAR ? (G.__HFL_STARTYEAR + year) : null;",
    "var y0c = G.__HFL_LEAGUE_YEAR0 ? G.__HFL_LEAGUE_YEAR0(league) : G.__HFL_STARTYEAR;\n"
    "  var thisClass = y0c ? (y0c + year) : null;",
    'A7 thisClass league-scoped')

# --------------------------- ADVANCE: migration + transaction flag at entry
patch(
    "var st = G.__HFL_CAREER_LOAD(league.id);\n  var year = season.year || 1;",
    "var st = G.__HFL_CAREER_LOAD(league.id);\n"
    "  try {\n"
    "    var mig = G.__HFL_MIGRATE_BOOK(league, st);\n"
    "    if (mig) { G.__HFL_LAST_MIGRATION = mig;\n"
    "      if (mig.orphans || mig.retargeted || mig.created) console.warn('hfl contract book migrated to v67:', JSON.stringify(mig)); }\n"
    "  } catch(e) { console.warn('book migration failed', e); }\n"
    "  var year = season.year || 1;\n"
    "  G.__HFL_TXN = 1;   // suppress mid-offseason career saves; the commit block writes once",
    'A8 migration + txn open')

# ------------------------------------------- ERRS collector after entry row
patch(
    "var entry = {year: year, champion: team ? team.name : (cid || null), championId: cid || null};",
    "var entry = {year: year, champion: team ? team.name : (cid || null), championId: cid || null};\n"
    "  var ERRS = [];\n"
    "  function _stagefail(stage, e){\n"
    "    ERRS.push({stage: stage, error: String(e && e.message || e)});\n"
    "    try { console.warn('offseason stage failed: ' + stage, e); } catch(_e){}\n"
    "  }",
    'A9 ERRS collector')

# ---------------------------------------------- wrap the two bare stages
patch(
    "var retired = G.__HFL_AGE_ALL(league);",
    "var retired = [];\n  try { retired = G.__HFL_AGE_ALL(league); } catch(e) { _stagefail('age', e); }",
    'A10 wrap AGE_ALL')
patch(
    "var released = G.__HFL_RELEASE(league);",
    "var released = [];\n  try { released = G.__HFL_RELEASE(league); } catch(e) { _stagefail('release', e); }",
    'A11 wrap RELEASE')

# ---------------------------------------------- convert the nine catches
patch("try { entry.dupes = G.__HFL_DEDUPE(league); } catch(e) {}",
      "try { entry.dupes = G.__HFL_DEDUPE(league); } catch(e) { _stagefail('dedupe', e); }",
      'A12 dedupe1')
patch("try { entry.fired = G.__HFL_GM_REVIEW(league, season, year); } catch(e) {}",
      "try { entry.fired = G.__HFL_GM_REVIEW(league, season, year); } catch(e) { _stagefail('gm-review', e); }",
      'A13 gm review')
patch("catch(e) { console.warn('free agency failed', e); }",
      "catch(e) { _stagefail('free-agency', e); }", 'A14 free agency')
patch("catch(e) { console.warn('trades failed', e); }",
      "catch(e) { _stagefail('trades', e); }", 'A15 trades')
patch("catch(e) { console.warn('replenish failed', e); }",
      "catch(e) { _stagefail('replenish', e); }", 'A16 replenish')
patch(
    re.escape("G.__HFL_SIGNALL(league, function(p){ return G.__HFL_RATEOF(p, G.__HFL_QFRAW); },\n      function(p){ return G.__HFL_GRP(p); });\n  } catch(e) {}"),
    "G.__HFL_SIGNALL(league, function(p){ return G.__HFL_RATEOF(p, G.__HFL_QFRAW); },\n      function(p){ return G.__HFL_GRP(p); });\n  } catch(e) { _stagefail('signall', e); }",
    'A17 signall', regex=True)
patch("catch(e) { console.warn('cutdown failed', e); }",
      "catch(e) { _stagefail('cutdown', e); }", 'A18 cutdown')
patch("catch(e) { console.warn('cap compliance failed', e); }",
      "catch(e) { _stagefail('cap-compliance', e); }", 'A19 comply')
patch(
    re.escape("if (d2) G.__HFL_REPLENISH(league, season, year,\n      function(p){ return G.__HFL_RATEOF(p, G.__HFL_QFRAW); },\n      function(p){ return G.__HFL_GRP(p); });\n  } catch(e) {}"),
    "if (d2) G.__HFL_REPLENISH(league, season, year,\n      function(p){ return G.__HFL_RATEOF(p, G.__HFL_QFRAW); },\n      function(p){ return G.__HFL_GRP(p); });\n  } catch(e) { _stagefail('dedupe-final', e); }",
    'A20 dedupe2', regex=True)

# -------------------------------------- class mode into the history entry
patch(
    "entry.klass = filled.klass;",
    "entry.klass = filled.klass;\n"
    "  try {\n"
    "    if (G.__HFL_LAST_ROOKIES) {\n"
    "      entry.klassMode = G.__HFL_LAST_ROOKIES.mode || null;\n"
    "      entry.classSize = G.__HFL_LAST_ROOKIES.classSize || 0;\n"
    "    }\n"
    "  } catch(e) {}",
    'A21 entry class mode')

# ------------------------------- the gate + ordered commit replace the tail
OLD_TAIL = """  st.year = year + 1;
  G.__HFL_CAREER_SAVE();

  // COMMIT THE LEAGUE. Everything above — releases, signings, the rookie
  // class's new player rows, trades, cap cuts — lived only in memory until
  // now. Without this the whole offseason is lost on the next load and the
  // franchise silently replays its opening roster forever.
  try { if (typeof au === 'function') au(); } catch(e) { console.warn('league commit failed', e); }

  F.dg(year + 1);
  return {ok:true, year: year + 1, retired: retired, entry: entry};
};"""

NEW_TAIL = """  // ---- THE GATE. ok:true must mean the entire offseason committed. -------
  if (ERRS.length){
    G.__HFL_TXN = 0;
    G.__HFL_LAST_ADVANCE_ERRORS = ERRS;
    return {ok:false, stage: ERRS[0].stage, errors: ERRS, year: year,
            reason: 'Offseason stage failed: ' + ERRS[0].stage};
  }
  var audit = null;
  try { audit = G.__HFL_LEDGER_AUDIT(league, st); }
  catch(e) { G.__HFL_TXN = 0; return {ok:false, stage:'ledger-audit', errors:[String(e && e.message || e)], year: year, reason:'Ledger audit threw.'}; }
  if (!audit.ok){
    G.__HFL_TXN = 0;
    G.__HFL_LAST_ADVANCE_ERRORS = audit.errors;
    return {ok:false, stage: 'ledger', errors: audit.errors, year: year,
            reason: 'Contract ledger failed audit: ' + audit.errors.join('; ')};
  }
  entry.ledger = {deals: audit.deals, picks: audit.picks};

  // ---- ORDERED COMMIT: league first, then career, then the next season. --
  st.year = year + 1;
  G.__HFL_TXN = 0;
  try { if (typeof au === 'function') au(); }
  catch(e) { st.year = year; return {ok:false, stage:'commit', errors:[String(e && e.message || e)], year: year, reason:'League commit failed.'}; }
  G.__HFL_CAREER_SAVE();

  F.dg(year + 1);
  return {ok:true, year: year + 1, retired: retired, entry: entry, audit: audit};
};"""

patch(OLD_TAIL, NEW_TAIL, 'A22 gate + ordered commit')

# ------------------------------- CAREER_SAVE honors the transaction flag
patch(
    re.escape("G.__HFL_CAREER_SAVE = function"),
    "G.__HFL_CAREER_SAVE = function", 'A23 career save exists', regex=True)
m = re.search(r"G\.__HFL_CAREER_SAVE = function\s*\(\)\s*\{", html)
assert m, 'A23b career save head shape'
html = html[:m.end()] + "\n  if (G.__HFL_TXN) return;   // v67: the advance commit block writes once, at the end\n" + html[m.end():]
applied.append('A23b txn suppress')


# --------------- F-06b: REPLENISH's make-room release also closes the deal
patch(
    "league.picks.splice(vidx,1);\n          delete taken[vict.id];",
    "league.picks.splice(vidx,1);\n"
    "          if (st && G.__HFL_CLOSEDEAL) G.__HFL_CLOSEDEAL(st, vict.id, ft.id, 'cut');\n"
    "          delete taken[vict.id];",
    'A25 make-room closedeal')

# ------------------------------------------------------------- build stamp
patch("G.__HFL_BUILD = 'v66';", "G.__HFL_BUILD = 'v67';", 'A24 stamp')

open(DST, 'w').write(html)
print(f'wrote {DST} ({len(html)} chars), {len(applied)} patches:')
for a in applied: print('  ', a)
