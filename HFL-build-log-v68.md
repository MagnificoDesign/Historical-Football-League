# HFL Build Log — through v68 (Aug 16, 2026)

## Current build
**hfl-v68.html** — created-player careers. Prior: v67 integrity pass. Chain since last publish: v51 (live on GitHub Pages) → v52 Finish-draft → v54 attribute reconcile → v56 synth profiles → v58 Madden shapes → v59 cap compliance → v60 pressure aggregate → v61 trades → v62 economy league-scoped → v63 rating persistence → v64 rookie calendar league-scoped → v65 offseason commit → **v66 storage/career fix** → **v67 contract ledger + annual classes + staged failure**. Patch scripts apply in order. **The public repo still serves v51 (REL-01)** — publishing the current build is the top deployment task.

## The five persistence bugs (the pattern)
Anything a saved franchise needs must live **on the league or the row** and be **committed** — never a page-load global, a runtime map, or an in-memory mutation. Five systems broke this rule, all silently, with rosters reading a healthy 53 throughout:
1. **v62** — economy read the page-load start-year global; missing setting = contracts/cap/trades silently off. Fix: the league decides.
2. **v63** — ratings lived in a runtime map that died on reload (463/600 players re-rated). Fix: rating stamped on the player row.
3. **v64** — rookie calendar computed from the global at two sites; classes never arrived. Fix: league-scoped year. **v67 found a third site** (`thisClass` in replenish) and scoped it too.
4. **v65** — the offseason mutated the league in memory and never called the store commit; every advance was lost on reload. Fix: `au()` in the commit block.
5. **v66** — the storage adapter's boot migration moved every `hfl.*` localStorage key into IndexedDB **and deleted the original**, while career/GM/settings readers only read raw localStorage. First real reload after a save: career year 1, deals 0, GMs regenerate. Fix: migration copies without deleting; career save/load goes through IndexedDB (no 5MB quota) with a localStorage fallback that auto-recovers already-eaten careers. Proved as a regression pair in real Chromium (v65 fails, v66 passes).

## The independent audit (ChatGPT, v65) — cross-checked
Its two critical findings were real, verified in source, and one was independently confirmed by our own numbers (2,142 deals at year 2, exact match):
- **Orphan/wrong-team contracts**: retirement, cutdown — and a fifth path our new gate caught, replenish's "make room" floor pass — dropped roster picks without touching the deal book (224 orphans after the first offseason, 6,588 by year 25). Sign-all kept a cut man's old-club deal on re-signing (337 wrong-team deals by year 25). Payroll iterates the roster only, so every cap check stayed green over a rotting ledger: **a green cap is not a healthy ledger.**
- **Rookie famine after 2025**: the historical timeline ends at 2025; the rookie draft returned silently on an empty class and the scarcity generator never fired over thousands of leftovers.
- Its "persistence PASS" was environment-limited (no IndexedDB in its Node harness, so the boot migration never executed) — it structurally could not see bug 5. Both audits were right in their own environment.
- The 2016 class of 747 (and 2018's 458) is answered: **all unique real players with full attributes** — a debut-definition artifact (nflverse roster coverage expands ~2016, so fringe players first appear then). Policy: keep every real man, tag the class oversize, gate on class size explicitly.

## What v67 does
- **`__HFL_CLOSEDEAL`** — one place closes a contract however a player leaves: retirement at zero (AAV-only deals, nothing prorated), cuts book half AAV as dead money exactly like cap compliance. Called from release, cutdown, and the make-room pass.
- **Sign-all** re-signs fresh at the destination club when it finds a stale mismatched deal.
- **`__HFL_LEDGER_AUDIT`** runs before every commit: zero orphans, zero wrong-team, every rostered player exactly one deal, no duplicate picks. A failed audit blocks the offseason.
- **`__HFL_GENCLASS`** — deterministic 372-man future class per calendar year (canon: every franchise that reaches 2026 meets the same fictional class, the way every franchise meets the same real 2005). Class-shaped ratings capped at 83 so a generated prospect never outclasses a real legend. The rookie draft reports its mode: historical / historical-oversize / generated / empty.
- **Staged failure** — eleven silent catch blocks now feed an error collector; any unrecovered stage failure returns `{ok:false, stage, errors}` **without committing** (mid-offseason career saves are suppressed by a transaction flag, so a failed stage can't half-commit). Ordered commit: ledger audit → year++ → league commit (reverted if it throws) → career save → next season.
- **`__HFL_MIGRATE_BOOK`** — one-time repair of v65-era saves: orphans deleted (no retroactive dead money), wrong-team deals retargeted, missing deals created at the veteran minimum.

## Verification (all on v67)
- Migration fixture: a deliberately corrupted book (2 orphans, 1 wrong-team, 1 missing) repaired exactly; audit clean after.
- Staged-failure smoke: a stage forced to throw → `ok:false, stage:'trades'`, career year frozen; restored → clean advance.
- 25 fast seasons: ledger **1,696/1,696 every year, zero orphans/wrong-team/missing**; classes every year — historical through 2025 (2016 tagged oversize at 747), generated 372 from 2026 on; retirements ramp to ~450/yr as the historical cohorts age out.
- Reload persistence regression: career year 3, deals exactly 1,696 (was 2,142 with orphans), surviving a full browser reload.
- Built-in QA: 38/38 at both 12 and 32 clubs.


## v68 — created-player careers, uncapped (hfl-dev-patch.py)
The rule: nobody ENTERS the league above ~83; careers are uncapped. In this engine the stored rating is the career peak and the age curve climbs to it from below, so v67's cap-at-83 had accidentally capped generated players' peaks — the generated era topped out at 83, scoring sagged to ~18.9, and a fullback won an MVP.
- Generated classes now carry real career-peak distributions: one generational slot per class (88–94), a few stars (84–89), the same taper below.
- Entry stays hard-capped at 83 via a per-player rise depth on the row (`rise = max(5.5, peak − 83)`); the age curve reads it, defaulting to 5.5 so every historical career is unchanged.
- Rookies now play their draft season at entry, not peak: the career record is seeded at rookie-draft time (yrs 0, full suppression) instead of waiting for the first offseason.
- The situation-driven dev offset (±5.5; fit .34 / opportunity .46 / luck .20) was applied at game time but not at valuation — a player who grew +5 played like it but was priced, traded, and cut like he never did. Valuation now sees dev too.
- Measured: every rookie cohort maxes at exactly 83; by year 3 stars reach ~90, by years 5–7 the best hit 92–94; a season-33 league that is 87% homegrown scores 20.9 with a 92-rated MVP. QA 38/38 both sizes; reload persistence and the 1,696-deal ledger unchanged.

## Open items
- **Publish the current build** (REL-01): upload v67, bump the service-worker guard, surface build+hash on the QA screen.
- Passing retune: 36% of QB games clear 300 yards vs the NFL's ~22% (completion bases and deep-ball payoff are the lever).
- Data rows: Marino's missing attributes, the Steve Smith WR/CB name collision, Reggie Nelson listed at guard, Tim Brown's KR/PR weight profile.
- Front-office UI: trade construction/inspection, human FA bidding, cap sheet with contract column and dead money.
- Real team names (your naming call), and the tier-cap vs mandatory-QB rule (your rules call).
- Generated-era top end is an aesthetic knob: steady state carries ~4 players at 90+ vs the historical pool's dozens (it is an all-time greatest-hits collection). Widening the generational slot in GENCLASS is a one-line tune if more juice is wanted.
- Deferred by design: undrafted historical leftovers don't age out; with real annual classes they only feed depth and the pool burns down naturally (1,086 → 41 by year 25).
