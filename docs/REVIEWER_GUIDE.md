# See SatQuery in action

[Overview](../README.md) · [Setup](SETUP.md) · [Architecture](ARCHITECTURE.md) · [Claims](CLAIM_REGISTER.md)

SatQuery brings prepared imagery, a question, a bounded specialist, and inspectable results into one local workspace. This guide uses supplied examples and saved evaluations. The screenshots are actual working screens, not conceptual mockups.

## The one-minute review

1. Look at the [water result screen](../README.md). It shows a final overlay, three sensor pathways, valid-pixel counts, and predicted coverage.
2. Read [measured evidence](../README.md#measured-evidence). Each result names its task, denominator, and scope. CDVQA is a separate experimental specialist.
3. Choose a depth: follow the local walkthrough below, inspect [numerical records](../paired_lab/evidence/benchmark-20260921/metrics.csv), or read [setup requirements](SETUP.md).

## 1. Map water and inspect three pathways

**Requires:** the provisioned water runtime and supplied `flood-India_900498` sample. [Setup](SETUP.md). This Sen1Floods11 example is already included in the repository; personal imagery is unnecessary.

1. Start the local services and open **http://localhost:8767**.
2. Choose **Workspace → Example datasets**, then the **India · 900498 (test)** water-map example. Its stable sample ID is `flood-India_900498`.
3. Ask **“Map water in these images.”** and select **Analyze images**.
4. Review the result and denominator. Switch between **Water overlay**, **Joint water mask**, **SAR-only water**, **Optical-only water**, **Optical**, and **SAR display**.
5. Open **Checks, calculations & run details** and the limitations. Download the evidence ZIP and run JSON to inspect stored outputs and provenance.

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="images/workspace-water-dark.png">
  <source media="(prefers-color-scheme: light)" srcset="images/workspace-water-light.png">
  <img src="images/workspace-water-dark.png" alt="Working water analysis with a final overlay and three sensor pathways" width="1440">
</picture>

**Demonstrated 27 October 2026:** a new run through the published interface completed on CPU with no browser JavaScript errors. The joint mask selected **129,908 / 262,144 common valid pixels (49.56%)**. This is predicted-mask coverage in one supplied crop, not ground-truth accuracy or a new benchmark. [Screenshot provenance](images/README.md).

**What to inspect:** the three masks stay available when predictions differ. Water includes permanent water; a single-date pair does not separate floodwater. A preview does not prove radiometric quality or physical co-registration.

## 2. Compare observed dates

**Requires:** the provisioned MCI runtime and a prepared temporal example.

Choose a supplied pair such as `mci-test_000585`. Inspect **Before** and **After**, then ask **“Describe road and building changes.”** Review the class mask and caption separately: the caption is interpretation; pixel counts come from the mask. The mask does not establish construction versus demolition.

This is a suggested walkthrough, not an additional inference run performed in this documentation pass. Inspect the recorded [100-pair evaluation and unchanged controls](../BENCHMARK_REPORT.md#temporal-segmentation-and-captions-are-separate), [per-pair outputs](../paired_lab/evidence/benchmark-20260921/temporal-rows.jsonl), and [metrics](../paired_lab/evidence/benchmark-20260921/metrics.csv).

Road/building segmentation does not measure general change-question answering. That task has a [separate CDVQA report](CDVQA_FINAL_REPORT.md) and [CLI](../scripts/predict_cdvqa.py).

## 3. Inspect the evidence behind the headline

Open **Evidence → Evidence overview**, then **Detailed evaluations** for controls, per-question-type results, and dataset qualifications.

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="images/evidence-overview-dark.png">
  <source media="(prefers-color-scheme: light)" srcset="images/evidence-overview-light.png">
  <img src="images/evidence-overview-dark.png" alt="Working Evidence page with CDVQA split sizes and separate water pathways" width="1440">
</picture>

This is the application displaying **saved** evaluations. The astronaut panel is interface artwork, not analytical evidence. Capturing it does not refresh model scores.

| Question | Check |
| --- | --- |
| Do images contribute to CDVQA? | [Paired, question-only, and shuffled-image controls](CDVQA_FINAL_REPORT.md#image-contribution-controls) |
| Was every test pair untouched? | [Exposure and exclusion analysis](CDVQA_FINAL_REPORT.md#previously-inspected-pairs-excluded) |
| Does fusion always win? | [All three water pathways](../BENCHMARK_REPORT.md#water-retain-the-three-pathways) |
| Are official sensors fully validated? | [Downloaded-sample checks and remaining gaps](OFFICIAL_SAMPLE_FINAL_REPORT.md) |
| What does green CI establish? | [Software checks and their limits](SETUP.md#software-checks-without-models) |

## Screens, illustrations, and history

The [architecture schematic](ARCHITECTURE.md) is drawn from code, not an execution trace. `design/` holds earlier references; `UI/` and `web/art/` hold supplied artwork. `ppt_handoff/`, `demo-freeze-20260907/`, `backups/`, and original bundles preserve earlier screens and measurements. Check dates using the [repository map](../REPOSITORY_CONTENTS.md).

There is no public hosted application advertised. Inference requires the external assets in [setup](SETUP.md), and the [claim register](CLAIM_REGISTER.md) applies to demonstrations.
