#!/usr/bin/env python3
"""LIVE SIM — latest play only, with the box score right beside it.

Nick: "on the play by play, can it just be one row and shows the most recent
play? That way we can have the play by play and box score updating where we can
see everything while we watch the field."

  * the section under the field becomes ONE card showing the most recent play
  * the box score moves straight back under it, so field / last play / box
    score all sit in the same screenful and all three update as it runs
  * the full 20-play log is not lost — it moves into a collapsed "Full drive
    log" tab further down, same pattern as the coverage tab
"""
import sys, io
SRC='hfl-v28.html'; OUT='hfl-v29.html'
html=io.open(SRC,encoding='utf-8').read()
def sub(old,new,label):
    n=html.count(old)
    if n!=1: sys.exit(f'ANCHOR {label}: expected 1, found {n}')
    return html.replace(old,new,1)

OLD_PBP = ("(0,I.jsxs)(`section`,{className:`mt-4`,children:[(0,I.jsx)(`p`,{className:`hfl-label mb-2`,"
  "children:`Play-by-play`}),t.plays.length===0?(0,I.jsx)(`p`,{className:`text-sm text-muted-foreground`,"
  "children:`Kickoff pending — press Start.`}):(0,I.jsx)(`div`,{className:`space-y-1.5`,"
  "children:t.plays.slice(0,20).map((e,n)=>(0,I.jsxs)(`div`,{className:U(`rounded-md border px-3 py-2 text-sm`,"
  "n===0?`border-primary bg-surface-2`:`border-border/60 text-muted-foreground`),children:[(0,I.jsxs)(`p`,"
  "{className:`hfl-label`,children:[`Q`,e.quarter,` `,Hp(e.clock),` · `,t[e.offense].abbr,` · `,e.defense]}),"
  "(0,I.jsx)(`p`,{className:U(e.scoring?`font-semibold text-primary`:``),children:e.text})]},e.id))})]}),")

# one card: the most recent play only
NEW_PBP = ("(0,I.jsx)(`section`,{className:`mt-3`,children:t.plays.length===0?"
  "(0,I.jsx)(`p`,{className:`text-sm text-muted-foreground`,children:`Kickoff pending — press Start.`}):"
  "(()=>{let e=t.plays[0];return (0,I.jsxs)(`div`,{className:`rounded-md border border-primary bg-surface-2 px-3 py-2`,"
  "children:[(0,I.jsxs)(`p`,{className:`hfl-label`,children:[`Q`,e.quarter,` `,Hp(e.clock),` · `,"
  "t[e.offense].abbr,` · `,e.defense]}),"
  "(0,I.jsx)(`p`,{className:U(`text-sm`,e.scoring?`font-semibold text-primary`:``),children:e.text})]},e.id);})()}),")

html = sub(OLD_PBP, NEW_PBP, 'play-by-play to one row')

# the full log, collapsed, further down
FULL_LOG = r"""(0,I.jsxs)(`details`,{className:`mt-3 hfl-card p-2.5`,children:[
 (0,I.jsxs)(`summary`,{className:`flex cursor-pointer items-center justify-between font-display text-[0.68rem] uppercase tracking-widest text-primary`,children:[
   `Full drive log`,
   (0,I.jsxs)(`span`,{className:`text-muted-foreground`,children:[t.plays.length,` plays`]})]}),
 (0,I.jsx)(`div`,{className:`mt-2.5 space-y-1.5`,children:t.plays.slice(0,20).map((e,n)=>(0,I.jsxs)(`div`,{className:U(`rounded-md border px-3 py-2 text-sm`,n===0?`border-primary bg-surface-2`:`border-border/60 text-muted-foreground`),children:[(0,I.jsxs)(`p`,{className:`hfl-label`,children:[`Q`,e.quarter,` `,Hp(e.clock),` · `,t[e.offense].abbr,` · `,e.defense]}),(0,I.jsx)(`p`,{className:U(e.scoring?`font-semibold text-primary`:``),children:e.text})]},e.id))})]}),"""

# put the box score directly under the latest play, and the log where the box score was
BOX_START = "((()=>{\nvar S=t.stats||{},HS=S.home||{},AS=S.away||{};"
bi = html.find(BOX_START)
if bi < 0: sys.exit('box score block not found')
BOX_END = "side_block(`away`,t.away.abbr),side_block(`home`,t.home.abbr)]})]});\n})()),"
be = html.find(BOX_END, bi)
if be < 0: sys.exit('box score tail not found')
be += len(BOX_END)
box_block = html[bi:be]
html = html[:bi] + FULL_LOG + html[be:]

anchor = NEW_PBP
ai = html.find(anchor)
if ai < 0: sys.exit('could not re-find the latest-play card')
ai += len(anchor)
html = html[:ai] + box_block + html[ai:]

io.open(OUT,'w',encoding='utf-8').write(html)
print(f'wrote {OUT} ({len(html)} chars)')
