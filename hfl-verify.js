// VERIFY — does every feature we built actually do its job?
// Run with MODE=draft | game | franchise
import 'fake-indexeddb/auto';
import { JSDOM } from 'jsdom';
const dom=new JSDOM('<!doctype html><div id="root"></div>',{url:'http://localhost/'});
for(const k of ['window','document','navigator']){try{if(!(k in globalThis))globalThis[k]=dom.window[k];}catch(e){}}
const mem={}; globalThis.localStorage={getItem:k=>k in mem?mem[k]:null,setItem:(k,v)=>{mem[k]=String(v)},removeItem:k=>{delete mem[k]},clear:()=>{},key:()=>null,get length(){return 0}};
globalThis.sessionStorage=globalThis.localStorage;
try{ await import('./v26.instr.mjs'); }catch(e){}
const F=globalThis.__HFL; try{F.my();}catch(e){}
import zlib from 'zlib';

const results=[];
const check=(name, ok, detail)=>{ results.push({name, ok, detail}); };
const MODE=process.env.MODE||'draft';

const KEYS=(()=>{F.vu({teamCount:12,slot:1,humanTeamName:'A',leagueName:'K',identityMode:false,seed:1,firstFranchiseId:'random'});
  const L=F.J(); return Object.keys(L.players.find(p=>p.attributes&&Object.keys(p.attributes).length).attributes);})();
const mk=(pos,group,r,i,nm)=>({id:'v'+pos+i,name:nm||pos+i,pos,group,rating:r,
  attrs:Object.fromEntries(KEYS.map(k=>[k,r]))});

// ─────────────────────────────────────────────── DRAFT-TIME FEATURES
if (MODE==='draft') {
  // 1. QB rating overrides land
  F.vu({teamCount:12,slot:1,humanTeamName:'A',leagueName:'V',identityMode:false,seed:1,firstFranchiseId:'random'});
  let L=F.J();
  const rate=n=>{const p=L.players.find(x=>x.name===n); return p?F.$f(p).rating:null;};
  check('QB ratings applied', rate('Tom Brady')===95 && rate('Peyton Manning')===94 && rate('Joe Flacco')===78,
    `Brady ${rate('Tom Brady')}, Manning ${rate('Peyton Manning')}, Flacco ${rate('Joe Flacco')}`);

  // 2. corrected ratings reach the tier system
  const js=L.players.find(p=>p.name==='Jeff Saturday');
  const raw=globalThis.__HFL_QFRAW?globalThis.__HFL_QFRAW(js):null;
  const cor=globalThis.__HFL_RATEOF(js, globalThis.__HFL_QFRAW);
  check('tier reads corrected rating', globalThis.__HFL_TIER(cor)!==null && cor>raw,
    `Jeff Saturday raw ${raw} -> corrected ${cor} -> ${globalThis.__HFL_TIER(cor)?.name}`);

  // 3. roster size by league size
  const rounds12=L.totalRounds;
  F.ug&&F.ug(); F.yu&&F.yu();
  F.vu({teamCount:32,slot:1,humanTeamName:'A',leagueName:'V32',identityMode:false,seed:1,firstFranchiseId:'random'});
  const rounds32=F.J().totalRounds;
  check('53-man at 32 clubs, 40 at 12', rounds12===40 && rounds32===53, `12 clubs ${rounds12} rounds, 32 clubs ${rounds32}`);

  // 4. tier caps bind
  globalThis.__HFL_TIERMODE=true;
  F.ug&&F.ug(); F.yu&&F.yu();
  F.vu({teamCount:12,slot:1,humanTeamName:'A',leagueName:'VT',identityMode:true,seed:9,firstFranchiseId:'random'});
  F.Fu();
  L=F.J();
  const caps={L:1,E:3,S:4,Q:5,D:8};
  const per={};
  for(const pk of L.picks){
    const p=L.players.find(x=>x.id===pk.playerId); if(!p) continue;
    const t=globalThis.__HFL_TIER(globalThis.__HFL_RATEOF(p, globalThis.__HFL_QFRAW));
    if(!t) continue;
    per[pk.teamId]=per[pk.teamId]||{}; per[pk.teamId][t.k]=(per[pk.teamId][t.k]||0)+1;
  }
  let over=0, worst='';
  for(const [tid,c] of Object.entries(per)) for(const [k,v] of Object.entries(c)) if(v>caps[k]){over++; worst=`${k} ${v}/${caps[k]}`;}
  check('tier caps bind', over<=3, `${over} club-tier overflows${worst?' (worst '+worst+')':''}`);
  globalThis.__HFL_TIERMODE=false;

  // 5. mandatory QBs get drafted
  let avail=0, missed=0;
  for(let s=0;s<8;s++){
    F.$v('vm-'+s);
    F.ug&&F.ug(); F.yu&&F.yu();
    F.vu({teamCount:12,slot:'random',humanTeamName:'A',leagueName:'VM',identityMode:true,seed:5500+s,firstFranchiseId:'random'});
    F.Fu();
    const LL=F.J();
    const drawn=new Set((LL.rounds||[]).map(r=>r.franchiseId).filter(Boolean));
    const taken=new Set(LL.picks.map(p=>p.playerId));
    for(const nm of Object.keys(globalThis.__HFL_MANDATORY)){
      const p=LL.players.find(x=>x.name===nm&&x.primaryPosition==='QB');
      if(!p||!(p.eligibility||[]).some(e=>drawn.has(e.franchiseId))) continue;
      avail++; if(!taken.has(p.id)) missed++;
    }
  }
  check('mandatory QBs drafted', avail>0 && missed/avail<=0.15, `${avail-missed}/${avail} taken`);

  // 6. modern pool inflates and drafts
  globalThis.__HFL_MODERN=JSON.parse(zlib.gunzipSync(Buffer.from(globalThis.__HFL_MODERN_B64,'base64')).toString());
  globalThis.__HFL_POOLMODE='modern';
  F.ug&&F.ug(); F.yu&&F.yu();
  F.vu({teamCount:12,slot:1,humanTeamName:'A',leagueName:'VMOD',identityMode:false,seed:3,firstFranchiseId:'random'});
  const modL=F.J();
  const yrs=modL.players.map(p=>p.startYear).filter(Boolean);
  check('modern pool loads', modL.players.length>1500 && Math.min(...yrs)>=1999 && Math.max(...yrs)<=2025,
    `${modL.players.length} players, ${Math.min(...yrs)}-${Math.max(...yrs)}`);
  globalThis.__HFL_POOLMODE='alltime';
}

// ─────────────────────────────────────────────── IN-GAME FEATURES
if (MODE==='game') {
  F.vu({teamCount:12,slot:1,humanTeamName:'A',leagueName:'VG',identityMode:false,seed:8,firstFranchiseId:'random'});
  F.Fu();
  const L=F.J();
  const find=n=>{const p=L.players.find(x=>x.name===n); return p?F.$f(p):null;};
  const rice=find('Jerry Rice'), moss=find('Randy Moss'), revis=find('Darrelle Revis'), lott=find('Ronnie Lott');
  const cb2=mk('CB','CB/S',78,1), cb3=mk('CB','CB/S',76,2), s1=mk('S','CB/S',78,3);
  const wr3=mk('WR','WR/TE',76,7), te=mk('TE','WR/TE',76,8);
  const off={leagueSize:12,id:'OFF',name:'O',abbr:'O',players:[find('Patrick Mahomes'),rice,moss,wr3,te,mk('RB','RB',78,9),
    ...['LT','LG','C','RG','RT'].map((p,i)=>mk(p,'OL',80,i))]};
  // exactly four DBs so nobody rotates out
  const mkDef=()=>({leagueSize:12,id:'DEF',name:'D',abbr:'D',players:[
    Object.assign({},revis), cb2, cb3, Object.assign({},lott),
    ...['EDGE','DT','DT','EDGE'].map((p,i)=>mk(p,'DL/EDGE',78,i)),
    mk('LB','LB',76,4), mk('LB','LB',76,5), mk('LB','LB',76,6),
    mk('QB','QB',60,7), mk('K','K',70,8), mk('P','P',70,9)]});

  const play=(games)=>{
    let y={}, pts=0, sacks=0, to=0, halfFG=0, lateScore=0, n=0;
    for(let g=0;g<games;g++){
      const G=F.Um(off, mkDef());
      let guard=0, before=6;
      while(G.status!=='final'&&guard++<400){
        const b=(G.timeouts?.home??3)+(G.timeouts?.away??3);
        F.km&&F.km();
        const a=(G.timeouts?.home??3)+(G.timeouts?.away??3);
        if(a<b) to+=(b-a);
      }
      for(const st of Object.values(G.playerStats||{})) if(st.recYards) y[st.name]=(y[st.name]||0)+st.recYards;
      for(const sc of (G.scoring||[])){
        if((sc.quarter===2||sc.quarter===4)&&sc.clock<=120) lateScore++;
        if(sc.quarter===2&&sc.clock<=45&&/FG|field/i.test(sc.kind||sc.type||'')) halfFG++;
      }
      pts+=G.score.home; sacks+=(G.stats?.away?.sacks)||0; n++;
    }
    return {y, pts:pts/n, sacks:sacks/n, to:to/n, halfFG:halfFG/n, lateScore:lateScore/n};
  };
  const clear=()=>{globalThis.__HFL_SETSHADOW('DEF',null,null,null); globalThis.__HFL_SETDOUBLE('DEF',null);};

  clear();
  const base=play(70);
  check('timeouts are used', base.to>1.5, `${base.to.toFixed(2)} per game`);
  check('late-half scoring happens', base.lateScore>0.5, `${base.lateScore.toFixed(2)} scores inside the last 2:00 of a half`);

  // shadow binds — assign deliberately WRONG and look for movement
  clear();
  globalThis.__HFL_SETSHADOW('DEF',0,cb3.id,rice.id);   // worst corner on the best receiver
  const bad=play(70);
  check('shadow assignment binds', (bad.y[rice.name]||0)/70 > (base.y[rice.name]||0)/70 + 8,
    `Rice ${( (base.y[rice.name]||0)/70).toFixed(0)} -> ${((bad.y[rice.name]||0)/70).toFixed(0)} yds/gm with the worst CB on him`);

  // double fires and suppresses the doubled man
  clear();
  globalThis.__HFL_SETDOUBLE('DEF',0,moss.id,cb2.id,lott.id);
  const dbl=play(70);
  check('double team suppresses its target', (dbl.y[moss.name]||0)/70 < (base.y[moss.name]||0)/70 - 8,
    `Moss ${((base.y[moss.name]||0)/70).toFixed(0)} -> ${((dbl.y[moss.name]||0)/70).toFixed(0)} yds/gm when doubled`);
  check('double costs the rest of the field', (dbl.y[wr3.name]||0)/70 > (base.y[wr3.name]||0)/70 - 2,
    `WR3 ${((base.y[wr3.name]||0)/70).toFixed(0)} -> ${((dbl.y[wr3.name]||0)/70).toFixed(0)} yds/gm`);

  // an AVERAGE helper should still matter
  clear();
  globalThis.__HFL_SETDOUBLE('DEF',0,moss.id,cb2.id,s1.id);   // s1 is 78 and ON the field
  const avg=play(70);
  check('average helper still matters', (avg.y[moss.name]||0)/70 < (base.y[moss.name]||0)/70 - 6,
    `Moss ${((base.y[moss.name]||0)/70).toFixed(0)} -> ${((avg.y[moss.name]||0)/70).toFixed(0)} with a 78 safety helping`);

  clear();
}

// ─────────────────────────────────────────────── FRANCHISE LOOP
if (MODE==='franchise') {
  F.$v('vf');
  F.vu({teamCount:12,slot:1,humanTeamName:'A',leagueName:'VF',identityMode:true,seed:77,firstFranchiseId:'random'});
  F.Fu();
  let sizesOK=true, deadOK=true, advanced=0, retired=0, signed=0;
  for(let y=1;y<=8;y++){
    F.dg(y);
    let w=0; while(F.lg().status==='regular'&&w++<60){F.Tg();F.Eg();}
    let r=0; while(F.lg().status==='playoffs'&&r++<6){F.jg();}
    const res=globalThis.__HFL_ADVANCE(F);
    if(!res||!res.ok) break;
    advanced++; retired+=res.entry.retired||0; signed+=res.entry.signed||0;
    const L=F.J();
    const sizes=L.teams.map(t=>F.Ku(L,t.id).length);
    if(Math.min(...sizes)!==40||Math.max(...sizes)!==40) sizesOK=false;
    const st=globalThis.__HFL_CAREER;
    let dead=0; for(const pk of L.picks){const rec=st.players[pk.playerId]; if(rec&&rec.retired) dead++;}
    if(dead>0) deadOK=false;
  }
  check('season advances', advanced>=7, `${advanced} offseasons completed`);
  check('rosters stay full', sizesOK, 'every club at 40 every year');
  check('no retired dead weight', deadOK, 'zero retired players left on rosters');
  check('careers end and are replaced', retired>0 && signed===retired, `${retired} retired, ${signed} signed`);
  const st=globalThis.__HFL_CAREER;
  check('league history recorded', st.history.length>=7, `${st.history.length} seasons logged, champion of season 1: ${st.history[st.history.length-1]?.champion}`);
}

const pass=results.filter(r=>r.ok).length;
console.log(`\n${MODE.toUpperCase()} — ${pass}/${results.length} pass\n`);
for(const r of results) console.log(`  ${r.ok?'PASS':'FAIL'}  ${r.name.padEnd(34)} ${r.detail}`);
