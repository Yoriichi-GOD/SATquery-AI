# Official specification audit

Verified 2026-10-14 IST from the organizer-linked PDFs saved in docs/sources.

Authority chain: Devpost -> problem-statements.pdf -> track-b.pdf -> track-b-linked.pdf.
Deadline: 2026-10-15 00:15 Asia/Kolkata (Devpost).

| Requirement | Finding | Status |
|---|---|---|
| Area/date inputs | Must run from raw satellite data for judge-selected areas and dates | Confirmed; not implemented |
| Nepal case | 26 August 2026 Bhote Koshi-Trishuli; EMSR927 comparison | Confirmed requirement; event assets unverified |
| Sensors | Sentinel-1 and Sentinel-2 when clear; same orbit for SAR comparison | Confirmed |
| Optical level | No L2A-only requirement found in either Track B PDF | Prior brief overconstrained this |
| Historical OSM | Snapshot before event; 27 July is quoted latest availability, not fixed required date | Corrected |
| AI | Choose segmentation trained on listed data OR English/Nepali situation-report copilot | Corrected; both not required |
| Training data | Kuro Siwo, optionally Sen1Floods11 | Confirmed; licenses must be checked upstream |
| Reference data | EMS/UNOSAT/published damage maps and post-event OSM are checking-only | Confirmed; prohibit prediction use |
| Debris | Mapping requirement includes debris; existing water model does not provide it | Missing |
| Elevation downstream tracing | Bonus | Defer |
| Deliverables | Dashboard, one-page sitrep, public repo/README, <=6-page report, demo, attribution | Confirmed |
| Video | Track asks 3 minutes; general guidelines say 3-10 minutes with English audio/subtitles | Target exactly 3 minutes |
| Existing-code reuse | Not explicitly resolved in inspected organizer documents | Open; disclose inheritance, do not claim approval |

Judging: mapping 30%, AI 25%, connectivity 20%, report/Q&A/limitations 15%, usability 10%.
The organizer's event narrative is a statement in the brief, not independently verified disaster reporting. Do not repeat casualty figures as independently established facts.

## Current acceptance boundary
A cached event is a milestone, NOT full compliance with arbitrary-area/date raw-data execution.
No prediction, flood accuracy, infrastructure exposure or settlement isolation is established yet.
Sources: https://multimodal-ai-hackathon-2026-7.devpost.com/ and /rules; PDF links retained in sources.

## Implementation verification update — 15 October 2026

The requirement findings above are retained as the original audit. Their implementation-status phrases are historical, not current readiness claims. Fresh Workspace API job `event-fe47db331390` completed SAR acquisition, historical OSM/node topology, optical coverage selection, debris proxy, exposure/access calculations and frozen exports. All 15 exported files matched their hashes; the copilot building count matched the saved result. The suite passes 69 tests. This verifies one bounded Nepal rectangle, not unrestricted global area/date capability or scientific accuracy. Settlement access remains unresolved; debris remains an unvalidated proxy. Browser visual verification, independent validation, Nepali review and recording remain pending. See `full-workflow-verification.json` and `demo-status.json`.
