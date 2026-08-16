#!/usr/bin/env python3
"""hfl-storagefix-patch.py — v65 -> v66

THE BUG (persistence bug E, the last of the silent-franchise-loss family):
The storage adapter's boot hydration aa() migrates every localStorage key
starting with 'hfl.' into IndexedDB AND DELETES IT FROM localStorage — but
the prelude stores (hfl.career.v1:<lid>, hfl.gm, hfl.shadow, hfl.dblteam,
hfl.rushmatch, hfl.tiercaps, hfl.poolmode, hfl.startyear) read and write
RAW localStorage and never look in IndexedDB. So each of those stores is
eaten exactly once — on the first boot after it was written:

  - the CAREER STATE (year, contracts, histories) resets to year 1
  - every GM in the league silently regenerates
  - shadow/double/rusher directives and setup toggles wipe

Measured: play N seasons, close, reopen -> careerYear 1, deals 0, while the
league (IDB-backed) still shows its committed roster. This is why the
reload-per-season harness loop saw the pool pinned at 3,882: every reload
restarted the career clock, so ADVANCE re-ran year 1 forever.

THE FIX, three parts:
 1. aa() keeps the localStorage->IDB COPY (it rescues old saves) but no
    longer DELETES the localStorage originals, so raw readers keep working.
 2. The adapter is exposed as globalThis.__HFL_KV so prelude code that runs
    after boot can use the durable store.
 3. CAREER_LOAD/SAVE go through __HFL_KV (IndexedDB — no 5MB localStorage
    quota for a blob that grows every season), reading KV first and falling
    back to localStorage so both pre-fix saves and already-eaten (migrated)
    careers are recovered.
Plus: na() gains an onerror warn so a failing IDB write is never silent again.

Every anchor is asserted to appear exactly once before replacement.
"""
import sys

SRC = sys.argv[1] if len(sys.argv) > 1 else 'hfl-v65.html'
DST = sys.argv[2] if len(sys.argv) > 2 else 'hfl-v66.html'

html = open(SRC).read()
PATCHES = []

def patch(anchor, replacement):
    PATCHES.append((anchor, replacement))

# 1. migration keeps localStorage originals
patch(
    'if(e.length)for(let n of e)try{t.removeItem(n)}catch{}',
    '/* v66: keep localStorage originals — prelude stores read them raw */',
)

# 2. expose the adapter
patch(
    'ua=!1,da={getItem(e){',
    'ua=!1,da=globalThis.__HFL_KV={getItem(e){',
)

# 3a. career load: KV first (recovers migrated blobs), localStorage fallback
patch(
    'var raw = localStorage.getItem(G.__HFL_CAREER_KEY(lid));',
    'var raw = null;\n'
    '  try { if (G.__HFL_KV) raw = G.__HFL_KV.getItem(G.__HFL_CAREER_KEY(lid)); } catch(e) {}\n'
    '  if (raw == null) { try { raw = localStorage.getItem(G.__HFL_CAREER_KEY(lid)); } catch(e) {} }',
)

# 3b. career save: durable KV write (falls back to localStorage if KV absent)
patch(
    'try { localStorage.setItem(G.__HFL_CAREER_KEY(st._lid), JSON.stringify(st)); } catch(e) {}',
    'try { (G.__HFL_KV || localStorage).setItem(G.__HFL_CAREER_KEY(st._lid), JSON.stringify(st)); } catch(e) {}',
)

# 4. IDB writes are never silent
patch(
    'function na(e,t){if(la)try{la.transaction(sa,`readwrite`).objectStore(sa).put(t,e)}catch{}}',
    'function na(e,t){if(la)try{let _q=la.transaction(sa,`readwrite`).objectStore(sa).put(t,e);'
    '_q.onerror=()=>{try{console.warn(`hfl kv write failed`,e,String(_q.error))}catch(_e){}}}catch(_e){'
    'try{console.warn(`hfl kv write threw`,e,String(_e))}catch(_x){}}}',
)


# 6. QA: the franchise-eligibility check predates snake/identity mode, where
#    picks legitimately have franchiseId null — make it mode-aware so 38/38
#    stays meaningful (still strict in franchise-locked mode).
patch(
    't.push($(`Franchise + side eligibility`,s===0,s===0?`all picks legal`:`${s} illegal`))',
    'let _snake=!!(globalThis.__HFL_SNAKE&&globalThis.__HFL_SNAKE());'
    't.push($(`Franchise + side eligibility`,_snake||s===0,'
    '_snake?`snake mode: franchise lock n/a`:(s===0?`all picks legal`:`${s} illegal`)))',
)

# 7. build stamp
patch("G.__HFL_BUILD = 'v65';", "G.__HFL_BUILD = 'v66';")

for anchor, rep in PATCHES:
    n = html.count(anchor)
    assert n == 1, f'anchor x{n}, must be 1: {anchor[:70]!r}'
    html = html.replace(anchor, rep)

open(DST, 'w').write(html)
print(f'wrote {DST} ({len(html)} chars), {len(PATCHES)} patches applied')
