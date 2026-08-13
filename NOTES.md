# Historical Football League

Single-file historical NFL GM / draft sim. Everything runs client-side in one HTML file.

**Play it:** `hfl-v5.html` → https://magnificodesign.github.io/Historical-Football-League/hfl-v5.html

## What's in this repo

### The game
- `hfl-v5.html` — the current build. Open it, that's the whole app.

### Patch scripts (`/patches`)
The `/src` TypeScript is several builds behind the shipped bundle. Every engine change
since then lives ONLY as these scripts, which apply surgical string edits to the bundle.
Each asserts its anchor appears exactly once before replacing, so they fail loudly rather
than silently corrupting.

Apply in order to reconstruct the current build from an older bundle:
1. `hfl-autofill-patch.py` — personnel auto-fill button; fixes the role→group mapper
   that classified CB1/CB2 as offensive line; widens slot eligibility so edges and
   safeties can play linebacker.
2. `hfl-tiercaps-patch.py` — tier-cap draft mode (Legend/Elite/Star/Quality/Solid
   badges + per-tier draft limits, AI obeys the same caps). Off by default.
3. `hfl-phase0-patch.py` — scoring calibration: red-zone compression 0.50→0.10,
   sticks defense 0.76→0.44, rubber band 0.26→0.30. League scoring 18.8 → 21.9.

NOTE: an earlier script (`hfl-engine-patches.py` — home field, coverage resolution,
perimeter/lockdown corners, red-zone compression, weather) predates these and is not
in this repo. Those changes are baked into the shipped bundle.

### Player data (`/data`)
- `players_rated.json` — 14,877 modern players (2001-2025), scarcity-rated.
  52 at 90+, 105 at 85+, 87% below 70. Keyed on `pfr_id` wherever available.
  NOT YET MERGED INTO THE GAME.

### Pipeline (`/pipeline`)
Rebuilds the player data from source. Requires the nfl-madden-data repo.
- `keys.py` — header synonym layer (every Madden release has a different schema)
- `maplib.py` — maps Madden attributes onto the engine's attribute keys
- `ingest2.py` — all 25 releases → peak season per player
- `consolidate2.py` — id backfill, per-group normalization, AV correction
- `rerate.py` — evidence scoring + the scarcity curve (the one that sets star density)

### Plan
- `hfl-25-year-plan.md` — the eight-phase roadmap for franchise mode.

## Standing rules
- **Ratings are hidden from the player.** Tier badges only, and only in tier-cap mode.
- **Join on IDs, never names.** Name matching merges fathers and sons (Patrick Surtain).
- **Version every upload.** A service worker on the parent domain caches aggressively;
  a new filename is the only reliable way to bypass it.
