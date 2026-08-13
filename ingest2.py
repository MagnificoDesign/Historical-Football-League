import csv, os, json, re, sys
import pyarrow.parquet as pq
sys.path.insert(0,'.')
from keys import build_lookup, kn
from maplib import norm, ENGINE_WEIGHTS, POSMAP

RAW='madden/data/madden/raw'; DS='madden/data/madden/dataset'

# dataset column -> concept (standardized parquet)
DSMAP={'overallrating':'overall','position':'position','team':'team','speed':'speed',
 'acceleration':'acceleration','strength':'strength','agility':'agility','awareness':'awareness',
 'jumping':'jumping','stamina':'stamina','catching':'catching','carrying':'carrying',
 'tackle':'tackle','throwpower':'throwpower','throwaccuracyshort':'accshort',
 'throwaccuracymid':'accmid','throwaccuracydeep':'accdeep','throwonrun':'totr',
 'playaction':'playaction','ballcarriervision':'bcvision','jukemove':'juke','spinmove':'spin',
 'trucking':'truck','stiffarm':'stiffarm','changeofdirection':'changedir',
 'shortrouterunning':'rrshort','midrouterunning':'rrmid','deeprouterunning':'rrdeep',
 'spectacularcatch':'speccatch','catchintraffic':'cit','release':'release',
 'runblocking':'runblock','passblocking':'passblock','impactblocking':'impactblock',
 'mancoverage':'mancov','zonecoverage':'zonecov','press':'press','playrecognition':'playrec',
 'pursuit':'pursuit','hitpower':'hitpower'}

def C(d,*names):
    for n in names:
        v=d.get(n)
        if v is not None: return v
    return None
def bl(*pairs):
    n=t=0.0
    for v,w in pairs:
        if v is None: continue
        n+=v*w; t+=w
    return None if t==0 else n/t

def engine_attrs(d, group):
    """d is a concept->float dict"""
    A=lambda *n: C(d,*n)
    awr,spd,acc,agi=A('awareness'),A('speed'),A('acceleration'),A('agility')
    st_,tk=A('strength'),A('tackle')
    prec,pur=A('playrec'),A('pursuit')
    pb,rb=A('passblock'),A('runblock')
    o={}
    if group=='QB':
        o={'processing':bl((awr,.6),(prec,.4)),'shortAccuracy':A('accshort'),
           'intermediateAccuracy':A('accmid'),'deepAccuracy':A('accdeep'),
           'pressureHandling':bl((A('tup'),.7),(A('breaksack'),.3)) or awr,
           'armStrength':A('throwpower'),'ballSecurity':bl((A('carrying'),.5),(awr,.5)),
           'scrambleCreation':bl((spd,.4),(acc,.3),(A('totr'),.3))}
    elif group=='RB':
        o={'vision':A('bcvision') or awr,'elusiveness':bl((A('elusive'),.5),(A('juke'),.3),(A('spin'),.2)) or A('changedir') or agi,
           'power':bl((A('truck'),.5),(A('breaktackle'),.3),(st_,.2)),'longSpeed':spd,
           'hands':A('catching'),'ballSecurity':A('carrying'),
           'routeCraft':bl((A('rrshort'),.5),(A('rrmid'),.5)) or A('catching'),'passProtection':pb}
    elif group=='WR/TE':
        o={'separation':bl((A('rrshort'),.35),(A('rrmid'),.35),(agi,.3)) or agi,
           'hands':A('catching'),'routeCraft':bl((A('rrmid'),.5),(A('rrdeep'),.5)) or A('catching'),
           'deepSpeed':spd,'contestedCatch':bl((A('speccatch'),.5),(A('cit'),.5)) or A('catching'),
           'release':A('release') or acc,'yac':bl((A('elusive'),.4),(A('breaktackle'),.3),(acc,.3)),
           'runBlocking':bl((rb,.6),(A('impactblock'),.4))}
    elif group=='OL':
        o={'passSet':bl((pb,.5),(A('passblockfin'),.5)),
           'anchor':bl((A('passblockpwr'),.6),(st_,.4)),
           'driveBlock':bl((A('runblockpwr'),.6),(A('impactblock'),.4)) or rb,
           'handTechnique':bl((A('passblockfin'),.6),(awr,.4)),
           'runBlocking':bl((rb,.6),(A('runblockfin'),.4)),
           'power':st_,'awareness':awr,'pullMobility':bl((acc,.5),(agi,.5))}
    elif group=='DL/EDGE':
        pr=bl((A('finessemoves'),.5),(A('powermoves'),.5))
        o={'passRush':pr or st_,'firstStep':bl((acc,.6),(A('finessemoves'),.4)),
           'power':bl((A('powermoves'),.6),(st_,.4)),'blockShedding':A('blockshed') or bl((st_,.5),(tk,.5)),
           'runDefense':bl((A('blockshed'),.5),(tk,.3),(prec,.2)) or tk,
           'bend':bl((agi,.6),(A('finessemoves'),.4)),'motor':bl((pur,.6),(A('stamina'),.4)),'tackling':tk}
    elif group=='LB':
        o={'tackling':tk,'diagnosis':bl((prec,.7),(awr,.3)) or awr,
           'runFit':bl((A('blockshed'),.5),(prec,.3),(tk,.2)) or tk,
           'coverage':bl((A('zonecov'),.6),(A('mancov'),.4)) or awr,
           'range':bl((spd,.5),(pur,.5)) or spd,
           'blitz':bl((A('powermoves'),.4),(A('finessemoves'),.4),(acc,.2)) or acc,
           'awareness':awr,'discipline':bl((awr,.6),(prec,.4))}
    elif group=='CB/S':
        o={'manCoverage':A('mancov') or awr,'recovery':bl((spd,.5),(acc,.3),(agi,.2)),
           'zoneCoverage':A('zonecov') or awr,
           'ballSkills':bl((A('catching'),.5),(A('jumping'),.25),(prec,.25)),
           'press':A('press') or st_,'range':bl((spd,.5),(pur,.5)) or spd,
           'tackling':tk,'discipline':bl((awr,.6),(prec,.4))}
    return {k:v for k,v in o.items() if v is not None}

def overall(a,g):
    w=ENGINE_WEIGHTS.get(g)
    if not w: return None
    n=d=0.0
    for k,wt in w.items():
        if k in a: n+=a[k]*wt; d+=wt
    return (n/d, d) if d>0 else None

peaks={}; ps=0; years=[]
for y in range(2001,2026):
    # ---- ids from dataset
    ids={}; dsrec={}
    dp=f'{DS}/{y}.parquet'
    if os.path.exists(dp):
        t=pq.read_table(dp).to_pydict()
        for i,nm in enumerate(t['fullname']):
            k=norm(nm)
            if not k: continue
            d={}
            for col,con in DSMAP.items():
                if col in t:
                    v=t[col][i]
                    if v is not None:
                        try: d[con]=float(v)
                        except (TypeError,ValueError): pass
            ids.setdefault(k,{'pfr_id':t['pfr_id'][i],'av':t['last_season_av'][i],
                              'pos':t['position'][i],'team':t['team'][i]})
            dsrec.setdefault(k,d)
    # ---- raw
    rawrec={}
    rp=f'{RAW}/{y}.csv'
    if os.path.exists(rp):
        with open(rp,encoding='utf-8',errors='replace') as f:
            rd=csv.DictReader(f); lu=build_lookup(rd.fieldnames or [])
            for r in rd:
                nm=(r.get(lu.get('fullname','')) or
                    ((r.get(lu.get('firstname','')) or '')+' '+(r.get(lu.get('lastname','')) or ''))).strip()
                k=norm(nm)
                if not k: continue
                d={}
                for con,col in lu.items():
                    if con in ('position','team','fullname','firstname','lastname'): continue
                    v=r.get(col)
                    if v not in (None,''):
                        try: d[con]=float(v)
                        except ValueError: pass
                d['_name']=nm
                d['_pos']=(r.get(lu.get('position','')) or '').strip().upper()
                d['_team']=(r.get(lu.get('team','')) or '').strip()
                rawrec[k]=d
    keys=set(rawrec)|set(dsrec)
    if not keys: continue
    kept=0
    for k in keys:
        d=dict(dsrec.get(k,{}))
        d.update({kk:vv for kk,vv in rawrec.get(k,{}).items() if not kk.startswith('_')})
        meta=ids.get(k,{})
        rr=rawrec.get(k,{})
        pos=(rr.get('_pos') or meta.get('pos') or '').upper()
        group=POSMAP.get(pos)
        if not group or group in ('K','P'): continue
        a=engine_attrs(d,group)
        res=overall(a,group)
        if not res: continue
        ov,cov=res
        if cov<0.55: continue          # need most of the weight covered
        ps+=1; kept+=1
        name=rr.get('_name') or k
        key=meta.get('pfr_id') or ('NAME:'+k)
        prev=peaks.get(key)
        rec={'key':key,'pfr_id':meta.get('pfr_id'),'name':name,'pos':pos,'group':group,
             'team':rr.get('_team') or meta.get('team'),'year':y,'eng':round(ov,2),
             'cov':round(cov,2),'attrs':{kk:round(vv,1) for kk,vv in a.items()},'av':meta.get('av')}
        if prev is None or ov>prev['eng']:
            rec['first']=min(y,prev['first']) if prev else y
            rec['last']=max(y,prev['last']) if prev else y
            rec['seasons']=(prev['seasons']+1) if prev else 1
            rec['bestAV']=max([v for v in (rec['av'],prev.get('bestAV') if prev else None) if v is not None],default=None)
            peaks[key]=rec
        else:
            prev['first']=min(prev['first'],y); prev['last']=max(prev['last'],y)
            prev['seasons']+=1
            if rec['av'] is not None:
                prev['bestAV']=rec['av'] if prev.get('bestAV') is None else max(prev['bestAV'],rec['av'])
    years.append(y)
    print(f'  {y}: {kept:5d} usable   (unique so far {len(peaks)})')

print('\nyears used:',len(years),'| player-seasons:',ps,'| unique players:',len(peaks))
print('name-only keys:',sum(1 for k in peaks if k.startswith('NAME:')))
json.dump(list(peaks.values()),open('peaks.json','w'))
for grp in ENGINE_WEIGHTS:
    v=sorted(p['eng'] for p in peaks.values() if p['group']==grp)
    if v: print('  %-8s n=%5d  p10 %.0f p50 %.0f p90 %.0f max %.0f'%(grp,len(v),v[len(v)//10],v[len(v)//2],v[int(len(v)*.9)],v[-1]))
