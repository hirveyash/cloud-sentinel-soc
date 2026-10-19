---
version: 1
slug: "src-app-jsx"
primary_target: "src/App.jsx"
related_targets: []
---

# Dashboard surface

Scope: the main SOC dashboard (src/App.jsx and src/components/*). Mode: Operate.
Audience/job: SOC analyst at a desk, long sessions in a dim room, scanning multi-cloud posture and spotting incidents that need a human decision.
Content: status banner, AWS/GCP/Azure event counters, Live Incidents, Security Events. Phase 2 has no data source beyond /api/health: show honest empty and not-connected states.
Constraints: offline (self-hosted fonts and icons only), no fabricated data.
Unresolved: incident row anatomy and the detail screen (Phases 3 and 5).

## Direction contract

THESIS: Ground control for three clouds. Incidents wait behind a hold line until an analyst clears them. Refuses the slate-KPI-tile SIEM layout with rounded cards and a green success pill.
OWN-WORLD: Asphalt-grey ground (#1b1c1e) with 1px rules. Flat airfield-sign panels: black with yellow border for location/status, yellow with black for provider direction, red with white for mandatory hold. Barlow condensed widths for everything, tabular numerals. No glow, gradients, or rounded cards.
STORY: The analyst sees within a second whether anything is holding for clearance and which cloud it came from, and trusts that nothing moves without their decision.
FIRST VIEWPORT: 52px top bar (brand, nav, last-check time). A full-width composite sign array as the status banner: the location panel holds the status, then one direction panel per provider with its count. A dashed yellow hold line. A 3-cell provider grid with fixed furniture (count, source service, connection, last poll). Live Incidents (wider) and Security Events tables with column headers and empty states.
FORM: Airfield signage, my grounded list #4; seed:6822c2b209381aff. Signature move: the status banner as an airfield sign array, and the red mandatory HOLD sign marking incidents that await clearance. Raises: fixed counter furniture (character goods); one family plus 1px rules (design annual); whole-cell module (Crouwel); a sign form per status (acetate manual); one motion timing, flat colour (zoo map).
FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance
