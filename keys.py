import re
def kn(s):
    """normalize a header into a comparable key"""
    s = (s or '').lower()
    s = s.replace('accleration','acceleration').replace('accruacy','accuracy')
    return re.sub(r'[^a-z]', '', s)

# concept -> list of accepted normalized header spellings, best first
SYN = {
 'overall':      ['overall','overallrating','ovr','rating'],
 'position':     ['position','positionshortlabel','pos'],
 'team':         ['team','teamname'],
 'firstname':    ['firstname'], 'lastname':['lastname'], 'fullname':['fullname','name','playername'],
 'speed':        ['speed'], 'acceleration':['acceleration'], 'strength':['strength'],
 'agility':      ['agility'], 'awareness':['awareness'], 'jumping':['jumping'],
 'stamina':      ['stamina'], 'catching':['catching'], 'carrying':['carrying'],
 'tackle':       ['tackle','tackling'],
 'throwpower':   ['throwpower'],
 'accshort':     ['throwaccuracyshort','shortthrowaccuracy','throwaccuracy'],
 'accmid':       ['throwaccuracymid','mediumthrowaccuracy','throwaccuracymedium','throwaccuracy'],
 'accdeep':      ['throwaccuracydeep','deepthrowaccuracy','throwaccuracy'],
 'tup':          ['throwunderpressure'],
 'totr':         ['throwontherun','throwonrun'],
 'breaksack':    ['breaksack'],
 'playaction':   ['playaction'],
 'bcvision':     ['bcvision','ballcarriervision','bcvision'],
 'elusive':      ['elusiveness'], 'juke':['jukemove'], 'spin':['spinmove'],
 'truck':        ['trucking'], 'breaktackle':['breaktackle'], 'stiffarm':['stiffarm'],
 'changedir':    ['changeofdirection'],
 'rrshort':      ['shortrouterunning','routerunningshort'],
 'rrmid':        ['mediumrouterunning','midrouterunning','routerunningmid'],
 'rrdeep':       ['deeprouterunning','routerunningdeep'],
 'speccatch':    ['spectacularcatch'], 'cit':['catchintraffic'], 'release':['release'],
 'runblock':     ['runblock','runblocking'],
 'runblockpwr':  ['runblockpower','runblockingpower'],
 'runblockfin':  ['runblockfinesse','runblockingfinesse'],
 'passblock':    ['passblock','passblocking'],
 'passblockpwr': ['passblockpower','passblockingpower'],
 'passblockfin': ['passblockfinesse','passblockingfinesse'],
 'impactblock':  ['impactblocking','leadblock'],
 'powermoves':   ['powermoves','powermove'],
 'finessemoves': ['finessemoves','finessemove'],
 'blockshed':    ['blockshedding'],
 'playrec':      ['playrecognition'],
 'pursuit':      ['pursuit'],
 'hitpower':     ['hitpower'],
 'mancov':       ['mancoverage'],
 'zonecov':      ['zonecoverage'],
 'press':        ['press'],
}

def build_lookup(fieldnames):
    """map concept -> actual header present in this file"""
    have = {kn(f): f for f in fieldnames}
    out = {}
    for concept, spellings in SYN.items():
        for sp in spellings:
            if sp in have:
                out[concept] = have[sp]; break
    return out
