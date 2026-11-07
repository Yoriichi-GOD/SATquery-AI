# Source access and reference roles

Checked7November2026. Native acquisition and derived measurements are separate from source authority,
field truth, source epochs, dataset exposure history and licensing. Small native windows were actually
acquired; the following is not merely a catalogue search.

## Delhi

- Publisher site: [Geospatial Delhi Limited](https://gsdl.org.in/), a Government of NCT Delhi company.
  Its disclaimer does not guarantee completeness, reliability or ground verification. No field-certification
  claim is made for this native map.
- [Sangam native service](https://gsdl.org.in/arcgis/rest/services/DIFC/sangam/MapServer): layer3storm drains,
  layers4–7updated/original sewer and water networks; layers0–2colony/constituency boundaries.
- [Agency storm-drain inventory](https://gsdl.org.in/arcgis/rest/services/DIFC/storm_drain_08082024/MapServer):
  all agency layers0–20were queried; only SDMC and PWD returned features in the fixed ROI.
- [Waterlogging point schema](https://gsdl.org.in/arcgis/rest/services/DIFC/DIFC_portal_data/MapServer/41):
  no usable event-date, measured depth, surveyed-condition or negative-label field. One ROI point is
  positive-only context, not complete exposure reference support.
- [Portal DEM layer](https://gsdl.org.in/arcgis/rest/services/DIFC/DIFC_portal_data/MapServer/49) returned raster
  display metadata with no native posting/vertical-quality contract; it was not called a submeter DEM.
- A documented historical OSM alternate at maps.mail.ru returned504 on one bounded query. Previously
  rejected overpass-api.de/kumi were not repeatedly retried. Native official geometry was used instead.

All31queried native layers have source metadata/identity receipts. Public access is not an unrestricted
redistribution license; raw geometry remains private in the ignored research data directory.

## Nepal finer terrain

[Shean and Bhushan2026, Zenodo22842746](https://doi.org/10.5281/zenodo.22842746) provides a CC-BY-NC4.0
post-event stereo terrain release. Its dates, native posting, ellipsoidal datum and provider warnings are
retained. A bounded archive-directory/TIFF-header read confirmed the saved case lies within the raster
envelope before pixel acquisition. Elevation and input-count native crops were then acquired by HTTP
range inside stored ZIP/COG members. Raw valid coverage and count-screened support were measured
separately. Provider co-registration does not establish local surveyed accuracy. The release concerns
Langtang avalanche terrain; we do not assert equivalence of its mechanism and the saved Syapru event.
No prior-event causal inference or cross-datum elevation difference is reported.

## Independent local water-component test

- [Authors' WorldFloodsv2 release](https://huggingface.co/datasets/isp-uv-es/WorldFloodsv2), CC-BY-NC4.0,
  immutable revision1f3faa2989e69930ac31d5c0a79fd224461123f8. The dataset has public test/meta/S2/gt
  directories, native tiled TIFFs and a two-band reference contract: clear/cloud and land/water.
- [Authors' source repository](https://github.com/spaceml-org/ml4floods) links the release and
  [reference creation code](https://github.com/spaceml-org/ml4floods/blob/main/ml4floods/data/create_gt.py).
  References combine event polygons, hydrology and JRC permanent water. They are not purely new-water
  labels, field-verified exposure labels, or an exposure-assessment benchmark.
- [Dataset paper](https://doi.org/10.1038/s41598-023-47595-7) is the required citation. This campaign did
  not rerun its models or claim direct model-comparison superiority. Six fixed small windows were used;
  no whole-benchmark score is implied.
- [Sen1Floods11](https://github.com/cloudtostreet/Sen1Floods11) has already been trained/evaluated in this
  workspace and is rejected as a new untouched reference. Existing Nepal EMSR927 delivered AOIs are
  development/context under the prior source audit. No fresh blind exposure test is claimed for them.

## Registration and Kedarnath

[Planetary Computer Landsat catalogue](https://planetarycomputer.microsoft.com/dataset/landsat-c2-l2)
was queried for same-sensor/path/row Tier1 scenes with complete footprint coverage. Full metadata is
retained privately. Scene-cloud percentage was not substituted for ROI/common QA-clear coverage.
QA-only ranking and a fixed25% coverage gate yielded no eligible replacement. Shared grids, Tier1
metadata, low fitted residuals and a convenient alternate date are not independent physical control.
The added1.5pixel uncorrected-displacement gate is a declared engineering policy, not a USGS accuracy
certification. Cross-sensor SAR/optical and absolute geolocation remain unvalidated.

No new suitable independent exposure labels were acquired for Varanasi or historical Kedarnath. CEMS
EMSR049 is pre-event base mapping under the prior audit; no flood-truth reinterpretation was made.
The prior [novelty comparison](../../case-campaign-20261107/sources/NOVELTY_COMPARISON.md) remains in force;
the present access and baseline results do not establish a first-ever contribution.
