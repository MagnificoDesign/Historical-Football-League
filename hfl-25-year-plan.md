# HFL Franchise Mode — The 25-Year Plan

*What has to be true for a quarter-century sim to be great, and the order to build it in.*

---

## What actually makes a 25-year sim great

Before the feature list, the design targets. A long sim lives or dies on five things, and every phase below traces back to one of them.

**Stories have to emerge, not be scripted.** The moment you'll tell someone about isn't a menu — it's Bo Jackson staying healthy for ten years, or Adrian Peterson landing on a pass-first team and becoming merely good. The 65/35 rule (talent guarantees 65% of a ceiling; situation decides the rest) is the story generator. It applies to *development*, never to box scores: the sim produces the stat line honestly, and situation only bends the arc of growth and decline.

**Decisions have to compound.** A draft pick matters in year one; it should still matter in year nine. Career length as a drafted asset, aging rosters, and contention windows are what turn 25 seasons into one continuous decision instead of 25 disconnected ones.

**The league has to live without you.** If AI clubs don't rebuild, hoard picks, blow it up, and rise again, the human is playing solitaire against furniture. AI franchise behavior is a feature, not plumbing.

**History has to accumulate and be visible.** A record book, a Hall of Fame, career pages, retired legends. Year 19 feels different from year 2 only if the game remembers year 2.

**A season has to be fast.** Twenty-five years at two hours a season is a 50-hour commitment before the offseason exists. Target: a full season playable (sim-heavy) in 15–20 minutes, with the option to go deep on any single game.

---

## Phase 0 — Engine health first (the unskippable one)

The 717-season audit found that the 1-seed wins 67% of titles and no seed below 3rd has ever won. In a one-season game that's a flaw. **In a 25-year sim it's fatal** — the best roster wins 17 of 25 championships and every story dies. Scoring at 18.7 (target ~22) and the MVP going to a quarterback 99.6% of the time compound the same way: small biases become permanent history when seasons stack.

So the existing fix list is now a prerequisite, in this order: playoff variance (a lower seed must have a real path), scoring back toward 22, and the ratings-concentration audit (Terrell Davis owns 18.5% of all rushing crowns; Tittle, Sharpe, and Wagner have the same disease). A dynasty should be *earnable* — the target is the best club winning maybe 5–7 titles in 25 years, not 15.

**Exit test:** 200 headless 25-year runs; no franchise averages more than ~7 titles; at least one champion from the bottom half of seeds per run.

## Phase 1 — The data spine (1999 → 2025)

Timeline mode needs, for every player: real rookie year, real career span, season-by-season team (franchise pools per year), availability history (the injury prior), and the scarcity-rated peak from the re-rate work. Most of this is already sitting in the container — nflverse rosters 1999–2025, the Madden attribute shapes, the 14,877-player rated table. What remains is the merge: keying everything on `pfr_id`, mapping relocations (STL→LA, SD→LAC, OAK→LV), and storing the whole thing gzipped so the single-file app survives (~5–6k Tier-1 players inflated at boot).

**Exit test:** pick any season 1999–2025; the generated league's rosters spot-check against reality, and the whole bundle still loads on an iPhone in under 3 seconds.

## Phase 2 — The season loop

The architectural refactor: League → Year → {draft, season, playoffs, offseason} → Year+1, with history written at each boundary. Aging and retirement are the first offseason systems in, because they create the roster churn everything else feeds on. Persistence moves to one-record-per-year in IndexedDB so a 25-year save loads the current year fast and pages history in on demand.

This is the largest engineering risk in the project — the app is single-season in its bones. It ships with *placeholder* development (simple curves) so the loop can be tested end-to-end before the interesting parts arrive.

**Exit test:** sim 25 years untouched; no crashes, no save corruption, rosters turn over completely, year 25 loads as fast as year 1.

## Phase 3 — The development engine (your 65/35)

Each player carries a hidden **ceiling** (the rated peak) and a visible current rating. Every offseason he moves toward or away from his ceiling based on: scheme fit (the ten identities are the fit system — a power back on a Ground club climbs, on a Vertical club stalls), opportunity (snaps earned, which the deployment engine already tracks), supporting cast (a QB behind a bad line regresses; the trench duel already measures this), and stability. Talent floors at 65% of ceiling — a legend can disappoint, never bust to nothing.

Injuries are *risk, not script*: each player's real availability sets a personal injury rate the season rolls against, plus a workload term. Most sims, Bo plays a decade. Career length works the same way — real span sets the expectation, usage and luck move it.

**Exit test (the calibration contract):** replay 1999 two hundred times. Each player's *average* career lands within ~15% of his real one; his 10th-to-90th percentile runs span bust-to-all-timer. Same-seed leagues diverge meaningfully by year 10.

## Phase 4 — The economy

No invented salaries in v1. The tier-cap system just shipped **is** the cap: every roster must stay legal under its tier budget every season, contracts are years of control, and free agency is the annual market where aging stars fall out of tiers and rookies grow into them. Free agents weigh money-equivalent (tier slot offered), role, and club quality. This is deliberately the smallest economy that creates real scarcity decisions; dollars can replace points later without redesign.

**Exit test:** 25-year AI-only runs where every club stays cap-legal, stars change teams at a believable rate (~2–4 marquee moves a year), and no AI club hoards or starves.

## Phase 5 — Trades and living AI franchises

AI clubs get a **state machine** — contending, retooling, rebuilding — driven by roster age, tier budget, and recent results. Trades are valued on tier × remaining career years (a 28-year-old Elite with eight years left ≫ a 34-year-old with two), with pick value from a chart and a hard ceiling on lopsidedness so the AI cannot be farmed. Rebuilding clubs sell veterans for picks; contenders pay up at the deadline.

**Exit test:** across long runs, trade volume looks like a real league, the human cannot fleece the AI with a scripted exploit set, and franchise win-cycles actually cycle.

## Phase 6 — History, memory, and the Hall

The presentation layer that makes year 19 feel earned: a record book (single-season and career, with the real NFL records as the founding entries to chase), career pages with year-by-year lines, a Hall of Fame vote for retirees, retired numbers, season recap pages, and a franchise timeline. The trophy shelf already survives resets — this is that idea, expanded into the game's memory.

**Exit test:** after a 25-year sim, you can answer "who was the best back of the 2010s in *this* universe?" from inside the app in three taps.

## Phase 7 — Full-system calibration and pacing

The 717-season harness, pointed at 25-year runs: title distribution, aging curves, economy health, record-break rates across a quarter century, and sim speed. Tuning ends when the exit tests in every phase hold *simultaneously* — systems interact, and this phase exists because they will break each other.

---

## Decisions I need from you (not yet — when we start)

1. **Start-year options** — 1999 only, or any year 1999–2025? (Any-year is nearly free once the spine exists.)
2. **What happens after 2025** — the timeline runs out of real rookie classes in year 27 of a 1999 start. Generated players, or the sim ends at 2025?
3. **Season pacing default** — how much of a season do you want to *play* vs sim in a typical year?
4. **The 12-team all-time league stays untouched** as its own mode. Confirm.

## Honest risk register

The single-file architecture will creak — Phase 2 is where we find out how loudly, and the fallback is splitting the data payload from the app file. The public repo remains eight cycles stale, so every phase's patches must keep exporting as replayable scripts or the work is one bad rebuild from gone. And the container resets between our sessions — every phase's intermediate data gets exported to you at each stage, so nothing depends on my machine remembering.

## Sequence and rough weight

Phase 0 and Phase 1 can run in parallel (engine fixes vs data work — they don't touch). Phase 2 is the giant. 3 and 4 are where the game gets *good*. 5 and 6 are where it gets *loved*. By effort: 0 ≈ a session or two; 1 ≈ two; 2 ≈ three-plus; 3 ≈ two; 4 ≈ two; 5 ≈ two; 6 ≈ two; 7 ≈ ongoing throughout.

*The one-sentence version: fix the engine's fairness, lay the real-history data spine, build the year loop, then let talent, situation, and luck write 25 years of stories the sim never scripted.*
