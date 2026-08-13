import csv, re
def norm(s):
    s=(s or '').lower(); s=re.sub(r"[.'\u2019`]",'',s)
    s=re.sub(r'\b(jr|sr|ii|iii|iv|v)\b','',s); return re.sub(r'[^a-z]','',s)
def g(r,*keys):
    for k in keys:
        v=r.get(k)
        if v not in (None,''):
            try: return float(v)
            except ValueError: pass
    return None
def blend(*pairs):
    n=d=0.0
    for v,w in pairs:
        if v is None: continue
        n+=v*w; d+=w
    return None if d==0 else n/d
ENGINE_WEIGHTS={
 'QB':{'processing':.18,'shortAccuracy':.14,'intermediateAccuracy':.14,'deepAccuracy':.12,'pressureHandling':.12,'armStrength':.10,'ballSecurity':.08,'scrambleCreation':.06},
 'RB':{'vision':.20,'elusiveness':.17,'power':.15,'longSpeed':.13,'hands':.10,'ballSecurity':.08,'routeCraft':.07,'passProtection':.06},
 'WR/TE':{'separation':.21,'hands':.19,'routeCraft':.16,'deepSpeed':.12,'contestedCatch':.12,'release':.09,'yac':.08,'runBlocking':.03},
 'OL':{'passSet':.24,'anchor':.19,'driveBlock':.16,'handTechnique':.12,'runBlocking':.10,'power':.09,'awareness':.06,'pullMobility':.04},
 'DL/EDGE':{'passRush':.26,'firstStep':.15,'power':.13,'blockShedding':.12,'runDefense':.12,'bend':.09,'motor':.07,'tackling':.06},
 'LB':{'tackling':.17,'diagnosis':.17,'runFit':.15,'coverage':.15,'range':.12,'blitz':.12,'awareness':.07,'discipline':.05},
 'CB/S':{'manCoverage':.24,'recovery':.18,'zoneCoverage':.15,'ballSkills':.13,'press':.10,'range':.09,'tackling':.06,'discipline':.05},
}
POSMAP={'QB':'QB','HB':'RB','RB':'RB','FB':'RB','WR':'WR/TE','TE':'WR/TE',
 'LT':'OL','LG':'OL','C':'OL','RG':'OL','RT':'OL','OL':'OL','OT':'OL','G':'OL',
 'LE':'DL/EDGE','RE':'DL/EDGE','DT':'DL/EDGE','DE':'DL/EDGE','DL':'DL/EDGE','EDGE':'DL/EDGE','NT':'DL/EDGE',
 'LOLB':'LB','ROLB':'LB','MLB':'LB','LB':'LB','ILB':'LB','OLB':'LB',
 'CB':'CB/S','FS':'CB/S','SS':'CB/S','S':'CB/S','DB':'CB/S','K':'K','P':'P'}
def to_engine(r,group):
    A=lambda *k: g(r,*k)
    awr,spd,acc,agi=A('Awareness'),A('Speed'),A('Acceleration'),A('Agility')
    str_,tkl=A('Strength'),A('Tackle')
    prec,purs=A('Play Recognition'),A('Pursuit')
    o={}
    if group=='QB':
        o={'processing':blend((awr,.6),(prec,.4)),'shortAccuracy':A('Short Throw Accuracy'),
           'intermediateAccuracy':A('Medium Throw Accuracy'),'deepAccuracy':A('Deep Throw Accruacy','Deep Throw Accuracy'),
           'pressureHandling':blend((A('Throw Under Pressure'),.7),(A('Break Sack'),.3)),
           'armStrength':A('Throw Power'),'ballSecurity':blend((A('Carrying'),.5),(awr,.5)),
           'scrambleCreation':blend((spd,.4),(acc,.3),(A('Throw On The Run'),.3))}
    elif group=='RB':
        o={'vision':A('BC Vision'),'elusiveness':blend((A('Elusiveness'),.5),(A('Juke Move'),.3),(A('Spin Move'),.2)),
           'power':blend((A('Trucking'),.5),(A('Break Tackle'),.3),(str_,.2)),'longSpeed':spd,
           'hands':A('Catching'),'ballSecurity':A('Carrying'),
           'routeCraft':blend((A('Short Route Running'),.5),(A('Medium Route Running'),.5)),'passProtection':A('Pass Block')}
    elif group=='WR/TE':
        o={'separation':blend((A('Short Route Running'),.35),(A('Medium Route Running'),.35),(agi,.3)),
           'hands':A('Catching'),'routeCraft':blend((A('Medium Route Running'),.5),(A('Deep Route Running'),.5)),
           'deepSpeed':spd,'contestedCatch':blend((A('Spectacular Catch'),.5),(A('Catch in Traffic'),.5)),
           'release':A('Release'),'yac':blend((A('Elusiveness'),.4),(A('Break Tackle'),.3),(acc,.3)),
           'runBlocking':blend((A('Run Block'),.6),(A('Impact Blocking'),.4))}
    elif group=='OL':
        o={'passSet':blend((A('Pass Block'),.5),(A('Pass Block Finesse'),.5)),
           'anchor':blend((A('Pass Block Power'),.6),(str_,.4)),
           'driveBlock':blend((A('Run Block Power'),.6),(A('Impact Blocking'),.4)),
           'handTechnique':blend((A('Pass Block Finesse'),.6),(awr,.4)),
           'runBlocking':blend((A('Run Block'),.6),(A('Run Block Finesse'),.4)),
           'power':str_,'awareness':awr,'pullMobility':blend((acc,.5),(agi,.5))}
    elif group=='DL/EDGE':
        o={'passRush':blend((A('Finesse Moves'),.5),(A('Power Moves'),.5)),
           'firstStep':blend((acc,.6),(A('Finesse Moves'),.4)),
           'power':blend((A('Power Moves'),.6),(str_,.4)),'blockShedding':A('Block Shedding'),
           'runDefense':blend((A('Block Shedding'),.5),(tkl,.3),(prec,.2)),
           'bend':blend((agi,.6),(A('Finesse Moves'),.4)),
           'motor':blend((purs,.6),(A('Stamina'),.4)),'tackling':tkl}
    elif group=='LB':
        o={'tackling':tkl,'diagnosis':blend((prec,.7),(awr,.3)),
           'runFit':blend((A('Block Shedding'),.5),(prec,.3),(tkl,.2)),
           'coverage':blend((A('Zone Coverage'),.6),(A('Man Coverage'),.4)),
           'range':blend((spd,.5),(purs,.5)),
           'blitz':blend((A('Power Moves'),.4),(A('Finesse Moves'),.4),(acc,.2)),
           'awareness':awr,'discipline':blend((awr,.6),(prec,.4))}
    elif group=='CB/S':
        o={'manCoverage':A('Man Coverage'),'recovery':blend((spd,.5),(acc,.3),(agi,.2)),
           'zoneCoverage':A('Zone Coverage'),
           'ballSkills':blend((A('Catching'),.5),(A('Jumping'),.25),(prec,.25)),
           'press':A('Press'),'range':blend((spd,.5),(purs,.5)),
           'tackling':tkl,'discipline':blend((awr,.6),(prec,.4))}
    return {k:v for k,v in o.items() if v is not None}
def overall(attrs,group):
    w=ENGINE_WEIGHTS.get(group)
    if not w: return None
    n=d=0.0
    for k,wt in w.items():
        if k in attrs: n+=attrs[k]*wt; d+=wt
    return None if d==0 else n/d
