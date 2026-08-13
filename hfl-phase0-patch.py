#!/usr/bin/env python3
"""PHASE 0 — scoring calibration.

Three constant changes, each anchor asserted unique:
  RZ    0.50 -> 0.10   red-zone compression eased (it was choking scoring)
  STICK 0.76 -> 0.44   sticks defense relaxed (drives stall less between the 20s)
  BAND  0.26 -> 0.30   rubber band nudged, gently, to hold blowouts

Band deliberately kept LOW: at 0.50 it bought a smaller margin but cost talent
expression (corr(rating,wins) 0.465 -> 0.421, best rosters 9.5 -> 8.9 wins).
Stars mattering outranks margin cosmetics for a 25-year sim.
"""
import sys, io
SRC='hfl-v4.html'; OUT='hfl-v5.html'
html=io.open(SRC,encoding='utf-8').read()

def sub(old,new,label):
    n=html.count(old)
    if n!=1: sys.exit(f'ANCHOR {label}: expected 1, found {n}')
    return html.replace(old,new,1)

html=sub('G.__HFL_STICK = 0.76;','G.__HFL_STICK = 0.44;','stick')
html=sub('G.__HFL_BAND = 0.26;','G.__HFL_BAND = 0.30;','band')
html=sub('G.__HFL_RZ = 0.50;','G.__HFL_RZ = 0.10;','rz')

io.open(OUT,'w',encoding='utf-8').write(html)
print(f'wrote {OUT} ({len(html)} chars)')
