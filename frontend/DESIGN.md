---
name: Cloud Sentinel v2.0
description: Ground control for three clouds; incidents wait behind a hold line until an analyst clears them.
colors:
  sign-yellow: "#ffc72c"
  sign-black: "#111112"
  sign-red: "#c8102e"
  sign-white: "#f4f4f2"
  asphalt: "#1b1c1e"
  asphalt-raised: "#222427"
  rule: "#34363a"
  rule-soft: "#2a2c2f"
  ink: "#e7e7e4"
  muted: "#a2a4a7"
typography:
  display:
    fontFamily: "Barlow Condensed, Arial Narrow, sans-serif"
    fontSize: "clamp(1.75rem, 2.2vw, 2.25rem)"
    fontWeight: 700
    lineHeight: 1
    letterSpacing: "0.03em"
  numeral:
    fontFamily: "Barlow Condensed, Arial Narrow, sans-serif"
    fontSize: "3.5rem"
    fontWeight: 700
    lineHeight: 1
    fontFeature: "\"tnum\""
  title:
    fontFamily: "Barlow Condensed, Arial Narrow, sans-serif"
    fontSize: "1.125rem"
    fontWeight: 700
    lineHeight: 1
    letterSpacing: "0.08em"
  body:
    fontFamily: "Barlow Semi Condensed, Arial Narrow, sans-serif"
    fontSize: "0.875rem"
    fontWeight: 400
    lineHeight: 1.43
    fontFeature: "\"tnum\""
  label:
    fontFamily: "Barlow Semi Condensed, Arial Narrow, sans-serif"
    fontSize: "0.75rem"
    fontWeight: 600
    lineHeight: 1.33
    letterSpacing: "0.1em"
rounded:
  none: "0px"
spacing:
  gutter: "4px"
  tight: "12px"
  cell: "16px"
  panel-gap: "20px"
  section: "24px"
  page-x: "32px"
components:
  sign-location:
    backgroundColor: "{colors.sign-black}"
    textColor: "{colors.sign-yellow}"
    typography: "{typography.display}"
    rounded: "{rounded.none}"
    padding: "12px 24px"
    height: "96px"
  sign-location-offline:
    backgroundColor: "{colors.sign-red}"
    textColor: "{colors.sign-white}"
    typography: "{typography.display}"
    rounded: "{rounded.none}"
    padding: "12px 24px"
    height: "96px"
  sign-direction:
    backgroundColor: "{colors.sign-yellow}"
    textColor: "{colors.sign-black}"
    rounded: "{rounded.none}"
    padding: "12px 16px"
    height: "96px"
  sign-direction-hover:
    backgroundColor: "{colors.sign-white}"
    textColor: "{colors.sign-black}"
  sign-direction-unknown:
    backgroundColor: "{colors.asphalt-raised}"
    textColor: "{colors.muted}"
    rounded: "{rounded.none}"
    padding: "12px 16px"
    height: "96px"
  hold-sign-active:
    backgroundColor: "{colors.sign-red}"
    textColor: "{colors.sign-white}"
    rounded: "{rounded.none}"
    padding: "2px 8px"
  tag-status:
    backgroundColor: "{colors.asphalt}"
    textColor: "{colors.muted}"
    typography: "{typography.label}"
    rounded: "{rounded.none}"
    padding: "2px 8px"
  data-panel-header:
    backgroundColor: "{colors.asphalt-raised}"
    textColor: "{colors.ink}"
    typography: "{typography.title}"
    rounded: "{rounded.none}"
    padding: "12px 16px"
---

# Design System: Cloud Sentinel v2.0

## Overview

**Creative North Star: "Ground Control for Three Clouds"**

Cloud Sentinel is drawn as an airfield seen from the tower: an asphalt-grey ground ruled with 1px lines, flat painted sign panels standing on it, and a yellow holding-position marking that everything behind it must wait at. Each status has its own sign form, the way airfield signage does: black with a yellow border says where you are (system status), yellow with black says which way to go (a provider and its count), and red with white is a mandatory hold (incidents awaiting an analyst's clearance).

The surface is dense and dim-room friendly. One condensed family in two widths carries everything, all numerals are tabular, and colour is flat and fully saturated only on signs. Everything that is not a sign is asphalt, rule, and quiet grey text, so the signs read first and in under a second. Motion is a single 200ms timing on one easing curve, used only for state change and hover.

The world rejects the slate-KPI-tile SIEM layout: rounded cards, soft shadows, glow, and a green success pill.

**Key Characteristics:**
- Asphalt ground, 1px rules, square corners everywhere.
- Flat sign panels whose colour pairing encodes their meaning.
- Barlow Condensed for sign faces, Barlow Semi Condensed for reading text, uppercase tracked labels, tabular numerals.
- The ICAO holding-position marking as the boundary between overview and work.
- Honest unknowns: an em dash and "no data", never an invented number.

## Colors

A near-neutral asphalt palette with three fully saturated sign colours reserved for meaning.

### Primary
- **Taxiway Sign Yellow** (sign-yellow): the system's one accent. Direction-sign faces, the location-sign border and legend, the holding-position marking, the active-nav underline, focus rings, text selection, and the "Sentinel" half of the wordmark.

### Secondary
- **Mandatory Red** (sign-red): reserved for the mandatory sign forms only. The offline location sign, and the HOLD sign (filled when incidents await clearance, outlined when the hold is clear).

### Neutral
- **Sign Black** (sign-black): location-sign face and the black backing plate that frames the whole sign array; legend colour on yellow.
- **Sign White** (sign-white): legend on red; the hover face of a direction sign.
- **Asphalt** (asphalt): the page ground and dark scheme base.
- **Raised Asphalt** (asphalt-raised): panel header strips and direction signs that cannot vouch for their data.
- **Rule** (rule): every 1px border: panel frames, grid dividers, tag outlines, the top-bar baseline.
- **Soft Rule** (rule-soft): the lighter divider under table column headers.
- **Ink** (ink): primary text on asphalt.
- **Muted** (muted): secondary text, column headers, definition terms, unknown values.

### Named Rules
**The Sign Colour Rule.** Yellow, red, and white appear only as sign faces, sign legends, and painted markings. A colour pairing is a meaning: black/yellow is location, yellow/black is direction, red/white is mandatory. Never use red for anything but a hold or an outage.

**The Lit-Only-When-True Rule.** A sign is lit (full colour) only when the backend vouches for its value. Unknown data drops to raised asphalt with muted text and an em dash.

## Typography

**Display Font:** Barlow Condensed (with Arial Narrow, sans-serif)
**Body Font:** Barlow Semi Condensed (with Arial Narrow, sans-serif)

**Character:** One family in two widths, self-hosted. The condensed cut at 600/700 is the paint on the signs; the semi-condensed cut at 400 to 600 is the readable text around them. Tabular numerals are set on the root.

### Hierarchy
- **Display** (700, clamp 1.75 to 2.25rem, line-height 1, 0.03em, uppercase): the location-sign legend only.
- **Numeral** (700, 3.5rem in provider cells; clamp 1.75 to 2.5rem on direction signs, line-height 1): counters. Fixed furniture: always present, showing an em dash when unknown.
- **Title** (700, 1.125 to 1.25rem, line-height 1, 0.06 to 0.08em, uppercase): panel titles, provider names, empty-state headings, the wordmark.
- **Body** (400, 0.875rem; 1rem for empty-state explanations capped at 42ch): source service names, values, status detail.
- **Label** (600, 0.75rem, 0.1em, uppercase, muted): table column headers, definition terms, status tags. Nav items use 0.875rem at 0.08em.

### Named Rules
**The One Family Rule.** Barlow only, condensed or semi-condensed. No second family, no system display face, no monospace.

**The Uppercase Is Paint Rule.** Uppercase with positive tracking is for sign legends, titles, and labels. Sentences (detail lines, empty-state bodies) stay in sentence case.

## Layout

A single column capped at 1600px, padded 16px on mobile and 32px from the sm breakpoint. The top bar is a fixed 52px band with a 1px rule beneath it. Below it, in order: the sign array, the holding-position marking (24px above and below), the provider grid, then the two data panels.

The sign array is a black backing plate with 4px padding and 4px gutters; on large screens the location sign takes 1.6 parts and each direction sign one part, and below lg the location sign stacks above a three-up row of direction signs. The provider grid is one bordered module divided into three cells by 1px internal rules (whole-cell modules, no gaps), stacking below md. The data panels sit side by side from xl at 1.25 : 1 (incidents wider) with a 20px gap.

Spacing rhythm: 4px inside sign arrays, 12px and 16px inside cells and headers, 20px to 24px between modules, 32px page gutter.

## Elevation & Depth

Flat. There are no elevation shadows, no glow, and no blur. Depth is conveyed by tone and framing alone: asphalt ground, raised-asphalt header strips, 1px rules, and the black backing plate behind the sign array. The only box-shadow in the build is a 2px inset yellow line under the active nav item, which is a painted underline, not elevation.

### Named Rules
**The Painted Not Lifted Rule.** Nothing floats. If something needs emphasis, give it a sign colour or a rule, never a shadow.

## Shapes

Square corners throughout (0px radius); nothing in the build is rounded. Borders are 1px rules, except sign panels, which carry a 4px border in their own legend colour (solid when known, dashed at reduced opacity while checking). The holding-position marking is drawn as four 3px yellow stripes over 18px: two solid, two dashed at 28px on, 16px off.

## Components

### Sign Array (signature)
Status banner composed as an airfield sign array on a black backing plate.
- **Location sign:** black face, 4px yellow border, yellow legend in Display, sentence-case detail line at 90% opacity. Checking state: yellow at 75% legend with a dashed 60% border. Offline state: red face and border, white legend.
- **Direction signs:** one per provider, links to that provider's cell. Yellow face, black legend: provider name, count in Numeral, "event/events", and a 3px-stroke down arrow. Hover turns the face sign-white and nudges the arrow 2px down. Unknown: raised asphalt, muted, em dash plus "no data"; hover lifts text to ink.
- **Motion:** colour and transform transitions at 200ms on cubic-bezier(0.16, 1, 0.3, 1); zeroed under reduced motion.

### HOLD Sign (signature)
Mandatory sign beside the Live Incidents title. Condensed 700, 0.875rem, 0.08em, uppercase, 2px by 8px padding, square.
- **Awaiting:** red face, white legend, "Hold · n awaiting clearance".
- **Clear:** red outline on asphalt with a lightened red legend.
- **No data:** rule outline, muted legend.

### Holding-Position Marking
The full-width yellow hold line between the sign array and the provider grid. Decorative and hidden from assistive tech; it is the world's boundary device and is used once per screen.

### Provider Cell
Whole-cell module with fixed furniture in a fixed order: provider name (Title) and a status tag, source service (muted body), counter (Numeral, muted em dash when unknown), then a definition row of Window and Last poll.

### Tags
Status tags such as "Not connected": 1px rule outline, no fill, Label typography in muted, 2px by 8px padding, square.

### Data Panel (Cards / Containers)
- **Corner Style:** square (0px).
- **Background:** asphalt body, raised-asphalt header strip.
- **Shadow Strategy:** none; see Elevation & Depth.
- **Border:** 1px rule frame and header divider; soft rule under column headers.
- **Internal Padding:** header 12px by 16px; cells 10px by 12px (16px from sm).
- **Empty state:** centred Title heading plus a muted explanation (42ch max) filling a minimum 384px panel. Column headers always render so the table furniture is visible before data exists.

### Navigation
Top bar: wordmark in Title (with "v2.0" muted at 0.875rem), nav items uppercase semi-condensed 600 at 0.08em. Active item takes a 2px yellow underline flush with the bar's bottom rule. Last-check time sits right-aligned in muted body, shortened on mobile.

### Focus
Every focusable element gets a 2px solid sign-yellow outline at 2px offset.

## Do's and Don'ts

### Do:
- **Do** encode status by sign form: black/yellow for location, yellow/black for direction, red/white for mandatory hold.
- **Do** keep every corner square (0px) and every structural line 1px rule; reserve the 4px border for sign panels.
- **Do** show unknown values as an em dash with muted text and "no data"; light a sign only when the backend vouches for it.
- **Do** keep counters and furniture in place in every state so the layout never shifts between empty, offline, and live.
- **Do** use the single motion timing (200ms, cubic-bezier(0.16, 1, 0.3, 1)) for colour and hover state only.

### Don't:
- **Don't** use rounded cards, elevation shadows, glow, or decorative gradients. Gradients are acceptable only as a drawing technique for hard-edged painted markings, as the hold line does.
- **Don't** introduce a green success colour or pill; "operational" is the yellow-on-black location sign.
- **Don't** use sign-red for anything other than a hold or an outage.
- **Don't** add a second type family or load fonts or icons from a CDN; Barlow and lucide-react are bundled locally.
