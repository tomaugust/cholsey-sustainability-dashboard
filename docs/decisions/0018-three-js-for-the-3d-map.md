# 0018. Add three.js for the 3D Cholsey map (Phase 9)

- **Status:** Accepted by Tom (Q-016, 2026-10-04).
- **Date:** 2026-10-04
- **Deciders:** Claude Code agent proposes; project lead to accept
- **Related:** Phase 9 (P9.1-P9.9); ADR-0002 (stack), ADR-0014, ADR-0017; the `tomaugust/web-map-render` prototype

## Context

The project lead wants a modern, designed, animated front end, including a 3D map of Cholsey with pins and pop-outs. The prototype `web-map-render` builds a parish-shaped terrain block with three.js (displaced mesh, alpha-masked imagery, walls, pivot rig, raycast pins). ADR-0002 chose Astro with static output and no UI framework.

## Decision

1. Add **three.js** (npm, tree-shaken ES modules) for the 3D scene only. Charts stay hand-rolled SVG enhanced with CSS and the Web Animations API; no chart library.
2. **Lazy island.** The scene loads after first paint (idle or visible). The page carries a pre-rendered poster image and complete server-rendered numbers, so it works without JavaScript or WebGL and the initial-load budget (Phase 7, 500 KB gzip) is unchanged. The 3D chunk, including baked assets, has its own cap of about 450 KB gzip.
3. **Bake map assets at build time** (heightmap, OSM imagery, simplified parish and green-space geometry, provenance) into `web/src/data/map/`; no tile fetching in visitors' browsers. Attribution: OpenStreetMap contributors (ODbL), Mapzen/AWS Terrain Tiles, ONS boundaries, OS Open Greenspace (OGL). OS Terrain 50 (OGL) is a possible later replacement for elevation.
4. **Start policy.** On wide screens with a fine pointer and without Save-Data the scene starts when the map scrolls into view; on phones, coarse pointers or Save-Data the flat map shows first with an "Explore in 3D" button. Software-rendered WebGL (as in Lighthouse CI and low-end devices) otherwise blocks the main thread for tens of seconds; with this policy Lighthouse mobile scores 100/100/100.
5. Accessibility: canvas has a text alternative; pins are DOM buttons; keyboard rotate/zoom; reduced motion disables auto-spin and count-ups; 3D is never the only route to a number.

## Consequences

- One new runtime dependency and a new generated-asset step.
- Launch waits for Phase 9 (which follows Phase 8).
- If the project lead declines, the plan falls back to the animated 2D charts and design system (P9.1, P9.6, P9.7) without the 3D scene.
