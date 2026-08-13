#!/usr/bin/env python3
"""SHADOW COVERAGE: five slots instead of one.

Nick: "the CB shadowing, we need 5 slots? Not just 1?" — correct. A nickel
defence puts five defensive backs on the field against four or five eligible
receivers, so a single assignment only ever governed one matchup and the
engine's automatic map decided the rest.

  __HFL_SHADOW[teamId] is now {pairs:[{cb,wr},...]} (old single-pair saves are
  migrated on read), __HFL_SETSHADOW(teamId, index, cb, wr) writes one slot,
  and __HFL_APPLYSHADOW walks the list in order.

Each pair still SWAPS rather than overrides — the man your corner leaves is
picked up by whoever had the receiver. Assign all five and you have effectively
called the whole coverage yourself, which is the point; assign one or two and
the engine still sorts out the rest.
"""
import sys, io
SRC='hfl-v20.html'; OUT='hfl-v21.html'
html=io.open(SRC,encoding='utf-8').read()
def sub(old,new,label):
    n=html.count(old)
    if n!=1: sys.exit(f'ANCHOR {label}: expected 1, found {n}')
    return html.replace(old,new,1)

OLD_CORE = """G.__HFL_SETSHADOW = function(teamId, cbId, wrId){
  if (!teamId) return;
  if (!cbId || !wrId) delete G.__HFL_SHADOW[teamId];
  else G.__HFL_SHADOW[teamId] = {cb: cbId, wr: wrId};
  try { localStorage.setItem('hfl.shadow', JSON.stringify(G.__HFL_SHADOW)); } catch(e) {}
};"""
NEW_CORE = """G.__HFL_SHADOW_SLOTS = 5;
// old saves held a single {cb,wr}; read them as a one-element list
G.__HFL_PAIRS = function(teamId){
  var s = G.__HFL_SHADOW[teamId];
  if (!s) return [];
  if (s.pairs) return s.pairs;
  if (s.cb && s.wr) return [{cb:s.cb, wr:s.wr}];
  return [];
};
G.__HFL_SETSHADOW = function(teamId, index, cbId, wrId){
  if (!teamId) return;
  var pairs = G.__HFL_PAIRS(teamId).slice();
  if (index == null) {                       // clear everything
    delete G.__HFL_SHADOW[teamId];
  } else {
    while (pairs.length <= index) pairs.push({cb:null, wr:null});
    pairs[index] = {cb: cbId || null, wr: wrId || null};
    pairs = pairs.filter(function(p){ return p.cb && p.wr; });
    if (pairs.length) G.__HFL_SHADOW[teamId] = {pairs: pairs};
    else delete G.__HFL_SHADOW[teamId];
  }
  try { localStorage.setItem('hfl.shadow', JSON.stringify(G.__HFL_SHADOW)); } catch(e) {}
};"""
html = sub(OLD_CORE, NEW_CORE, 'shadow state')

OLD_APPLY = """    var s = defTeam && G.__HFL_SHADOW[defTeam.id];
    if (!s) return map;
    var cb = null, wr = null, i;
    for (i=0;i<defenders.length;i++) if (defenders[i].id === s.cb) cb = defenders[i];
    for (i=0;i<receivers.length;i++) if (receivers[i].id === s.wr) wr = receivers[i];
    if (!cb || !wr) return map;            // either man is off the field this snap
    var current = map.get(wr.id);
    if (current && current.id === cb.id) return map;   // already on him
    // whoever the shadow corner was covering inherits the man he leaves
    var vacated = null;
    map.forEach(function(d, rid){ if (d && d.id === cb.id) vacated = rid; });
    map.set(wr.id, cb);
    if (vacated && current) map.set(vacated, current);
    return map;"""
NEW_APPLY = """    if (!defTeam) return map;
    var pairs = G.__HFL_PAIRS(defTeam.id);
    if (!pairs.length) return map;
    for (var p=0;p<pairs.length && p<G.__HFL_SHADOW_SLOTS;p++){
      var s = pairs[p];
      var cb = null, wr = null, i;
      for (i=0;i<defenders.length;i++) if (defenders[i].id === s.cb) cb = defenders[i];
      for (i=0;i<receivers.length;i++) if (receivers[i].id === s.wr) wr = receivers[i];
      if (!cb || !wr) continue;            // either man is off the field this snap
      var current = map.get(wr.id);
      if (current && current.id === cb.id) continue;   // already on him
      // whoever this corner was covering inherits the man he leaves
      var vacated = null;
      map.forEach(function(d, rid){ if (d && d.id === cb.id) vacated = rid; });
      map.set(wr.id, cb);
      if (vacated && current) map.set(vacated, current);
    }
    return map;"""
html = sub(OLD_APPLY, NEW_APPLY, 'apply shadow')

io.open(OUT,'w',encoding='utf-8').write(html)
print(f'wrote {OUT} ({len(html)} chars)')

# ---------------------------------------------------------------- five rows
html2 = io.open(OUT, encoding='utf-8').read()
def sub2(old, new, label):
    global html2
    n = html2.count(old)
    if n != 1: sys.exit(f'ANCHOR {label}: expected 1, found {n}')
    html2 = html2.replace(old, new, 1)

start = html2.find("var cur=(globalThis.__HFL_SHADOW||{})[mine.id]||{};")
end   = html2.find("})()),", start)
if start < 0 or end < 0: sys.exit('could not locate the shadow panel body')
OLD_BODY = html2[start:end]

NEW_BODY = r"""var pairs=globalThis.__HFL_PAIRS(mine.id);
var slots=globalThis.__HFL_SHADOW_SLOTS||5;
var set=function(i,cb,wr){globalThis.__HFL_SETSHADOW(mine.id,i,cb,wr);};
var row=function(i){
  var cur=pairs[i]||{};
  return (0,I.jsxs)(`div`,{className:`grid grid-cols-2 gap-2`,children:[
    (0,I.jsxs)(`select`,{"aria-label":`shadow corner `+i,defaultValue:cur.cb||``,
      onChange:function(ev){var box=ev.target.parentNode;var wrSel=box.querySelectorAll(`select`)[1];
        set(i,ev.target.value,wrSel&&wrSel.value?wrSel.value:null);},
      className:`w-full rounded-md border border-border bg-surface-2 px-2 py-1.5 text-xs`,
      children:[(0,I.jsx)(`option`,{value:``,children:`— corner —`}),
        cbs.map(function(p){return (0,I.jsx)(`option`,{value:p.id,children:p.name},p.id);})]}),
    (0,I.jsxs)(`select`,{"aria-label":`shadow receiver `+i,defaultValue:cur.wr||``,
      onChange:function(ev){var box=ev.target.parentNode;var cbSel=box.querySelectorAll(`select`)[0];
        set(i,cbSel&&cbSel.value?cbSel.value:null,ev.target.value);},
      className:`w-full rounded-md border border-border bg-surface-2 px-2 py-1.5 text-xs`,
      children:[(0,I.jsx)(`option`,{value:``,children:`— receiver —`}),
        wrs.map(function(p){return (0,I.jsx)(`option`,{value:p.id,children:p.name},p.id);})]})]},i);
};
var rows=[]; for(var ri=0;ri<slots;ri++) rows.push(row(ri));
return (0,I.jsxs)(`div`,{className:`mt-2 hfl-card p-2.5`,children:[
 (0,I.jsxs)(`div`,{className:`mb-1.5 flex items-baseline justify-between`,children:[
   (0,I.jsxs)(`p`,{className:`hfl-label`,children:[`Shadow · `+mine.abbr,
     pairs.length?(0,I.jsxs)(`span`,{className:`ml-1.5 text-primary`,children:[pairs.length,`/`,slots]}):null]}),
   pairs.length?(0,I.jsx)(`button`,{onClick:function(ev){set(null,null,null);
     try{var box=ev.target.closest(`.hfl-card`);box.querySelectorAll(`select`).forEach(function(el){el.value=``;});}catch(_e){}},
     className:`font-display text-[0.6rem] uppercase tracking-widest text-muted-foreground`,children:`Clear all`}):null]}),
 (0,I.jsx)(`div`,{className:`space-y-1.5`,children:rows}),
 (0,I.jsx)(`p`,{className:`mt-1.5 text-[0.66rem] leading-snug text-muted-foreground`,
   children:pairs.length?`Each pair travels together all game. The man a shadow corner leaves is picked up by whoever had the receiver.`
     :`Lock corners onto receivers — up to `+slots+`. Anyone you leave blank, the coaches sort out.`})]});
"""
sub2(OLD_BODY, NEW_BODY, 'shadow panel body')
io.open(OUT,'w',encoding='utf-8').write(html2)
print(f'panel rebuilt for {5} slots ({len(html2)} chars)')

