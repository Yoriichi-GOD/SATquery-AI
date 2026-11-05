# SATQuery fixed header and frontend rules — 5 November 2026

The user's explicit requirement: **no blur on the header/taskbar; keep the header fixed and let the body scroll**.
This replaces the previous internally scrolling fixed-main shell. It applies to SATQuery and Flood Lab.

| Before | After | Why |
|---|---|---|
| Flood Lab sticky header with 14 px backdrop blur | Fixed header, solid theme background, both backdrop-filter declarations set to none | Honour the requested stable, clear taskbar |
| Main content locked between fixed header/footer; separate scrolling panes | Normal document flow under the header, with measured space reserved | Scrolling the body keeps the investigation in one readable page |
| Hard-to-verify header height at responsive sizes | ResizeObserver plus font-ready/window-resize measurement | Wrapped navigation cannot cover content after font loading |
| Main SATQuery refers to Space Grotesk without a font asset | Local Space Grotesk 500, Geist 400/500, Plex Mono 400 with OFL notices | Apply the supplied frontend playbook's actual font roles |
| Inconsistent or absent transitions | 180 ms pointer-only route feedback; explicit 140 ms control colors | Show context changes without creating fake progress or delays |
| Potential animation on keyboard/reduced-motion paths | Instant keyboard navigation; reduced-motion cancellation; repeated actions interrupt | Follow Emil's interaction guidance |

## Sources and implementation

- User's private `HACKATHON_BUILD_PLAYBOOK.md`, Scientific Space and evidence-workbench guidance.
  The private file is a local reference, not copied into the repository or published.
- Installed Impeccable polish, typeset, animate and craft-floor instructions.
- Installed Emil design-engineering guidance: explicit properties, short custom ease-out, interruption,
  pointer-only hover, keyboard immediacy and reduced motion. No header/evidence blur is introduced.
- Existing STEPLOCK `CINEMATIC_DESIGN_SYSTEM.md` and `MOTION_SYSTEM.md` were read for techniques.
  Its branding and business logic are not reused.

Heading role: Space Grotesk 500. Reading and control roles: Geist 400/500 with Nirmala/Segoe UI fallback
for scripts outside the bundled Latin subset. Measurement, source hash and timestamp roles: Plex Mono.
Fonts are self-hosted with `font-display: swap`; no external font service is contacted.

`workspace-shell.css` owns shared typography, control feedback and the unblurred header contract.
`workspace-shell.js` owns header measurement and a single bounded navigation transition. Existing
data state, routes, scientific renderers and their calculations keep their owners. No GSAP or smooth-scroll
dependency is needed for this small workbench correction. The playbook explicitly permits native CSS
and the existing runtime; a framework migration would displace the requested fix.

The viewport of a chart/map, horizontal data table, or a modal may still scroll locally. Whole Workspace,
Terrain and Evidence columns now participate in normal document flow. SATQuery's existing metadata
footer remains fixed, with its measured height reserved at the bottom of the body.

## Verification and exact limits

Eight behavioural tests exercise responsive header measurement, font completion, keyboard cancellation,
pointer-only navigation, repeated navigation, reduced motion and missing-capability fallbacks.
They use DOM doubles and do **not** prove rendered CSS geometry. JavaScript syntax and CSS parsing,
installed-file hashes, local HTTP asset delivery and existing regressions are checked separately.

Browser control reported **Local browser use is disabled in Work settings** during this correction.
No alternate browser-control method was used. This change has **not been screenshot-verified**; the earlier
cosmic screenshots predate this correction. Do not cite them as proof of the fixed-header/body-scroll layout.
Remaining rendered checks: 1440×900 and 390×844, scroll body while header bounds stay unchanged,
verify no covered controls after font load, keyboard/rapid navigation, and reduced-motion preference.

No satellite pixels, thresholds, masks, model weights, frozen results, backend API contracts or Day 1 tag
were changed. Main and Flood Lab receive the same shared shell files and attribution notices.
