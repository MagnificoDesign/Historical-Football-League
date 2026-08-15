#!/usr/bin/env python3
# hfl-simpick-patch.py — the runaway draft.
#
# CAUSE: __HFL_SNAKE() keys off __HFL_STARTYEAR, which is read ONCE at page
# load. With no start year (a fresh device, or the setup default), snake is
# off, Nu() lets auto-draft pick FOR the human, and one press of the button
# takes all 1,696 picks — the user's 53 included.
#
# FIX A: a 32-club draft never auto-picks for the human, start year or not.
# FIX B: the league records its own start year at creation, so the draft
#        format is a property of the league instead of a global that can
#        drift mid-session.
import sys

SRC = sys.argv[1] if len(sys.argv) > 1 else 'hfl-v49.html'
DST = sys.argv[2] if len(sys.argv) > 2 else 'hfl-v50.html'

s = open(SRC, encoding='utf-8').read()

def rep(anchor, new, label):
    n = s.count(anchor)
    assert n == 1, f'{label}: anchor appears {n} times, need exactly 1'
    print(f'  ok  {label}')
    return s.replace(anchor, new)

# A — league-scoped draft format, with a live localStorage fallback so a start
#     year chosen this session is never missed.
s = rep(
"""G.__HFL_SNAKE = function(){ return !!G.__HFL_STARTYEAR; };""",
"""G.__HFL_SNAKE = function(){
  try {
    var A = G.__HFL_APP, L = A && A.J && A.J();
    if (L && L.hflStartYear !== undefined) return !!L.hflStartYear;   // the league decides
  } catch(e) {}
  if (G.__HFL_STARTYEAR) return true;
  try { return !!localStorage.getItem('hfl.startyear'); } catch(e) { return false; }
};

// Which clubs run their own draft board. The human's is never auto-picked in a
// 32-club league: that draft is the whole point of the mode.
G.__HFL_NOAUTOHUMAN = function(league){
  return !!(league && league.teams && league.teams.length >= 32);
};

// The sim-to-my-pick button belongs to any 32-club draft, not just a snake.
G.__HFL_SIMBTN = function(league){
  if (G.__HFL_SNAKE && G.__HFL_SNAKE()) return true;
  return G.__HFL_NOAUTOHUMAN(league);
};""",
'A: league-scoped snake + helpers')

# B — stamp the start year onto the league at creation
s = rep(
"""complete:!1,autoDraft:`off`,qaLeague:e.qaLeague===!0}""",
"""complete:!1,autoDraft:`off`,qaLeague:e.qaLeague===!0,hflStartYear:(globalThis.__HFL_STARTYEAR||null)}""",
'B: stamp start year on the league')

# C — the auto-drafter stops at the human in any 32-club league.
#     The QA harness drives its own control club, so a QA league keeps the
#     plain rule — which also fixes the pre-existing stall where QA could not
#     complete a draft whenever a start year was set.
s = rep(
"""function Nu(e,t){if(globalThis.__HFL_SNAKE&&globalThis.__HFL_SNAKE())return !1;return e.autoDraft===`full`||e.autoDraft===`round`&&e.autoDraftRoundIndex===t}""",
"""function Nu(e,t){var _q=e&&e.qaLeague===!0;if(!_q&&globalThis.__HFL_SNAKE&&globalThis.__HFL_SNAKE())return !1;if(!_q&&globalThis.__HFL_NOAUTOHUMAN&&globalThis.__HFL_NOAUTOHUMAN(e))return !1;return e.autoDraft===`full`||e.autoDraft===`round`&&e.autoDraftRoundIndex===t}""",
'C: Nu blocks human auto-picks at 32 clubs (QA exempt)')

# D/E — the button and its label follow the same rule
s = rep(
"""children:(globalThis.__HFL_SNAKE&&globalThis.__HFL_SNAKE())?`Sim to my pick`:`Auto draft`}""",
"""children:(globalThis.__HFL_SIMBTN&&globalThis.__HFL_SIMBTN(e))?`Sim to my pick`:`Auto draft`}""",
'D: button label')

s = rep(
"""}):((globalThis.__HFL_SNAKE&&globalThis.__HFL_SNAKE())?(0,I.jsx)(`button`,{onClick:()=>{Fu();Iu();}""",
"""}):((globalThis.__HFL_SIMBTN&&globalThis.__HFL_SIMBTN(e))?(0,I.jsx)(`button`,{onClick:()=>{Fu();Iu();}""",
'E: button variant')

open(DST, 'w', encoding='utf-8').write(s)
print(f'wrote {DST} ({len(s):,} bytes)')
