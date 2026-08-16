// talentarc.mjs — v68 proof. One session, foreground:
//   draft -> 25 fast advances (into the generated era) -> sample the
//   generated-class talent arc by career-year cohort -> play season 26
//   in full and read pts/team-game + MVP.
import http from 'http';
import fs from 'fs';
import path from 'path';
import { chromium } from '/home/claude/.npm-global/lib/node_modules/playwright/index.mjs';

const DIR = '/home/claude/hfl';
const srv = http.createServer((q, r) => {
  const f = path.join(DIR, q.url === '/' ? 'hfl-v68-test.html' : q.url.slice(1));
  fs.readFile(f, (e, d) => { if (e) { r.writeHead(404); r.end(); } else { r.writeHead(200, {'Content-Type':'text/html'}); r.end(d); } });
});
await new Promise(r => srv.listen(8160, '127.0.0.1', r));
const ctx = await chromium.launchPersistentContext('/tmp/pf-arc-' + Date.now(), { headless: true });
const pg = ctx.pages()[0] || await ctx.newPage();
await pg.addInitScript(() => { try { localStorage.setItem('hfl.startyear', '2004'); } catch (e) {} });
await pg.goto('http://127.0.0.1:8160/', { waitUntil: 'domcontentloaded' });
await pg.waitForFunction(() => globalThis.__HFL_F && globalThis.__HFL_F.J && document.querySelector('#root').children.length > 0, null, { timeout: 60000 });

await pg.evaluate(() => {
  const F = globalThis.__HFL_F;
  globalThis.__HFL_STARTYEAR = 2004;
  F.vu({ teamCount: 32, slot: 'random', humanTeamName: 'Sunset Park', leagueName: 'arc', identityMode: true, seed: 68 });
  globalThis.__HFL_FINISH_ALLOW = true; F.Fu();
});
for (let g = 0; g < 40; g++) {
  const done = await pg.evaluate(() => { const F = globalThis.__HFL_F; globalThis.__HFL_FINISH_ALLOW = true; F.Lu(220); return !!F.J().complete; });
  if (done) break;
}
console.log('drafted');

// 25 fast advances, 5 per evaluate
for (let b = 0; b < 5; b++) {
  const out = await pg.evaluate(() => {
    const F = globalThis.__HFL_F; const G = globalThis;
    const res = [];
    for (let i = 0; i < 5; i++) {
      let s = F.lg(); if (!s) { F.dg(1); s = F.lg(); }
      s.status = 'complete';
      const adv = G.__HFL_ADVANCE(G.__HFL_APP);
      if (!adv.ok) { res.push('FAIL ' + (adv.reason || adv.stage)); break; }
      res.push(adv.year - 1 + ':' + (adv.entry.klassMode || '?') + (adv.audit.ok ? '' : ' LEDGER-FAIL'));
    }
    return res;
  });
  console.log(' ', out.join(' '));
  if (out.some(x => String(x).includes('FAIL'))) process.exit(1);
}

// talent arc sample: rostered generated-class players by career-year cohort
const arc = await pg.evaluate(() => {
  const F = globalThis.__HFL_F; const G = globalThis;
  const L = F.J();
  try { F.$f(L.players[0]); } catch (e) {}
  const st = G.__HFL_CAREER_LOAD(L.id);
  const byId = {}; for (const p of L.players) byId[p.id] = p;
  const eff = (p) => G.__HFL_RATEOF(p, G.__HFL_QFRAW);
  const cohorts = {};
  const stars = [];
  for (const pk of L.picks) {
    if (!pk.playerId.startsWith('p-gcls-')) continue;
    const p = byId[pk.playerId]; if (!p) continue;
    const rec = (st.players && st.players[p.id]) || { yrs: 0 };
    const e = eff(p);
    const c = cohorts[rec.yrs] = cohorts[rec.yrs] || { n: 0, sum: 0, max: -1, over83: 0, entryBreach: 0 };
    c.n++; c.sum += e; if (e > c.max) c.max = e; if (e > 83) c.over83++;
    if (rec.yrs === 0 && e > 83) c.entryBreach++;
    stars.push({ name: p.name, pos: p.primaryPosition, yrs: rec.yrs, peak: p.mr, rise: p.rise, eff: e, dev: Math.round((rec.dev || 0) * 10) / 10 });
  }
  stars.sort((a, b) => b.eff - a.eff);
  const out = {};
  for (const y of Object.keys(cohorts).sort((a, b) => a - b)) {
    const c = cohorts[y];
    out['yrs' + y] = `n=${c.n} avg=${(c.sum / c.n).toFixed(1)} max=${c.max} >83:${c.over83}` + (c.entryBreach ? ` ENTRY-BREACH:${c.entryBreach}` : '');
  }
  return { cohorts: out, top: stars.slice(0, 8), leagueTop: L.picks.map(pk => byId[pk.playerId]).filter(Boolean)
    .map(p => ({ n: p.name.slice(0, 18), e: eff(p), g: p.id.startsWith('p-gcls-') ? 'GEN' : 'real' }))
    .sort((a, b) => b.e - a.e).slice(0, 10) };
});
console.log('COHORTS', JSON.stringify(arc.cohorts, null, 1));
console.log('TOP GENERATED:');
for (const s of arc.top) console.log(`  ${s.name} ${s.pos} yrs${s.yrs} peak ${s.peak} rise ${s.rise} dev ${s.dev} -> eff ${s.eff}`);
console.log('LEAGUE TOP 10:', arc.leagueTop.map(x => `${x.n}(${x.g})${x.e}`).join(' | '));

// play season 26 in full — the harness's exact loop
let wguard = 0;
while (wguard++ < 40) {
  const r = await pg.evaluate(() => {
    const F = globalThis.__HFL_F;
    const s = F.lg();
    if (!s || s.status !== 'regular') return { status: s ? s.status : null };
    F.Tg(); F.Eg();
    return { status: F.lg().status };
  });
  if (r.status !== 'regular') break;
}
let pguard = 0;
while (pguard++ < 12) {
  const r = await pg.evaluate(() => {
    const F = globalThis.__HFL_F;
    const s = F.lg();
    if (!s || s.status !== 'playoffs') return { status: s ? s.status : null };
    F.jg();
    return { status: F.lg().status };
  });
  if (r.status !== 'playoffs') break;
}
const fin = await pg.evaluate(() => {
  const F = globalThis.__HFL_F; const G = globalThis;
  const L = F.J(); const s = F.lg();
  let ptsFor = 0, games = 0;
  for (const ts of Object.values(s.teamStats || {})) { ptsFor += ts.pointsFor || 0; games += ts.games || 0; }
  let mvp = null; try { const aw = F.Tv(L, s); if (aw && aw.mvp) mvp = aw.mvp.name + ' (' + (aw.mvp.pos || '?') + ')'; } catch (e) { mvp = 'Tv threw: ' + e.message; }
  const champRow = L.teams.find(t => t.id === s.champion);
  return { status: s.status, ptsPerTeamGame: games ? +(ptsFor / games).toFixed(2) : null,
    mvp, champ: champRow ? champRow.name : s.champion };
});
console.log('SEASON 26 (generated era):', JSON.stringify(fin));
const mvp26 = await pg.evaluate(() => {
  const G = globalThis;
  const adv = G.__HFL_ADVANCE(G.__HFL_APP);
  return { ok: adv.ok, mvp: adv.entry && adv.entry.mvp ? adv.entry.mvp.name + ' (' + adv.entry.mvp.pos + ')' : null,
    mode: adv.entry.klassMode, audit: adv.audit ? adv.audit.ok : null };
});
console.log('SEASON 26 MVP + advance:', JSON.stringify(mvp26));

// push fast to season 33 (7 more), then sample mature cohorts and play 34
for (let b = 0; b < 2; b++) {
  const out = await pg.evaluate((n) => {
    const F = globalThis.__HFL_F; const G = globalThis;
    const res = [];
    for (let i = 0; i < n; i++) {
      const s = F.lg(); s.status = 'complete';
      const adv = G.__HFL_ADVANCE(G.__HFL_APP);
      if (!adv.ok) { res.push('FAIL ' + (adv.reason || adv.stage)); break; }
      res.push(adv.year - 1 + (adv.audit.ok ? '' : ':LEDGER-FAIL'));
    }
    return res;
  }, b === 0 ? 4 : 3);
  console.log('  fast:', out.join(' '));
  if (out.some(x => String(x).includes('FAIL'))) process.exit(1);
}
const arc2 = await pg.evaluate(() => {
  const F = globalThis.__HFL_F; const G = globalThis;
  const L = F.J();
  try { F.$f(L.players[0]); } catch (e) {}
  const st = G.__HFL_CAREER_LOAD(L.id);
  const byId = {}; for (const p of L.players) byId[p.id] = p;
  const eff = (p) => G.__HFL_RATEOF(p, G.__HFL_QFRAW);
  const cohorts = {};
  let over88 = 0, over90 = 0;
  const all = [];
  for (const pk of L.picks) {
    if (!pk.playerId.startsWith('p-gcls-')) continue;
    const p = byId[pk.playerId]; if (!p) continue;
    const rec = (st.players && st.players[p.id]) || { yrs: 0 };
    const e = eff(p);
    const c = cohorts[rec.yrs] = cohorts[rec.yrs] || { n: 0, sum: 0, max: -1 };
    c.n++; c.sum += e; if (e > c.max) c.max = e;
    if (e >= 88) over88++; if (e >= 90) over90++;
    all.push({ name: p.name, pos: p.primaryPosition, yrs: rec.yrs, peak: p.mr, eff: e });
  }
  all.sort((a, b) => b.eff - a.eff);
  const out = {};
  for (const y of Object.keys(cohorts).sort((a, b) => a - b)) {
    const c = cohorts[y]; out['yrs' + y] = `n=${c.n} avg=${(c.sum / c.n).toFixed(1)} max=${c.max}`;
  }
  return { cohorts: out, over88, over90, top: all.slice(0, 6),
    genOnRoster: all.length, poolNow: L.players.length };
});
console.log('SEASON 33 COHORTS', JSON.stringify(arc2.cohorts));
console.log(`gen on rosters: ${arc2.genOnRoster}, eff>=88: ${arc2.over88}, >=90: ${arc2.over90}`);
for (const s of arc2.top) console.log(`  ${s.name} ${s.pos} yrs${s.yrs} peak ${s.peak} -> eff ${s.eff}`);

// play season 34 fully
wguard = 0;
while (wguard++ < 40) {
  const r = await pg.evaluate(() => {
    const F = globalThis.__HFL_F;
    const s = F.lg();
    if (!s || s.status !== 'regular') return { status: s ? s.status : null };
    F.Tg(); F.Eg();
    return { status: F.lg().status };
  });
  if (r.status !== 'regular') break;
}
pguard = 0;
while (pguard++ < 12) {
  const r = await pg.evaluate(() => {
    const F = globalThis.__HFL_F;
    const s = F.lg();
    if (!s || s.status !== 'playoffs') return { status: s ? s.status : null };
    F.jg();
    return { status: F.lg().status };
  });
  if (r.status !== 'playoffs') break;
}
const fin2 = await pg.evaluate(() => {
  const F = globalThis.__HFL_F; const G = globalThis;
  const L = F.J(); const s = F.lg();
  let ptsFor = 0, games = 0;
  for (const ts of Object.values(s.teamStats || {})) { ptsFor += ts.pointsFor || 0; games += ts.games || 0; }
  const adv = G.__HFL_ADVANCE(G.__HFL_APP);
  return { status: 'complete', ptsPerTeamGame: games ? +(ptsFor / games).toFixed(2) : null,
    mvp: adv.entry && adv.entry.mvp ? adv.entry.mvp.name + ' (' + adv.entry.mvp.pos + ')' : null,
    audit: adv.audit ? adv.audit.ok : null };
});
console.log('SEASON 34 (mature generated era):', JSON.stringify(fin2));
await ctx.close(); srv.close(); process.exit(0);
