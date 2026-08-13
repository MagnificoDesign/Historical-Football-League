import json, re, statistics as st
from maplib import norm, ENGINE_WEIGHTS

P=[p for p in json.load(open('peaks.json')) if p['cov']>=0.93]   # full-schema seasons only
print('peaks kept at cov>=0.93:',len(P))

# --- id backfill ONLY where career spans are compatible (kills the father/son merge)
byname={}
for p in P: byname.setdefault(norm(p['name']),[]).append(p)
merged={}
for nm,rows in byname.items():
    ided=[r for r in rows if r['pfr_id']]
    idset={r['pfr_id'] for r in ided}
    for r in rows:
        pid=r['pfr_id']
        if not pid and len(idset)==1:
            cand=ided[0]
            # only inherit if the seasons overlap or touch — never bridge a 12-year gap
            if not (r['last']<cand['first']-2 or r['first']>cand['last']+2):
                pid=cand['pfr_id']
        key=pid or ('NAME:%s:%d'%(nm,r['first']//6))
        q=merged.get(key)
        if q is None or r['eng']>q['eng']:
            if q:
                r['first']=min(r['first'],q['first']); r['last']=max(r['last'],q['last'])
                r['seasons']+=q['seasons']
                a=[v for v in (r.get('bestAV'),q.get('bestAV')) if v is not None]; r['bestAV']=max(a) if a else None
            r['pfr_id']=pid; merged[key]=r
        else:
            q['first']=min(q['first'],r['first']); q['last']=max(q['last'],r['last']); q['seasons']+=r['seasons']
            a=[v for v in (q.get('bestAV'),r.get('bestAV')) if v is not None]; q['bestAV']=max(a) if a else None
P=list(merged.values())

# --- name cleanup: prefer a properly capitalized, spaced variant
def pretty(n):
    if ' ' in n and n[:1].isupper(): return n
    s=re.sub(r'(?<=[a-z])(?=[A-Z])',' ',n)
    return s.title() if s==s.lower() or ' ' not in s else s
for p in P: p['name']=pretty(p['name'])

print('unique players:',len(P),'| name-only',sum(1 for p in P if not p['pfr_id']))

TARGET=[(0.10,58),(0.50,72),(0.90,86),(0.99,93),(1.00,97)]
def fit(v):
    v=sorted(v); n=len(v)
    return [(v[min(n-1,int(q*(n-1)))],t) for q,t in TARGET]
def curve(x,pts):
    if x<=pts[0][0]: return pts[0][1]+(x-pts[0][0])*0.5
    for (x0,y0),(x1,y1) in zip(pts,pts[1:]):
        if x<=x1:
            t=0 if x1==x0 else (x-x0)/(x1-x0); return y0+t*(y1-y0)
    return pts[-1][1]
for grp in ENGINE_WEIGHTS:
    sel=[p for p in P if p['group']==grp]
    if not sel: continue
    pts=fit([p['eng'] for p in sel])
    for p in sel: p['rating']=round(max(40,min(99,curve(p['eng'],pts))),1)

avs=[p['bestAV'] for p in P if p.get('bestAV') is not None]
hi=sorted(avs)[int(len(avs)*0.97)] if avs else 20
for p in P:
    av=p.get('bestAV')
    if av is None: continue
    p['rating']=round(max(40,min(99,p['rating']+(min(1.0,av/max(1,hi))-(p['rating']-58)/39)*7.0)),1)

json.dump(P,open('players_modern.json','w'))
print('wrote players_modern.json\n')
for grp in ENGINE_WEIGHTS:
    v=sorted(p['rating'] for p in P if p['group']==grp)
    print('  %-8s n=%5d  p10 %.0f p50 %.0f p90 %.0f max %.0f'%(grp,len(v),v[len(v)//10],v[len(v)//2],v[int(len(v)*.9)],v[-1]))
print('\n=== TOP 8 BY GROUP ===')
for grp in ENGINE_WEIGHTS:
    print('\n--- %s ---'%grp)
    for p in sorted([x for x in P if x['group']==grp],key=lambda x:-x['rating'])[:8]:
        print('   %-24s %-4s %.0f   peak %d   span %d-%d   AV %s'%(p['name'],p['pos'],p['rating'],p['year'],p['first'],p['last'],int(p['bestAV']) if p.get('bestAV') is not None else '-'))
