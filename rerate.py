"""Re-rate the modern pool on EVIDENCE, then force a scarcity curve.

Principle: Madden supplies the attribute SHAPE. Real accomplishment supplies the
RANK. The rating is then assigned by rank against a deliberately steep curve, so
the number of stars is a design decision rather than a by-product of EA's scale.
"""
import json, math, statistics as st
from maplib import norm, ENGINE_WEIGHTS

P=json.load(open('players_modern.json'))
E=json.load(open('evidence.json')); HON=E['hon']; T100=E['t100']
honN={norm(k):v for k,v in HON.items()}
t100N={norm(k):v for k,v in T100.items()}

# ---------- 1. evidence score ----------
def z(vals):
    m=st.mean(vals); sd=st.pstdev(vals) or 1
    return lambda x:(x-m)/sd

for grp in ENGINE_WEIGHTS:
    sel=[p for p in P if p['group']==grp]
    if not sel: continue
    zm=z([p['eng'] for p in sel])
    avs=[p['bestAV'] for p in sel if p.get('bestAV') is not None]
    za=z(avs) if len(avs)>5 else (lambda x:0.0)
    for p in sel:
        k=norm(p['name'])
        h=honN.get(k) or {}
        # only credit honors whose span overlaps this player's career (guards vs collisions)
        if h and (h.get('to',0) < p['first']-3 or h.get('from',9999) > p['last']+3):
            h={}
        ap=h.get('ap',0); pb=h.get('pb',0); rings=h.get('rings',0)
        t=t100N.get(k) or {}
        # top-100 conviction: repeat selection matters far more than one appearance
        tscore=0.0
        if t:
            yrs=t.get('years',0); best=t.get('best',100)
            tscore=min(3.2, (yrs**0.72)*0.62 + max(0,(100-best))/100*1.5)
        av=p.get('bestAV')
        score = (zm(p['eng'])*1.00
                 + (za(av) if av is not None else -0.25)*1.35
                 + min(ap,8)*0.62
                 + min(pb,12)*0.20
                 + tscore
                 + min(rings,4)*0.10)
        p['ev']=round(score,3)
        p['_ap']=ap; p['_pb']=pb; p['_t100']=t.get('years',0)

# ---------- 2. scarcity curve ----------
# How many modern players (25 seasons) may occupy each band, TOTAL across all groups.
# Sized so a 32-club draft still has to fight over stars, and so the modern set does
# not swamp the all-time pool it will sit beside.
BANDS=[(99,99,1),(97,98,3),(95,96,7),(93,94,12),(90,92,26),
       (87,89,30),(85,86,18),(82,84,45),(79,81,80),(76,78,190),
       (73,75,420),(70,72,900),(66,69,2200),(60,65,4200),(45,59,99999)]
# distribute each band across position groups in proportion to real roster demand
DEMAND={'QB':.09,'RB':.09,'WR/TE':.24,'OL':.20,'DL/EDGE':.18,'LB':.10,'CB/S':.19}

ranked={g:sorted([p for p in P if p['group']==g], key=lambda x:-x['ev']) for g in ENGINE_WEIGHTS}
cursor={g:0 for g in ranked}
import random
for lo,hi,count in BANDS:
    for g,share in DEMAND.items():
        n=max(0,int(round(count*share)))
        lst=ranked[g]; i=cursor[g]
        take=lst[i:i+n]
        for j,p in enumerate(take):
            # spread inside the band, best at the top
            span=hi-lo
            p['rating']= hi - (span*(j/max(1,len(take)-1)) if len(take)>1 else 0)
            p['rating']=round(p['rating'],0)
        cursor[g]=i+len(take)
# anything left over
for g,lst in ranked.items():
    for p in lst[cursor[g]:]:
        p.setdefault('rating',50)

for p in P: p['rating']=int(max(45,min(99,p['rating'])))
json.dump(P,open('players_rated.json','w'))

# ---------- report ----------
print('TOTAL:',len(P))
bands=[(90,100),(85,90),(80,85),(75,80),(70,75),(0,70)]
for lo,hi in bands:
    n=sum(1 for p in P if lo<=p['rating']<hi)
    print('  %3d-%-3d %6d  (%.1f%%)'%(lo,hi-1,n,100*n/len(P)))
print()
print('=== TOP 12 OVERALL (all positions) ===')
for p in sorted(P,key=lambda x:(-x['rating'],-x['ev']))[:12]:
    print('  %2d  %-24s %-4s  AP %d  PB %2d  T100 %d  AV %s'%(
        p['rating'],p['name'],p['pos'],p['_ap'],p['_pb'],p['_t100'],
        int(p['bestAV']) if p.get('bestAV') is not None else '-'))
print()
for g in ENGINE_WEIGHTS:
    sel=sorted([p for p in P if p['group']==g],key=lambda x:-x['rating'])[:6]
    print('--- %s ---'%g)
    for p in sel:
        print('   %2d  %-22s %-4s  AP %d PB %2d T100 %d'%(p['rating'],p['name'],p['pos'],p['_ap'],p['_pb'],p['_t100']))
