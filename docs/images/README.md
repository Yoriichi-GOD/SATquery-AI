# Product screenshot provenance

[Overview](../../README.md) · [Walkthrough](../REVIEWER_GUIDE.md) · [Capture manifest](capture-manifest.json)

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
