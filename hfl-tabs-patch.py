#!/usr/bin/env python3
"""POSITION TABS IN FOOTBALL ORDER.

Nick: "the order of tabs should be QB, RB, WR, TE, T, G, C, LB, CB, S, DL."

The board was tabbing by GROUP (WR/TE, OL, CB/S, DL/EDGE) in alphabetical
order, which is how the engine thinks and not how a scout does. In snake mode
the tabs are now true positions, in offence-then-defence order, filtered to the
ones actually on the board.

Grouped tabs stay for the 12-club all-time league, where the franchise pools
are small and splitting an eight-man OL group into T/G/C would leave tabs with
one name in them.
"""
import sys, io
SRC='hfl-v45.html'; OUT='hfl-v46.html'
html=io.open(SRC,encoding='utf-8').read()
def sub(old,new,label):
    n=html.count(old)
    if n!=1: sys.exit(f'ANCHOR {label}: expected 1, found {n}')
    return html.replace(old,new,1)

CORE = r"""
// ---- draft board tabs, in the order a scout reads them -----------------
G.__HFL_TABORDER = ['QB','RB','WR','TE','T','G','C','LB','CB','S','DL','K','P'];
// what a player's tab is: real positions, with the line collapsed sensibly
G.__HFL_TABOF = function(pos){
  if (pos === 'OT' || pos === 'LT' || pos === 'RT') return 'T';
  if (pos === 'LG' || pos === 'RG' || pos === 'OL') return 'G';
  if (pos === 'FB') return 'RB';
  if (pos === 'KR/PR') return 'WR';
  if (pos === 'LS') return 'C';
  if (pos === 'DE' || pos === 'DT' || pos === 'NT' || pos === 'EDGE') return 'DL';
  if (pos === 'FS' || pos === 'SS') return 'S';
  if (pos === 'ILB' || pos === 'OLB' || pos === 'MLB' || pos === 'ATH') return 'LB';
  return pos;
};
"""
html = sub("G.__HFL_HFA = 0.060;", CORE + "G.__HFL_HFA = 0.060;", 'tab map')

# the tab list, ordered the way Nick reads a board
html = sub("A=(0,F.useMemo)(()=>{let e=new Set;return k.forEach(t=>e.add($s(t.primaryPosition))),[...e].sort()},[k])",
           "A=(0,F.useMemo)(()=>{let snake=globalThis.__HFL_SNAKE&&globalThis.__HFL_SNAKE();"
           "let e=new Set;k.forEach(t=>e.add(snake?globalThis.__HFL_TABOF(t.primaryPosition):$s(t.primaryPosition)));"
           "return snake?globalThis.__HFL_TABORDER.filter(x=>e.has(x)):[...e].sort()},[k])",
           'tab order')

# and the filter has to match on the same key
html = sub("return k.filter(t=>(i===`ALL`||$s(t.primaryPosition)===i)&&",
           "return k.filter(t=>(i===`ALL`||((globalThis.__HFL_SNAKE&&globalThis.__HFL_SNAKE())"
           "?globalThis.__HFL_TABOF(t.primaryPosition):$s(t.primaryPosition))===i)&&",
           'tab filter')

io.open(OUT,'w',encoding='utf-8').write(html)
print(f'wrote {OUT} ({len(html)} chars)')
