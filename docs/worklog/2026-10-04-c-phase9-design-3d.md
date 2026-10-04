# 2026-10-04 — Phase 9 design, motion and the 3D map

- **Phase / tasks:** Phase 9, P9.1–P9.9 mostly built (see Not done)
- **Branch / PR:** `phase-9-design-3d` → `main` (PR open, merge held: Q-016)
- **Agent / person:** Claude Code agent, live session with Tom

## Done

- **P9.2 baking**: `pipeline/scripts/bake_map_assets.py` + `cholsey_pipeline/map_assets.py` (tested offline) write `web/src/data/map/` (uint8 terrain 48 KB, softened OSM imagery 110 KB, simplified parish polygons, Cholsey's real accessible OS green-space sites, provenance/attribution in `meta.json`). Contract tests keep them consistent with `areas.json`. Added `pillow` to the pipeline.
- **P9.3 map**: `web/src/lib/map/` (geo, assets, layers, scene) and `components/MapIsland.astro`: three.js terrain block with imagery, drag/flick/pinch/wheel/keyboard controls, auto-spin that stops on hover/focus/open card, DOM pins and pop-out cards (values and `<Provenance>` rendered on the server), poster fallback, no-WebGL fallback, reduced motion.
- **P9.4 home**: new hero (`content/home.md`, draft), map with layer chips, four-beat story (tiles, reference strips, trends, actions), 5-tile grid.
- **P9.5 layers**: canopy, electricity, gas, solar, heat pump as raised parish blocks (zero baseline); green space as Cholsey's real sites on terrain. Solar/heat pump say plainly that only Cholsey has a figure.
- **P9.6 motion**: scroll reveals, count-up numbers that end on the server text, line draw-in and bar growth, year scrubber with Play and sourced readout on trend charts.
- **P9.7 (part)**: header with logo and active nav, type scale, tile grid, unit suffix styling.
- Start policy: 3D auto-starts only on wide, fine-pointer screens without Save-Data; phones get the flat map and an "Explore in 3D" button. Reason: software-rendered WebGL (Lighthouse CI, low-end devices) blocked the main thread for ~70 s; with this policy Lighthouse mobile is 100/100/100 on home and a metric page (SEO 63 only because of noindex).

## Verification

Pipeline pytest and ruff clean; Vitest and Playwright (incl. axe with the 3D map running and in fallback, provenance gate on pins and strips, three-points rule, 360 px, tap targets, map load/keyboard/fallback/reduced-motion/phone-start, scrubber, count-up, weight budgets: initial load < 500 KB gzip without JS; lazy 3D chunk < 450 KB gzip) run locally; Lighthouse CI run locally. Screenshots in `docs/screenshots/phase-9/`.

## Not done / decisions needed

- **Q-016**: accept ADR-0018 (three.js); visual sign-off before merge; follow-ups.
- Not built yet: dark mode, scrubbing the 3D layer by year, a provenance popover (provenance is still the existing disclosure), animated compare page.
- Canopy for comparators shares Cholsey's ward value (ADR-0006), so several blocks are equal; this is the data, not a bug. Aldworth has no canopy figure (documented exception).
- New reader-facing wording (home page) is draft and in the review pack (regenerated).

## Review cycle 1 (Opus) and fixes

- **Blocking, fixed:** a lone figure (solar PV, heat pump) was drawn as a full-height block on Cholsey's outline, implying a ranking. The map now raises blocks only when at least two areas have figures, and the legend says "Only one area has a figure for this measure, so there is nothing to compare it with on the map."
- Also fixed: green-space sites placed with the final (not animating) exaggeration; plain scrolling over the map now scrolls the page (zoom needs Ctrl/Cmd or +/-); tall elements always reveal (motion threshold); the hidden canvas no longer blocks touch or becomes a tab stop; flat-map pins now align with the drawn parishes; pins carry `*` for estimates or partial coverage, with a map note; print shows all content; a 3-second failsafe shows hidden content if the motion script fails, and the hero no longer waits for it; focus moves into an opened card; pin elements are cached and cards only re-placed when the pin moves; materials disposed; contract test compares green-space types with `ACCESSIBLE_FUNCTION_TYPES`; the initial-load budget is now also tested with JavaScript on (lazy chunk excluded).
- Not changed: `baked_at` changes on re-bake; green-space geometry comes from the committed test fixture (source release and retrieval date not recorded in `meta.json`).
- Cycle 2 review to be run when Tom decides on Q-016, before merge.

## Q-016 answered

Tom accepted ADR-0018 and asked to merge now; he will do a full review. The second review cycle was not run. Unbuilt items (dark mode, 3D year scrubbing, provenance popover, animated compare page) are backlog.
