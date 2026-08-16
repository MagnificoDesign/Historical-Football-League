// v66 career-persistence test. Fresh profile: draft, two FAST advances
// (dg -> set status on the STORE's season -> ADVANCE, asserting ok), close,
// reopen, assert careerYear/deals/pool all survived. On v65 this fails:
// careerYear resets to 1 and deals to 0 because boot migration eats the
// career key out of localStorage.
import http from 'http';
import fs from 'fs';
import path from 'path';
import { chromium } from '/home/claude/.npm-global/lib/node_modules/playwright/index.mjs';

const DIR = '/home/claude/hfl';
const PROFILE = path.join(DIR, 'profile-careertest');
fs.rmSync(PROFILE, { recursive: true, force: true });

const server = http.createServer((req, res) => {
  const BUNDLE = process.env.BUNDLE || 'hfl-v67-test.html';
  const f = path.join(DIR, req.url === '/' ? BUNDLE : req.url.slice(1));
  fs.readFile(f, (e, d) => { if (e) { res.writeHead(404); res.end(); } else { res.writeHead(200, {'Content-Type':'text/html'}); res.end(d); } });
});
await new Promise(r => server.listen(8124, '127.0.0.1', r));

async function open() {
  const ctx = await chromium.launchPersistentContext(PROFILE, { headless: true });
  await ctx.addInitScript(() => { try { localStorage.setItem('hfl.startyear', '2004'); } catch (e) {} });
  const page = ctx.pages()[0] || await ctx.newPage();
  page.on('console', m => { const t = m.text(); if (t.includes('hfl kv')) console.log('PAGE:', t.slice(0, 160)); });
  await page.goto('http://127.0.0.1:8124/', { waitUntil: 'domcontentloaded' });
  await page.waitForFunction(() => globalThis.__HFL_TIMELINE && globalThis.__HFL_F && globalThis.__HFL_F.J, null, { timeout: 60000 });
  await page.waitForFunction(() => document.querySelector('#root') && document.querySelector('#root').children.length > 0, null, { timeout: 60000 });
  return { ctx, page };
}


const drain = (pg) => pg.evaluate(() => new Promise(res => {
  try {
    const q = indexedDB.open('hfl', 1);
    q.onsuccess = () => {
      const rq = q.result.transaction('kv', 'readonly').objectStore('kv').get('hfl.league.v1');
      rq.onsuccess = () => { q.result.close(); res('drained, league in IDB: ' + (rq.result ? rq.result.length + ' chars' : 'MISSING')); };
      rq.onerror = () => { q.result.close(); res('drain err'); };
    };
    q.onerror = () => res('open err');
  } catch (e) { res('sync ' + e); }
}));

// ---- session 1: build + two fast advances ----
let { ctx, page } = await open();
console.log('S1 BOOT', JSON.stringify(await page.evaluate(() => ({ ua: globalThis.__HFL_F.ua, la: !!globalThis.__HFL_F.la, kv: !!globalThis.__HFL_KV }))));
await page.evaluate(() => {
  const F = globalThis.__HFL_F;
  globalThis.__HFL_STARTYEAR = 2004;
  F.vu({ teamCount: 32, slot: 'random', humanTeamName: 'Sunset Park',
    leagueName: 'careertest', identityMode: true, seed: 42 });
  globalThis.__HFL_FINISH_ALLOW = true; F.Fu();
});
let g = 0;
while (g++ < 40) {
  const p = await page.evaluate(() => { const F = globalThis.__HFL_F; globalThis.__HFL_FINISH_ALLOW = true; F.Lu(220); const L = F.J(); return !!L.complete; });
  if (p) break;
}
const s1 = await page.evaluate(() => {
  const F = globalThis.__HFL_F; const G = globalThis;
  globalThis.__HFL_FINISH_ALLOW = false;
  const L = F.J();
  try { F.$f(L.players[0]); } catch (e) {}
  const out = [];
  F.dg(1);
  for (let i = 0; i < 2; i++) {
    const s = F.lg();                 // the STORE's season — never a held copy
    s.status = 'complete';            // fast probe: skip the games
    const adv = G.__HFL_ADVANCE(G.__HFL_APP);
    if (!adv.ok) return { fail: 'advance refused: ' + adv.reason };
    out.push({ year: adv.year, klass: adv.entry.klass, retired: adv.entry.retired });
  }
  const st = G.__HFL_CAREER_LOAD(L.id);
  const audit = G.__HFL_LEDGER_AUDIT(F.J(), st);
  return { advances: out, careerYear: st.year, deals: Object.keys(st.deals || {}).length,
    pool: F.J().players.length, leagueId: L.id, audit };
});
console.log('SESSION 1', JSON.stringify(s1));
if (s1.fail) { console.log('FAIL'); process.exit(1); }
console.log('drain:', await drain(page));


// ---- session 2 (reload): what survived? ----
await page.reload({ waitUntil: 'domcontentloaded' });
await page.waitForFunction(() => globalThis.__HFL_TIMELINE && globalThis.__HFL_F && globalThis.__HFL_F.J, null, { timeout: 60000 });
await page.waitForFunction(() => document.querySelector('#root') && document.querySelector('#root').children.length > 0, null, { timeout: 60000 });
const s2 = await page.evaluate(() => {
  const F = globalThis.__HFL_F; const G = globalThis;
  const L = F.J();
  const st = L ? G.__HFL_CAREER_LOAD(L.id) : null;
  let lsCareer = null; try { lsCareer = !!localStorage.getItem('hfl.career.v1:' + L.id); } catch (e) {}
  let kvCareer = null; try { kvCareer = !!(G.__HFL_KV && G.__HFL_KV.getItem('hfl.career.v1:' + L.id)); } catch (e) {}
  const s = F.lg();
  return { careerYear: st ? st.year : null, deals: st && st.deals ? Object.keys(st.deals).length : 0,
    pool: L ? L.players.length : null, season: s ? { year: s.year, status: s.status } : null,
    lsCareer, kvCareer, gm: Object.keys(G.__HFL_GM || {}).length };
});
console.log('SESSION 2', JSON.stringify(s2));

const ledger = await page.evaluate(() => {
  const F = globalThis.__HFL_F; const G = globalThis;
  const L = F.J(); const st = G.__HFL_CAREER_LOAD(L.id);
  return G.__HFL_LEDGER_AUDIT(L, st);
});
console.log('S2 LEDGER', JSON.stringify(ledger));
const ok = s2.careerYear === 3 && s2.pool === s1.pool && s2.season && s2.season.year === 3
  && s1.audit.ok === true && s1.deals === 1696 && ledger.ok === true && ledger.deals === ledger.picks;
console.log(ok ? 'CAREER PERSISTENCE: PASS' : 'CAREER PERSISTENCE: FAIL');
await ctx.close(); server.close(); process.exit(ok ? 0 : 1);
