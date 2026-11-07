# Product screenshot provenance

[Overview](../../README.md) · [Walkthrough](../REVIEWER_GUIDE.md)

## Terrain workspace — 7 November 2026

[Current README image](terrain-workspace-20261107.jpg) · [Capture manifest](terrain-capture-20261107.json)

The current README hero is an **actual, unretouched 1280 × 720 browser screenshot** of the cosmic Terrain & flood interface. It was captured from the provisioned local application at `http://127.0.0.1:8768/#terrain`, using the existing default browser viewport and ordinary page scrolling. No screenshot generation, compositing, CSS overrides or mocked API responses were used.

The selected saved investigation is `event-fe47db331390`; the terrain is `terrain-45737e0da2983d9d`. The scene uses the existing **90 m Copernicus GLO-90 DSM**, displayed at 1× height with elevation colours and gold saved-water candidate markers. The separately acquired 2 m post-event terrain is a research quality audit and is not the surface shown here. The adjacent optical panel displays the retained **27 August 2026 RGB** source; 22 August is available through the before selector. Both crops were restored locally from the original run and verified against its frozen SHA-256 values. Raw crops remain ignored by Git.

Water, possible debris/surface change and mapped-building optical overlays have independent toggles, shown off in the capture. Their colours do not certify damage or debris type. Terrain source epoch, optical dates and SAR dates differ; common grids do not establish physical sensor registration. Clouds are retained in the RGB display.

The captured view was checked for a rendered terrain canvas, decoded optical imagery, the selected run, and a fixed header with no backdrop blur. This is a focused rendering check, not a complete UI regression or scientific validation. The cosmic artwork is interface decoration, not satellite evidence. Application source baseline: `727793592d083c1fb4b8b22a0ff0844db47fbf64`; the manifest retains source hashes and image integrity.

## Historical captures — 27 October 2026

[Historical capture manifest](capture-manifest.json)

These four images are **actual, unretouched browser captures** of the published application, captured 27 October 2026 at 1440 × 1000 using the existing provisioned WSL runtime and a temporary local browser profile. No API responses were mocked and no screenshot was generated as a conceptual illustration.

| Image | Source |
| --- | --- |
| [Water workspace, dark](workspace-water-dark.png) | New CPU run of supplied `flood-India_900498`, question “Map water in these images.” |
| [Water workspace, light](workspace-water-light.png) | Same completed run, application theme switched |
| [Evidence overview, dark](evidence-overview-dark.png) | Live page displaying existing saved benchmark records |
| [Evidence overview, light](evidence-overview-light.png) | Same page, application theme switched |

These captures predate the reviewed CDVQA browser integration. In particular, the Evidence screenshot contains the earlier CLI-only status wording; the live page and [current implementation review](../PENDING_RELEASE_REVIEW_20261027.md) describe the new explicit mode. The images and recorded hashes remain unchanged.

Application base revision: `cafdb8055c063c5d9f283a2d71d404d0c5830a8b`. Water checkpoint SHA256: `7844387fffd6c7e606895328e61be936304f979fee74411021f7312b3215f7ce`.

The result selected **129,908 of 262,144 common valid pixels (49.56%)** in its joint predicted mask. This is coverage in one demonstration, not measured accuracy. Its timing card describes this one execution and is not a latency benchmark. Opening the Evidence page does not rerun its historical evaluations.

The source sample and model were already in the published repository. These captures contain that example and application results, not personal uploads. Space artwork is existing interface decoration; it is not a satellite observation or scientific output. The [manifest](capture-manifest.json) records image hashes and the checked run scope; runtime uploads, raw ZIPs and private paths are not included.
