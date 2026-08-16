// franchise.mjs — v65 franchise runner with the FIXED season handshake.
//
// THE FIX (why the old harness failed): og() replaces Q with a shallow
// clone on every store notify — `Q&&={...Q}` — and dg() itself calls og()
// before returning. So the season object dg() returns is ALREADY STALE at
// return, and setting status on it mutates a dead copy while lg() reports
// 'regular' forever. Rule: NEVER hold a season reference. Re-read F.lg()
// from the store immediately before every read/mutation, and let the
// engine set status itself by actually playing the season (Tg/Eg/jg/kg).
//
// Every advance asserts ok:true. Pool must grow ~370/season or we fail
// loudly — no more logging a healthy 53 while nothing enters the league.
//
// Usage: NODE_PATH=/home/claude/.npm-global/lib/node_modules node franchise.mjs
// Env: BUDGET (seconds of season work, default 200), TARGET (default 25)

import http from 'http';
import fs from 'fs';
import path from 'path';
import { chromium } from '/home/claude/.npm-global/lib/node_modules/playwright/index.mjs';

const DIR = '/home/claude/hfl';
const PORT = 8123;
const PROFILE = path.join(DIR, 'profile');
const OUT = path.join(DIR, 'franchise-report.jsonl');
const BUDGET = (parseInt(process.env.BUDGET || '200', 10)) * 1000;
const TARGET = parseInt(process.env.TARGET || '25', 10);
const T0 = Date.now();

// ---- tiny static server (lives only for this call) ----
const server = http.createServer((req, res) => {
  const f = path.join(DIR, req.url === '/' ? 'hfl-v67-test.html' : req.url.slice(1));
  fs.readFile(f, (err, data) => {
    if (err) { res.writeHead(404); res.end('nope'); return; }
    res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
    res.end(data);
  });
});
await new Promise(r => server.listen(PORT, '127.0.0.1', r));

const ctx = await chromium.launchPersistentContext(PROFILE, {
  headless: true,
  viewport: { width: 430, height: 900 },
});
// start year must exist BEFORE the module script reads it
await ctx.addInitScript(() => {
  try { localStorage.setItem('hfl.startyear', '2004'); } catch (e) {}
});

const page = ctx.pages()[0] || await ctx.newPage();
page.on('pageerror', e => console.log('PAGEERROR', String(e).slice(0, 200)));

function die(msg) { throw new Error('FAIL ' + msg); }
async function cleanup(code) {
  // NEVER close gracefully: playwright's close sequence tears the leveldb log
  // mid-shutdown and chromium's paranoid recovery then NUKES the whole DB.
  // A hard kill leaves a crash-consistent log that recovers cleanly.
  try {
    const proc = ctx.browser() ? ctx.browser().process() : null;
    if (proc) proc.kill('SIGKILL');
  } catch (e) {}
  server.close();
  process.exit(code);
}

try {
await page.goto(`http://127.0.0.1:${PORT}/`, { waitUntil: 'domcontentloaded' });
await page.waitForSelector('#root', { timeout: 30000 });
await page.waitForFunction(
  () => globalThis.__HFL_TIMELINE && globalThis.__HFL_F && globalThis.__HFL_F.J,
  null, { timeout: 60000 },
);
await page.waitForFunction(
  () => document.querySelector('#root') && document.querySelector('#root').children.length > 0,
  null, { timeout: 60000 },
);

// ---- bridge sanity: the capture must have grabbed HFL's functions, not React's ----
const sanity = await page.evaluate(() => {
  const F = globalThis.__HFL_F;
  const has = (fn, frag) => { try { return String(fn).includes(frag); } catch (e) { return false; } };
  return {
    vu: has(F.vu, 'teamCount===32'),
    Fu: has(F.Fu, 'autoDraft'),
    Lu: has(F.Lu, 'pu('),
    dg: has(F.dg, 'usedFillerRosters'),
    lg: has(F.lg, 'sg()'),
    Tg: has(F.Tg, 'homeScore'),
    jg: has(F.jg, 'playoffs'),
    hh: has(F.hh, 'divisionId'),
    timeline: Array.isArray(globalThis.__HFL_TIMELINE) ? globalThis.__HFL_TIMELINE.length
      : Object.keys(globalThis.__HFL_TIMELINE || {}).length,
    startyear: globalThis.__HFL_STARTYEAR,
    build: globalThis.__HFL_BUILD,
  };
});
console.log('SANITY', JSON.stringify(sanity));
for (const k of ['vu', 'Fu', 'Lu', 'dg', 'lg', 'Tg', 'jg', 'hh']) {
  if (!sanity[k]) die(`bridge captured the wrong ${k}`);
}
if (sanity.startyear !== 2004) die(`STARTYEAR ${sanity.startyear} — init script did not land`);

// ---- state probe (re-reads the store; nothing is cached page-side) ----
const probe = () => page.evaluate(() => {
  const F = globalThis.__HFL_F; const G = globalThis;
  const L = F.J(); const s = F.lg();
  const st = L ? G.__HFL_CAREER_LOAD(L.id) : null;
  return {
    hasLeague: !!L,
    complete: L ? !!L.complete : false,
    picks: L ? L.picks.length : 0,
    teams: L ? L.teams.length : 0,
    pool: L ? L.players.length : 0,
    deals: st && st.deals ? Object.keys(st.deals).length : 0,
    careerYear: st ? st.year : null,
    season: s ? { year: s.year, status: s.status, week: s.currentWeek, weeks: s.weeks } : null,
    hflStartYear: L ? L.hflStartYear : null,
  };
});

let st = await probe();
console.log('STATE', JSON.stringify(st));

// batch-boundary persistence check: what did the last batch leave behind?
let lastLine = null;
if (fs.existsSync(OUT)) {
  const lines = fs.readFileSync(OUT, 'utf8').trim().split('\n').filter(Boolean);
  if (lines.length) lastLine = JSON.parse(lines[lines.length - 1]);
}
const doneYears = new Set();
if (fs.existsSync(OUT)) for (const l of fs.readFileSync(OUT, 'utf8').trim().split('\n').filter(Boolean)) doneYears.add(JSON.parse(l).year);
if (st.hasLeague && st.careerYear > 1) {
  const hist = await page.evaluate(() => {
    const F = globalThis.__HFL_F; const G = globalThis;
    const s = G.__HFL_CAREER_LOAD(F.J().id);
    return (s.history || []).map(h => ({ year: h.year, champion: h.champion,
      mvp: h.mvp ? h.mvp.name : null, retired: h.retired, klass: h.klass,
      trades: h.trades || 0, capCuts: h.capCuts || 0 }));
  });
  for (const h of hist.sort((a, b) => a.year - b.year)) {
    if (!doneYears.has(h.year) && h.year < st.careerYear) {
      fs.appendFileSync(OUT, JSON.stringify({ ...h, reconstructed: true }) + '\n');
      doneYears.add(h.year);
      console.log(`backfilled season ${h.year} from career history`);
    }
  }
}
if (lastLine && st.hasLeague) {
  if (st.pool !== lastLine.poolAfter) {
    die(`PERSISTENCE: pool ${st.pool} on reload, last batch ended at ${lastLine.poolAfter}`);
  }
  console.log(`PERSIST OK pool ${st.pool} careerYear ${st.careerYear}`);
}

// ---- create league + initial snake draft, once ----
if (!st.hasLeague) {
  console.log('creating 32-club 2004 franchise league…');
  const created = await page.evaluate(() => {
    const F = globalThis.__HFL_F;
    globalThis.__HFL_STARTYEAR = 2004;
    const L = F.vu({
      teamCount: 32, slot: 'random', humanTeamName: 'Sunset Park',
      leagueName: 'HFL v65 Franchise Report', identityMode: true,
      seed: Date.now(), firstFranchiseId: 'random',
    });
    return { id: L.id, hflStartYear: L.hflStartYear, pool: L.players.length,
      rounds: L.totalRounds, teams: L.teams.length };
  });
  console.log('LEAGUE', JSON.stringify(created));
  if (created.hflStartYear !== 2004) die('league did not capture hflStartYear 2004');

  // full-auto draft including the human club — the sanctioned Finish-draft override
  await page.evaluate(() => {
    const F = globalThis.__HFL_F;
    globalThis.__HFL_FINISH_ALLOW = true;
    F.Fu();       // autoDraft='full' + first Lu() burst
  });
  let guard = 0;
  while (guard++ < 60) {
    const p = await page.evaluate(() => {
      const F = globalThis.__HFL_F;
      globalThis.__HFL_FINISH_ALLOW = true;
      F.Lu(150);
      const L = F.J();
      return { picks: L.picks.length, complete: !!L.complete };
    });
    if (p.complete) { console.log(`draft complete at ${p.picks} picks`); break; }
    if (guard % 5 === 0) console.log(`  drafting… ${p.picks}`);
  }
  await page.evaluate(() => { globalThis.__HFL_FINISH_ALLOW = false; });
  st = await probe();
  console.log('POST-DRAFT', JSON.stringify(st));
  if (!st.complete) die('draft never completed');
  if (st.picks !== st.teams * 53) console.log(`WARN picks ${st.picks} != ${st.teams * 53}`);
}

// prime __HFL_QFRAW once per page load — offseason ratings depend on it
await page.evaluate(() => {
  const F = globalThis.__HFL_F;
  const L = F.J();
  if (L && L.players.length) { try { F.$f(L.players[0]); } catch (e) {} }
  return !!globalThis.__HFL_QFRAW;
});

// make sure a season exists (ADVANCE creates the next one itself; only
// season 1 after a fresh draft needs an explicit dg)
st = await probe();
if (!st.season) {
  await page.evaluate(() => { globalThis.__HFL_F.dg(1); });
  st = await probe();
  console.log('SEASON CREATED', JSON.stringify(st.season));
}

// ---- season loop ----
const seasonsDone = () => {
  if (!fs.existsSync(OUT)) return 0;
  return fs.readFileSync(OUT, 'utf8').trim().split('\n').filter(Boolean).length;
};

while (seasonsDone() < TARGET && (Date.now() - T0) < BUDGET) {
  const before = await probe();
  const yr = before.season.year;
  console.log(new Date().toISOString().slice(11,19) + ` season ${yr}: status ${before.season.status} week ${before.season.week}/${before.season.weeks} pool ${before.pool}`);

  // regular season — one week per evaluate; ALWAYS re-read lg() page-side
  let wguard = 0;
  while (wguard++ < 40) {
    const r = await page.evaluate(() => {
      const F = globalThis.__HFL_F;
      const s = F.lg();                       // fresh read, never cached
      if (!s || s.status !== 'regular') return { status: s ? s.status : null };
      F.Tg();                                 // play current week
      F.Eg();                                 // advance week / seed bracket
      const s2 = F.lg();
      return { status: s2.status, week: s2.currentWeek };
    });
    if (r.status !== 'regular') break;
  }
  // playoffs
  let pguard = 0;
  while (pguard++ < 12) {
    const r = await page.evaluate(() => {
      const F = globalThis.__HFL_F;
      const s = F.lg();
      if (!s || s.status !== 'playoffs') return { status: s ? s.status : null };
      F.jg();                                 // one round; kg() completes when final played
      return { status: F.lg().status };
    });
    if (r.status !== 'playoffs') break;
  }

  // the store must say complete — no manual status writes, no stale copies
  const done = await probe();
  if (!done.season || done.season.status !== 'complete') {
    die(`season ${yr} never completed: ${JSON.stringify(done.season)}`);
  }

  // collect season metrics + ADVANCE, assert everything
  const res = await page.evaluate(() => {
    const F = globalThis.__HFL_F; const G = globalThis;
    const L = F.J(); const s = F.lg();
    const st = G.__HFL_CAREER_LOAD(L.id);
    const poolBefore = L.players.length;
    const human = L.teams.find(t => t.isHuman);
    const table = F.hh(L.teams, s.alignment, s.schedule);
    const hrow = table.find(r => r.teamId === human.id) || {};
    const wins = table.map(r => r.w);
    let ptsFor = 0; let games = 0;
    for (const ts of Object.values(s.teamStats)) { ptsFor += ts.pointsFor || 0; games += ts.games || 0; }
    const champRow = L.teams.find(t => t.id === s.champion);
    const dealsBefore = st.deals ? Object.keys(st.deals).length : 0;
    // human payroll against the cap
    let payroll = 0;
    if (st.deals) for (const d of Object.values(st.deals)) if (d.team === human.id) payroll += d.aav || 0;
    const cap = G.__HFL_CAP ? G.__HFL_CAP(s.year) : null;

    const adv = G.__HFL_ADVANCE(G.__HFL_APP);

    const L2 = F.J(); const s2 = F.lg();
    const st2 = G.__HFL_CAREER_LOAD(L2.id);
    return {
      year: s.year,
      champion: champRow ? champRow.name : s.champion,
      championId: s.champion,
      mvp: adv.entry && adv.entry.mvp ? adv.entry.mvp.name : null,
      humanName: human.name, humanW: hrow.w, humanL: hrow.l,
      bestW: Math.max(...wins), worstW: Math.min(...wins),
      ptsPerTeamGame: games ? +(ptsFor / games).toFixed(2) : null,
      poolBefore, poolAfter: L2.players.length,
      dealsBefore, dealsAfter: st2.deals ? Object.keys(st2.deals).length : 0,
      humanPayroll: +payroll.toFixed(1), cap: cap ? +cap.toFixed(1) : null,
      retired: adv.entry ? adv.entry.retired : null,
      klass: adv.entry ? adv.entry.klass : null,
      klassMode: adv.entry ? (adv.entry.klassMode || null) : null,
      classSize: adv.entry ? (adv.entry.classSize || 0) : 0,
      audit: adv.audit || null,
      trades: adv.entry ? (adv.entry.trades || 0) : 0,
      capCuts: adv.entry ? (adv.entry.capCuts || 0) : 0,
      fired: adv.entry ? (adv.entry.fired || 0) : 0,
      advOk: adv.ok === true, advReason: adv.reason || null,
      nextYear: s2 ? s2.year : null, nextStatus: s2 ? s2.status : null,
      careerYear: st2.year,
    };
  });

  // ---- the assertions the old harness skipped ----
  if (!res.advOk) die(`ADVANCE refused at season ${yr}: ${res.advReason}`);
  if (res.nextYear !== yr + 1) die(`year did not move: season says ${res.nextYear} after advancing ${yr}`);
  if (res.careerYear !== yr + 1) die(`career year ${res.careerYear} out of step with season year ${res.nextYear}`);
  const grew = res.poolAfter - res.poolBefore;
  // v67: every year has an explicit class. Historical classes pass at any
  // size but must materialize fully; generated classes are exactly 372.
  if (!res.klassMode || res.klassMode === 'empty') die(`season ${yr}: no rookie class (mode ${res.klassMode})`);
  if (res.klassMode === 'generated') {
    if (res.classSize !== 372 || grew !== 372) die(`season ${yr}: generated class ${res.classSize}, grew ${grew}`);
  } else {
    if (res.classSize <= 0 || grew !== res.classSize) die(`season ${yr}: ${res.klassMode} class ${res.classSize} but pool grew ${grew}`);
  }
  if (!res.audit || !res.audit.ok) die(`season ${yr}: ledger audit failed: ${JSON.stringify(res.audit)}`);
  if (res.audit.deals !== res.audit.picks) die(`season ${yr}: deals ${res.audit.deals} != picks ${res.audit.picks}`);
  if (grew > 500) console.log(`  WARN class of ${cal} is ${grew} men — the documented 2016 debut artifact`);

  const dur = await page.evaluate(() => new Promise(resolve => {
    try {
      const q = indexedDB.open('hfl', 1);
      q.onsuccess = () => {
        const rq = q.result.transaction('kv', 'readonly').objectStore('kv').get('hfl.season.v1');
        rq.onsuccess = () => { const v = rq.result; q.result.close();
          try { const p = JSON.parse(v); resolve({ year: p.year, status: p.status }); }
          catch (e) { resolve({ year: null }); } };
        rq.onerror = () => { q.result.close(); resolve({ year: 'readerr' }); };
      };
      q.onerror = () => resolve({ year: 'openerr' });
    } catch (e) { resolve({ year: 'sync' }); }
  }));
  if (dur.year !== yr + 1) die(`durability: IDB season says ${JSON.stringify(dur)} after advancing ${yr}`);
  fs.appendFileSync(OUT, JSON.stringify(res) + '\n');
  console.log(`  ${yr}: ${res.champion} champ | ${res.humanName} ${res.humanW}-${res.humanL} | pts ${res.ptsPerTeamGame} | pool +${grew} -> ${res.poolAfter} | trades ${res.trades} | ledger ${res.audit.deals}/${res.audit.picks} | ${res.klassMode} ${res.classSize} | MVP ${res.mvp}`);

  // ---- renderer heap resets: five seasons of gamebook churn OOMs the tab.
  // page.reload() drops the JS heap, keeps browser + IndexedDB alive, and
  // reload persistence is a proven regression on this build.
  const heap = await page.evaluate(() => (performance.memory ? Math.round(performance.memory.usedJSHeapSize / 1048576) : -1));
  console.log(`    heap ${heap}MB after season ${yr}`);
  if (yr % 3 === 0 && yr < TARGET) {
    await page.reload({ waitUntil: 'domcontentloaded' });
    await page.waitForFunction(() => globalThis.__HFL_F && globalThis.__HFL_F.J &&
      document.querySelector('#root') && document.querySelector('#root').children.length > 0, null, { timeout: 90000 });
    await page.evaluate(() => {
      const F = globalThis.__HFL_F;
      globalThis.__HFL_STARTYEAR = 2004;
      globalThis.__HFL_FINISH_ALLOW = true;
      const L = F.J();
      if (L && L.players && L.players.length) { try { F.$f(L.players[0]); } catch (e) {} }
    });
    const back = await probe();
    if (!back.hasLeague || !back.season || back.season.year !== yr + 1) die(`reload at season ${yr} lost state: ${JSON.stringify(back)}`);
    const heap2 = await page.evaluate(() => (performance.memory ? Math.round(performance.memory.usedJSHeapSize / 1048576) : -1));
    console.log(`    renderer reset: heap ${heap}MB -> ${heap2}MB, season ${back.season.year} ${back.season.status} intact`);
  }
}

console.log(`run done: ${seasonsDone()}/${TARGET} seasons, ${((Date.now() - T0) / 1000).toFixed(0)}s`);
await cleanup(0);
} catch (e) {
  console.log(String(e && e.message || e));
  await cleanup(1);
}
