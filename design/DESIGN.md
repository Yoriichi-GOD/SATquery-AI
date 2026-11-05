# Agreed interface direction

The supplied mockups are design references only. They are not embedded in the app or presented as a screenshot of the working build.

Image-first two-column workspace. Decorative personality belongs in header/footer edges, the empty state, and a compact loading card. The actual satellite image, answer and exported records remain clean.

Dark mode: deep navy, muted violet, teal. Day mode: soft light gray instead of pure white, navy text and readable secondary labels. Theme switching never alters satellite pixels. Theme selection persists locally. Honour reduced motion; never extend a real wait just to display an animation.

The user will generate original assets. Suggested pieces: one transparent logo; dark and light header-edge illustrations; dark and light compact loading illustrations; dark and light shallow footer landscapes. Reuse pieces where possible. Keep text out of artwork. Use transparent PNG/WebP where appropriate; consistent shapes, outlines and lighting. Text, counters and statuses remain real HTML.

The implemented CSS shapes reserve space while these assets are pending. No compass or metre scale is shown without validated geospatial metadata. No fictional progress percentage, confidence score or completed answer appears during inference.

## Current shell and typography — 5 November 2026

The latest user requirement takes precedence over older shell descriptions: **no blur on the header
or taskbar, keep the header fixed, and let the body scroll**. The header uses a solid theme background.
Its measured height reserves space above normal document flow. SATQuery's metadata footer remains
fixed with its measured space reserved below. Whole Workspace/Terrain/Evidence columns are no longer
separate scrolling viewports; charts, horizontal data tables and modal contents retain bounded viewports.

Scientific Noir retains the supplied cosmic/Saturn assets and native black palette. Shared type roles
from the private frontend playbook are locally bundled Space Grotesk 500 headings, Geist 400/500 reading
and controls, and IBM Plex Mono 400 measurements/timestamps. OFL notices ship with the font files.
Shared transitions are short and interruptible, skip keyboard navigation, respect reduced motion,
and never blur or recolor analytical images. See [binding shell rules](UI_SHELL_RULES.md) and
[verification and limits](UI_SHELL_VERIFICATION_20261105.json). The rendered check for this correction
is incomplete because browser control was disabled; prior screenshots do not verify this layout.
