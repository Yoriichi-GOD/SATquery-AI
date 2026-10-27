# Repository presentation verification — 27 October 2026

[Overview](../README.md) · [Walkthrough](REVIEWER_GUIDE.md) · [Screenshot provenance](images/README.md)

This record covers a documentation/presentation pass based on published application revision `cafdb80`. Existing uncommitted application work was preserved in its original checkout; documentation was prepared on an isolated branch. No historical evaluation outputs were regenerated.

## Checks performed

| Check | Result and scope |
| --- | --- |
| Local documentation references | Local paths, heading anchors, and image/source references checked across the README, repository map, setup, architecture, walkthrough, this record, and screenshot provenance. This does not assert that every historical evidence link in the entire repository is portable. |
| Responsive previews | Four core documents rendered locally at 1440 × 1000 and 390 × 844 in light and dark themes: 16 checks, no missing images or document-level horizontal overflow. Desktop and mobile captures were visually inspected. |
| Real product screenshots | A new CPU water run completed through the published browser interface using supplied `flood-India_900498`. Four actual dark/light captures include the completed workspace and saved Evidence page. No conceptual screen or mocked API was used. |
| Demonstration evidence | ZIP CRC passed. Exported score arrays at threshold 0.5 reproduced all three displayed mask counts and the common-valid denominator. Joint: 129,908 / 262,144 pixels (49.56%). This is predicted coverage, not accuracy. |
| Reviewer example | The temporal sample `mci-test_000585` and question “Describe road and building changes.” passed the actual preparation/dispatch path. No additional temporal inference was performed. |
| Launcher probe | Direct Linux `paired_lab/launch.py --check` confirmed both local services. The PowerShell `start.ps1 -Check` wrapper failed during Windows-to-WSL path translation in this environment; the setup guide records the working Linux route and the observed wrapper limitation. No launch script was changed. |
| Software regression | 96 tests passed in an isolated native Linux checkout with the existing Python 3.11 environment. Application/test code is unchanged from the published base. Tests include mocks and synthetic inputs; they do not establish accuracy. |
| Saved benchmark consistency | Existing publication checker recomputed both CDVQA split metrics, both exposure scopes, and paired/question-only/shuffled-image controls from saved predictions. No fresh benchmark inference was performed. |
| Original checkout preservation | Before/after SHA256 snapshots matched for all 2,775 tracked/untracked files included in the snapshot. Original branch, HEAD, status, and Git index matched. Ignored dependencies/runtime data were outside this file inventory and were not staged. |
| Publication boundary | Only named Markdown guides, four product screenshots, and their provenance manifest are included. Application, tests, model assets, datasets, frozen reports and prediction artifacts are unchanged. |
| GitHub metadata | Description and relevant topics updated. Existing visibility, access settings, empty homepage and license retained. |

## Rendering method and limits

Previews used locally installed Markdown rendering and a headless browser with GitHub-like styling; they are an approximation of GitHub's renderer. No private material was sent to a remote rendering service. Theme-specific screenshots use native application themes, not recolored analytical images. The architecture flow is a source-derived Mermaid schematic; it is not an execution trace.

## Diagnosed platform issue

The first software run read a Windows CRLF checkout from WSL: 95 tests passed and the development-evidence hash check errored. The recorded Git/LF bytes matched the frozen manifest; CRLF conversion explained the difference. All 96 checks then passed in a separate native Linux checkout. No frozen file, expected hash, or application code was changed. [Setup](SETUP.md#byte-exact-evidence-on-windows) now documents this limitation.

## Finding the published checks

Open [Software regression](https://github.com/Yoriichi-GOD/SATquery-AI/actions/workflows/software-tests.yml) and match the run's commit to the documentation revision being inspected. CI runs the software suite and saved-metric publication check; a green check is not GPU inference, independent model validation, or a fresh-machine deployment test.

## Scope

The product demonstration is a supplied Sen1Floods11 example, not an independent accuracy evaluation. Saved CDVQA and component benchmark values retain their original dates, denominators, and exposure disclosures. External runtime provisioning and a new-machine installation were not performed. Publication does not include unfinished local application changes; capabilities describe the published code.
