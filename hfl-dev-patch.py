#!/usr/bin/env python3
"""hfl-dev-patch.py — v67 -> v68. Created-player careers, uncapped.

Nick's rule: nobody ENTERS the league above ~83, but a created player's
CAREER is uncapped. In this engine the stored rating is the career peak and
the age curve approaches it from below, so v67's cap-at-83 accidentally
capped generated players' PEAKS — the whole generated era topped out at 83
(+5.5 field dev), scoring sagged to 18.9, and a fullback won MVP.

1. GENCLASS now assigns career PEAKS with a real class shape:
   one generational slot per class (88-94), a few stars (84-89), tapering
   exactly as before below that. ENTRY stays hard-capped at 83 via a
   per-player rise depth stamped on the row: rise = max(5.5, peak - 83).
2. AGECURVE reads that per-player rise; players without one keep the 5.5
   default, so every historical career is bit-identical.
3. The dev offset (situation-driven, ±5.5) was applied at game time but NOT
   at valuation time — a player who grew +5 played like it but was priced,
   drafted, traded, and cut like he never did. Valuation now sees dev too,
   same 30..99 clamp as the sim site.
"""
import re, sys

SRC = sys.argv[1] if len(sys.argv) > 1 else 'hfl-v67.html'
DST = sys.argv[2] if len(sys.argv) > 2 else 'hfl-v68.html'
html = open(SRC).read()
applied = []

def patch(anchor, replacement, name):
    global html
    n = html.count(anchor)
    assert n == 1, f'{name}: anchor x{n}'
    html = html.replace(anchor, replacement)
    applied.append(name)

# 1. per-player rise depth in the age curve (default preserves history)
patch(
    "delta = -5.5 * (1 - p / peak);",
    "var rise = (typeof player.rise === 'number') ? player.rise : 5.5;\n"
    "    delta = -rise * (1 - p / peak);",
    'A1 agecurve per-player rise')

# 2. valuation applies dev like the sim does (sim site text differs: has dev already)
patch(
    "r = Math.max(30, Math.min(99, Math.round(r + cr.delta)));",
    "r = Math.max(30, Math.min(99, Math.round(r + cr.delta + (cr.dev || 0))));",
    'A2 dev at valuation')

# 3. GENCLASS: peak distribution + entry cap via rise
OLD = """    var rating;
    if (i < 3) rating = 79 + Math.floor(rnd(1) * 5);
    else if (i < 12) rating = 74 + Math.floor(rnd(1) * 6);
    else if (i < 40) rating = 68 + Math.floor(rnd(1) * 7);
    else if (i < 120) rating = 60 + Math.floor(rnd(1) * 9);
    else rating = 50 + Math.floor(rnd(1) * 11);"""
NEW = """    // career PEAKS, class-shaped: one generational talent, a few stars,
    // then the same taper as before. Entry is capped separately below.
    var peakR;
    if (i < 1) peakR = 88 + Math.floor(rnd(1) * 7);
    else if (i < 4) peakR = 84 + Math.floor(rnd(1) * 6);
    else if (i < 12) peakR = 78 + Math.floor(rnd(1) * 7);
    else if (i < 40) peakR = 70 + Math.floor(rnd(1) * 9);
    else if (i < 120) peakR = 60 + Math.floor(rnd(1) * 11);
    else peakR = 50 + Math.floor(rnd(1) * 11);
    // nobody ENTERS above 83: a high peak deepens the climb instead
    var riseR = Math.max(5.5, peakR - 83);
    var rating = peakR;"""
patch(OLD, NEW, 'A3 genclass peak curve')

patch(
    "startYear: cal, endYear: cal + 3 + Math.floor(rnd(7) * 9) + (rating >= 76 ? 2 : 0),\n      attributes: attrs, mr: rating};",
    "startYear: cal, endYear: cal + 3 + Math.floor(rnd(7) * 9) + (rating >= 76 ? 2 : 0),\n      attributes: attrs, mr: rating, rise: riseR};",
    'A4 stamp rise on row')


# 4. the rookie's DRAFT season plays at his entry rating, not his peak:
#    seed the career record (yrs 0, full rise suppression) the moment he is
#    drafted, instead of waiting for his first offseason AGE_ALL.
patch(
    "at:Date.now(), rookie:true});",
    "at:Date.now(), rookie:true});\n"
    "      if (G.__HFL_CAREER && G.__HFL_CAREER.players && !G.__HFL_CAREER.players[best.id]) {\n"
    "        try {\n"
    "          var c0 = G.__HFL_AGECURVE(best, 0);\n"
    "          G.__HFL_CAREER.players[best.id] = {yrs: 0, retired: false, delta: c0.delta, len: c0.len};\n"
    "        } catch(e) {}\n"
    "      }",
    'A6 rookie entry seed')

patch("G.__HFL_BUILD = 'v67';", "G.__HFL_BUILD = 'v68';", 'A5 stamp')

open(DST, 'w').write(html)
print(f'wrote {DST} ({len(html)} chars), {len(applied)} patches: ' + ', '.join(applied))
