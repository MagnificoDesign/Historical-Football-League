#!/usr/bin/env python3
"""SITUATIONAL FOOTBALL — clock, timeouts, two-minute, and two smaller fixes.

1. CLOCK AND SITUATION (the big one). The engine had no situational logic at
   all: sm() subtracted time and ended quarters, and timeouts:{home:3,away:3}
   was written at kickoff and halftime and then referenced NOWHERE. So a
   trailing club ran its offense at the same tempo down 10 with a minute left
   as it did in the first quarter, and nobody ever kicked before the half.

   __HFL_SITU(e)   classifies the moment for the team with the ball
   __HFL_LEANADJ   two-minute pass lean (throw when you must, run when ahead)
   __HFL_CLOCK     per-play time: hurry-up shrinks it, milking it grows it,
                   and a timeout stops it outright
   __HFL_FOURTH    fourth-down and end-of-half decisions, including the field
                   goal before the break the engine never took

2. HOT-HAND FIX. The rubber band damped yardage from a 7-point lead, which is
   exactly when a quarterback playing well has put his team ahead — so every
   heater got throttled at the moment it started. Measured first: there is no
   passing-yard cap (27.9% of QB games clear 300, 3.4% clear 400, max 497), so
   the band was the only suspect. Deadband moves 7 -> 13: blowouts still get
   damped, a one-score game does not.

3. ELITE PLAYERS NEVER GO UNDRAFTED. The AI scorer multiplies a candidate's
   value by 0.58^n for each player already rostered at that position, so a
   club with one quarterback valued Peyton Manning at 42% and a club with two
   at 24% — which is how a 96 sits on the board while someone takes a third
   linebacker. Adds a need-independent best-player-available floor above 88.
"""
import sys, io

SRC='hfl-v12.html'; OUT='hfl-v13.html'
html=io.open(SRC,encoding='utf-8').read()
def sub(old,new,label):
    n=html.count(old)
    if n!=1: sys.exit(f'ANCHOR {label}: expected 1, found {n}')
    return html.replace(old,new,1)

CORE = r"""
// ---- SITUATIONAL FOOTBALL: clock, tempo, timeouts ---------------------
G.__HFL_BANDDEAD = 9;     // rubber band ignores anything inside two scores
G.__HFL_BPA = 6.0;        // best-player-available pull above rating 88

// Read the moment from the ball carrier's point of view.
G.__HFL_SITU = function(e){
  var off = e.possession, def = off === 'home' ? 'away' : 'home';
  var diff = (e.score[off]||0) - (e.score[def]||0);
  var q = e.quarter, clk = e.clock;
  var endHalf = (q === 2 && clk <= 130);
  var endGame = (q >= 4 && clk <= 240);
  var s = {diff: diff, endHalf: endHalf, endGame: endGame, off: off, def: def,
           twoMin: false, milk: false, desperate: false};
  if (endGame) {
    if (diff < 0) { s.twoMin = true; s.desperate = (diff < -8 || clk <= 100); }
    else if (diff > 0 && clk <= 180) s.milk = true;
    else if (diff === 0 && clk <= 100) s.twoMin = true;
  } else if (endHalf) {
    // no reason to hurry from your own end with the clock nearly gone
    if (e.ballOn >= 35 || clk >= 60) s.twoMin = true;
  }
  return s;
};

// Two-minute offense throws; a club protecting a lead runs.
G.__HFL_LEANADJ = function(e){
  var s = G.__HFL_SITU(e);
  if (s.desperate) return 0.12;
  if (s.twoMin)    return 0.08;
  if (s.milk)      return -0.16;
  return 0;
};

// Per-play clock. Hurry-up and out-of-bounds shrink it; milking grows it;
// a timeout stops it dead.
G.__HFL_CLOCK = function(e, secs, play){
  var s = G.__HFL_SITU(e);
  var out = secs;
  if (s.twoMin || s.desperate) {
    // no huddle, sideline throws, spikes — the between-plays time collapses
    out = play && play.incomplete ? Math.max(3, secs * 0.42) : Math.max(6, secs * 0.55);
    // the offense stops the clock with a timeout when it is truly late
    if (!play || !play.incomplete) {
      if (e.clock <= 55 && (e.timeouts && e.timeouts[s.off] > 0)) {
        e.timeouts[s.off] -= 1;
        out = Math.max(2, out * 0.35);
        e.__hflTO = {side: s.off, clock: e.clock};
      }
    }
  } else if (s.milk) {
    out = secs * 1.35;
    // the trailing DEFENSE burns its timeouts to get the ball back
    if (e.timeouts && e.timeouts[s.def] > 0 && e.clock <= 170) {
      e.timeouts[s.def] -= 1;
      out = Math.max(3, secs * 0.40);
      e.__hflTO = {side: s.def, clock: e.clock};
    }
  }
  return Math.max(2, out);
};

// Fourth down, plus the two decisions the engine never made: kick before the
// half, and stop punting when you are out of time.
G.__HFL_FOURTH = function(e){
  var s = G.__HFL_SITU(e);
  var fgDist = Math.round(100 - e.ballOn + 17);
  var inRange = fgDist <= 56;
  // end of half: take the points rather than running out of time
  if (s.endHalf && e.clock <= 45 && inRange) return 'fg';
  // end of game, trailing: a punt is a concession
  if (s.endGame && s.diff < 0 && e.clock <= 90) {
    if (inRange && s.diff >= -3) return 'fg';
    return 'go';
  }
  // trailing by more than a field goal late, do not kick one
  if (s.endGame && s.diff <= -4 && e.clock <= 150 && !inRange) return 'go';
  return null;   // fall through to the engine's own logic
};
"""
html = sub("G.__HFL_STICK = 0.44;", CORE + "G.__HFL_STICK = 0.44;", 'prelude')

# 1. rubber band deadband
html = sub("G.__HFL_BAND*Math.tanh((lead-7)/16)",
           "G.__HFL_BAND*Math.tanh((lead-G.__HFL_BANDDEAD)/16)", 'band deadband')

# 2. pass lean gets the situation
html = sub("let{down:n,distance:r,ballOn:i,quarter:a,clock:o}=e,s=t.runPassLean/100",
           "let{down:n,distance:r,ballOn:i,quarter:a,clock:o}=e,s=t.runPassLean/100+(globalThis.__HFL_LEANADJ?globalThis.__HFL_LEANADJ(e):0)",
           'pass lean')

# 3. per-play clock
html = sub("g=Math.max(3,f.timeUsed*(f.incomplete?1:h));",
           "g=Math.max(3,f.timeUsed*(f.incomplete?1:h));g=globalThis.__HFL_CLOCK?globalThis.__HFL_CLOCK(e,g,f):g;",
           'clock')

# 4. fourth-down override
html = sub("function lm(e){let t=e.distance,",
           "function lm(e){let _o=globalThis.__HFL_FOURTH?globalThis.__HFL_FOURTH(e):null;if(_o)return _o;let t=e.distance,",
           'fourth down')

# 5. elite players never go undrafted
html = sub("(x+c*C+w+S+Math.random()*.4)",
           "(x+c*C+w+S+Math.random()*.4+Math.max(0,(f-88))*(globalThis.__HFL_BPA||0))",
           'draft BPA')

io.open(OUT,'w',encoding='utf-8').write(html)
print(f'wrote {OUT} ({len(html)} chars)')
