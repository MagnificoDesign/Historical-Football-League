// Paired-seed baseline: every cell plays the SAME sequence of games,
// so the only difference between cells is the roster change.
import 'fake-indexeddb/auto';
import { JSDOM } from 'jsdom';
const dom=new JSDOM('<!doctype html><div id="root"></div>',{url:'http://localhost/'});
for(const k of ['window','document','navigator']){try{if(!(k in globalThis))globalThis[k]=dom.window[k];}catch(e){}}
const mem={}; globalThis.localStorage={getItem:k=>k in mem?mem[k]:null,setItem:(k,v)=>{mem[k]=String(v)},removeItem:()=>{},clear:()=>{},key:()=>null,get length(){return 0}};
globalThis.sessionStorage=globalThis.localStorage;
const BUILD=process.env.BUILD||'v26';
try{ await import('./'+BUILD+'.instr.mjs'); }catch(e){}
const F=globalThis.__HFL; try{F.my();}catch(e){}
F.vu({teamCount:12,slot:1,humanTeamName:'A',leagueName:'E2',identityMode:false,seed:8,firstFranchiseId:'random'});
F.Fu();
const L=F.J();
const KEYS=Object.keys(L.players.find(p=>p.attributes&&Object.keys(p.attributes).length).attributes);
const mk=(pos,g,r,i)=>({id:'e'+pos+i,name:pos+i+'/'+r,pos,group:g,rating:r,attrs:Object.fromEntries(KEYS.map(k=>[k,r]))});
const mkOff=(ol)=>({leagueSize:12,id:'OFF',name:'O',abbr:'O',players:[mk('QB','QB',82,0),mk('RB','RB',80,1),
  mk('WR','WR/TE',82,2),mk('WR','WR/TE',80,3),mk('TE','WR/TE',78,4),
  ...['LT','LG','C','RG','RT'].map((p,i)=>mk(p,'OL',ol,10+i))]});
const mkDef=(f)=>({leagueSize:12,id:'DEF',name:'D',abbr:'D',players:[
  mk('EDGE','DL/EDGE',f[0],20), mk('DT','DL/EDGE',f[1],21), mk('DT','DL/EDGE',f[2],22), mk('EDGE','DL/EDGE',f[3],23),
  mk('LB','LB',78,30), mk('LB','LB',78,31), mk('LB','LB',78,32),
  mk('CB','CB/S',78,40), mk('CB','CB/S',78,41), mk('S','CB/S',78,42), mk('S','CB/S',78,43),
  mk('QB','QB',60,50), mk('K','K',75,51), mk('P','P',75,52)]});
const N=parseInt(process.env.N||'150'), OL=parseInt(process.env.OL||'80');
const E=94, A=78;
const cells={ '0':[A,A,A,A], '1':[E,A,A,A], '2':[E,A,A,E], '3':[E,E,A,E] };
const out={};
for(const [name,front] of Object.entries(cells)){
  let pts=[], sacks=0;
  F.$v('pairbase');                        // seed ONCE per cell — stream shared across cells
  const SKIP=parseInt(process.env.SKIP||'0');
  for(let s0=0;s0<SKIP;s0++){              // burn games to reach an independent stretch
    const W=F.Um(mkOff(OL), mkDef(front)); let q=0; while(W.status!=='final'&&q++<400){F.km&&F.km();}
  }
  for(let g=0;g<N;g++){
    const G=F.Um(mkOff(OL), mkDef(front));
    let guard=0; while(G.status!=='final'&&guard++<400){F.km&&F.km();}
    pts.push(G.score.home); sacks+=(G.stats?.away?.sacks)||0;
  }
  out[name]={pts, sacks:sacks/N};
}
const mean=a=>a.reduce((x,y)=>x+y,0)/a.length;
const base=out['0'].pts;
console.log(`\nBUILD ${BUILD} | OL ${OL} | ${N} paired games per cell\n`);
console.log('  cell   pts   sacks   worth   paired SE');
for(const k of ['0','1','2','3']){
  const p=out[k].pts;
  const d=base.map((b,i)=>b-p[i]);          // per-game paired difference
  const m=mean(d);
  const sd=Math.sqrt(d.reduce((s,x)=>s+(x-m)**2,0)/(d.length-1));
  const se=sd/Math.sqrt(d.length);
  console.log(`  ${k} elite  ${mean(p).toFixed(1)}  ${out[k].sacks.toFixed(2)}   ${m>=0?'+':''}${m.toFixed(2)}     ±${se.toFixed(2)}`);
}
