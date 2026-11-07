# Nepal reference access and compatibility audit

Checked 2026-11-07. Research and access audit only. No competitor was run, no model was trained, no full native ZIP or raster was downloaded, and no prediction accuracy was measured. Source imagery pixels were not viewed. TIFF checks read 16,384-byte metadata ranges only. Existing files under `sources/` were not changed.

## Decision

**No delivered EMSR927 geography should be described as untouched in this workspace. No verified water-only flood-inundation reference for the Syapru saved case was found in the current CEMS product catalogue.** The CEMS event polygons describe landslide/mass movement; the UNOSAT event extent combines mudflow/rockflow and flood-related effects. Both can support a correctly named reference-agreement task, with temporal and class limitations. They cannot establish field truth or validate a new-water mask merely because the activation is named “Flood in Nepal.”

The separate UNOSAT barrier-lake layer is a possible water-polygon task, at a different location and observation time. It is also already present in prior local schema inspection, and its native product page does not establish an unrestricted redistribution licence. It is not a new blind benchmark for this project.

## What is already exposed

| Geography/reference | Current local evidence | Consequence |
| --- | --- | --- |
| EMSR927 AOI01 Syapru Besi | `research-campaign-20261107/repo/research/datasets/registry.json`; prior road-grade diagnostic and saved Syapru runs | Development/replay material. |
| EMSR927 AOI02 Timure | `lifeline-comparison/floodlab/docs/dataset-readiness.json` records `damage_features_inspected: true`, SHA-256 `59375c884371862849eb05dc1c1b6c7622d8ea5a457aece9f8206ae898f29e1b`; `scripts/evaluate_unosat_reference_agreement.py` names run `event-02163045d752` | Already acquired and inspected; cannot relabel it untouched. |
| EMSR927 AOI03 Bidur | Static comparison-source files `lifeline-comparison/reference/scripts/validate_optical_dev.py`, `validate_fusion_dev.py`, and `src/lifeline/radar/extent.py` explicitly name AOI03 as their development area | Known development geography in comparison material. No competitor execution was needed to establish this. |
| EMSR927 AOI05 Phosretar | The same comparison-source split lists AOI05 among its held areas; `reference/web/data/trishuli-2026/validation.json` describes that evaluation | May be new to a particular SATQuery experiment, but not an untouched area across this workspace. A system-specific evaluation and a blind holdout are different claims. |
| UNOSAT `FL20260826NPL.gdb` | `scientific-development/asset-audit.json` already lists flood extent, affected infrastructure, barrier-lake polygon/point layers, cultural heritage, and detachment zone | Native structure and some attributes have already been exposed. |

The static reference-code audit above is provenance evidence, not endorsement of its accuracy. No comparison pipeline or performance evaluation was run during this task. This audit retrieved public metadata, layer styling, and raster grids for access/compatibility purposes; it did not preserve a new blind split. [Local inspection files](../repo/research/datasets/registry.json)

## Official event identity and catalogue

The authoritative detailed record is the [public EMSR927 activation API](https://rapidmapping.emergency.copernicus.eu/backend/dashboard-api/public-activations/?code=EMSR927), described by the [official Emergency Response API documentation](https://mapping.emergency.copernicus.eu/about/how-to-harvest-cems-mapping-data/emergency-response-data/). It returned HTTP 200 through a Windows HTTP client. The [activation landing page](https://mapping.emergency.copernicus.eu/activations/EMSR927/) is a JavaScript shell and did not itself expose these details to the web text reader.

- Activation name/category/subcategory: `Flood in Nepal` / `Flood` / `Flash flood`.
- `eventTime`: `2026-08-25T22:00:00` UTC; `activationTime`: `2026-08-26T09:53:00` UTC. The first time is 03:45 Nepal time on August 26, so the UTC date does not contradict the named local event date.
- The reason describes a flash flood **reportedly** triggered by a GLOF. Preserve that uncertainty; this record does not prove the initiating physical mechanism.
- `sensitive: false`, `closed: true`; activator DG ECHO; GDACS `FL1104124`; Charter `1052`.
- The current detailed record contains **six AOIs**, including two cancelled products, and six finished product entries across four mapped AOIs. An older “four AOIs/four products” secondary index is not the current detailed catalogue.

### Current native product links

These are exact `downloadPath` values returned by the official API, not guessed version paths. HEAD returned 405; streaming GET requests closed before body consumption returned 403 for the five newly checked AOI02/03/05 product ZIPs. Therefore **catalogue provenance is verified; successful native ZIP retrieval in this session is not**. Do not infer that credentials are required or that files do not exist from this client response alone.

| AOI | Product / current version | Official native ZIP | Delivery and caveat |
| --- | --- | --- | --- |
| 01 Syapru Besi | GRA PRODUCT v1 | [AOI01 v1](https://rapidmapping.emergency.copernicus.eu/backend/EMSR927/AOI01/GRA_PRODUCT/EMSR927_AOI01_GRA_PRODUCT_v1.zip) | 2026-08-27 19:03:49 UTC; already local/inspected. |
| 02 Timure | GRA PRODUCT v2 | [AOI02 v2](https://rapidmapping.emergency.copernicus.eu/backend/EMSR927/AOI02/GRA_PRODUCT/EMSR927_AOI02_GRA_PRODUCT_v2.zip) | 2026-08-28 17:10:43 UTC; version reason blank. |
| 03 Bidur | GRA PRODUCT v1 | [AOI03 v1](https://rapidmapping.emergency.copernicus.eu/backend/EMSR927/AOI03/GRA_PRODUCT/EMSR927_AOI03_GRA_PRODUCT_v1.zip) | 2026-08-29 02:57:09 UTC. |
| 03 Bidur | GRA MONIT01 v1 | [AOI03 monitoring v1](https://rapidmapping.emergency.copernicus.eu/backend/EMSR927/AOI03/GRA_MONIT01/EMSR927_AOI03_GRA_MONIT01_v1.zip) | 2026-08-31 01:07:28 UTC; a monitoring product, not an independent event. |
| 05 Phosretar | GRA PRODUCT v3 | [AOI05 v3](https://rapidmapping.emergency.copernicus.eu/backend/EMSR927/AOI05/GRA_PRODUCT/EMSR927_AOI05_GRA_PRODUCT_v3.zip) | 2026-09-04 10:42:28 UTC; reason: correction of observed event and not analysed. |
| 05 Phosretar | GRA MONIT01 v2 | [AOI05 monitoring v2](https://rapidmapping.emergency.copernicus.eu/backend/EMSR927/AOI05/GRA_MONIT01/EMSR927_AOI05_GRA_MONIT01_v2.zip) | 2026-09-07 16:38:38 UTC; missing damaged/destroyed bridges corrected. |

AOI04 Bharatpur and AOI06 Kyundi both have `feasible: false`, `statusCode: N`, empty download paths, no layers/maps, and the reason “Product cancelled because of persistent cloud coverage” (September 14). Their absence is an unavailable reference, not a dry/non-damage label. All current advertised products are GRA; the response advertises no separate DEL water product.

Baseline products advertised by the same API: [AOI01 BLP](https://rapidmapping.emergency.copernicus.eu/backend/EMSR927/AOI01/EMSR927_AOI01_BLP.zip), [AOI02 BLP](https://rapidmapping.emergency.copernicus.eu/backend/EMSR927/AOI02/EMSR927_AOI02_BLP.zip), [AOI03 BLP](https://rapidmapping.emergency.copernicus.eu/backend/EMSR927/AOI03/EMSR927_AOI03_BLP.zip), [AOI04 BLP](https://rapidmapping.emergency.copernicus.eu/backend/EMSR927/AOI04/EMSR927_AOI04_BLP.zip), [AOI05 BLP](https://rapidmapping.emergency.copernicus.eu/backend/EMSR927/AOI05/EMSR927_AOI05_BLP.zip), [AOI06 BLP](https://rapidmapping.emergency.copernicus.eu/backend/EMSR927/AOI06/EMSR927_AOI06_BLP.zip). These links were not downloaded. The [activation-wide archive](https://rapidmapping.emergency.copernicus.eu/backend/EMSR927/EMSR927_products.zip) was also left unread. Earlier product-version archives are not enumerated by this response; existence of an earlier version number is not verified access to that older file.

### Labels and compatible roles

The [AOI01 official observed-event GeoJSON](https://rapidmapping-viewer.s3.eu-west-1.amazonaws.com/EMSR927/AOI01/GRA_PRODUCT/EMSR927_AOI01_GRA_PRODUCT_observedEventA_v1.json) returned HTTP 200 (278,931 bytes). Its properties are `event_type: 6-Mass Movement`, `obj_desc: Landslide`, `det_method: Photo-interpretation`, `dmg_src_id: 2`, area 111.07795 ha. This agrees with the previously inspected local native structure. The current API statistics for all finished products use `Landslide`.

Small official styling files for [AOI02 observed event v2](https://rapidmapping-viewer.s3.eu-west-1.amazonaws.com/EMSR927/AOI02/GRA_PRODUCT/EMSR927_AOI02_GRA_PRODUCT_observedEventA_v2.sld), [AOI03 observed event v1](https://rapidmapping-viewer.s3.eu-west-1.amazonaws.com/EMSR927/AOI03/GRA_PRODUCT/EMSR927_AOI03_GRA_PRODUCT_observedEventA_v1.sld), and [AOI05 observed event v2](https://rapidmapping-viewer.s3.eu-west-1.amazonaws.com/EMSR927/AOI05/GRA_PRODUCT/EMSR927_AOI05_GRA_PRODUCT_observedEventA_v2.sld) each returned HTTP 200 and contain the class `Landslide`. Styling plus aggregate metadata is not a complete inspection of every feature in the native packages. The monitoring feature classes were not separately inspected in this audit. No water-only class was verified.

**Version trap:** AOI05's native product archive is v3, while its currently advertised `observedEventA` and `notAnalysedA` viewer layer filenames remain v2. Pin archive version, layer version, delivery time, and hashes separately; do not silently “fix” filenames to v3.

The API also advertises individual observed-event GeoJSONs for [Timure v2](https://rapidmapping-viewer.s3.eu-west-1.amazonaws.com/EMSR927/AOI02/GRA_PRODUCT/EMSR927_AOI02_GRA_PRODUCT_observedEventA_v2.json), [Bidur product v1](https://rapidmapping-viewer.s3.eu-west-1.amazonaws.com/EMSR927/AOI03/GRA_PRODUCT/EMSR927_AOI03_GRA_PRODUCT_observedEventA_v1.json), [Bidur monitoring v1](https://rapidmapping-viewer.s3.eu-west-1.amazonaws.com/EMSR927/AOI03/GRA_MONIT01/EMSR927_AOI03_GRA_MONIT01_observedEventA_v1.json), [Phosretar product layer v2](https://rapidmapping-viewer.s3.eu-west-1.amazonaws.com/EMSR927/AOI05/GRA_PRODUCT/EMSR927_AOI05_GRA_PRODUCT_observedEventA_v2.json), and [Phosretar monitoring v2](https://rapidmapping-viewer.s3.eu-west-1.amazonaws.com/EMSR927/AOI05/GRA_MONIT01/EMSR927_AOI05_GRA_MONIT01_observedEventA_v2.json). These exact URLs are catalogued access options; their geometry bodies were not retrieved in this audit. They are not a replacement for complete package source tables, masks, and footprint provenance.

| Proposed target | Compatible role of available reference | Required restriction |
| --- | --- | --- |
| New floodwater segmentation at Syapru | None verified from CEMS EMSR927 | Do not score a water-only mask against a landslide polygon as water accuracy. |
| Debris/mass-movement impact extent | CEMS photo-interpreted landslide polygon; UNOSAT cumulative mudflow/rockflow extent | Name the target to match the reference; preserve mixed-process and cumulative-time limits. No mechanism or field-truth claim. |
| Road damage grading | CEMS `transportationL` grade attributes | A separate diagnostic/classification question; screen `Possibly damaged` explicitly and do not interpret `No visible damage` as confirmed open/safe. Hazard intersection is not damage or access validation. |
| Building exposure | Asset geometry intersected with a declared hazard mask | Reference `builtUpP` is a building point/approximate centroid, not a footprint. CEMS damage grades and UNOSAT “exposed or near” counts are different target definitions. |
| Bridge damage | CEMS transportation points/grades | Preserve point semantics and corrected product versions; not a continuous road-water overlap target. |
| New barrier-lake surface water | UNOSAT 4260 barrier-lake polygons | Different location/date/phenomenon; already schema-exposed locally and only two mapped lakes. |

Current official layers also include `notAnalysedA` for Bidur and Phosretar. Preserve those masks as unknown/excluded; absence of a mapped event outside usable observation is not a negative label. The [official data-source manual](https://mapping.emergency.copernicus.eu/about/rapid-mapping-manual/product-overview/what-is-delivered-in-a-product/map/map-marginalia/data-sources/) says monitoring products can cumulate affected extents from preceding post-event products, while listing only the latest analysis imagery. Do not treat a monitoring polygon as a single-date observation without inspecting its provenance.

## Image dates and raster envelopes

The official API reports all following images as optical `VHR1`; its documentation defines acquisition time as UTC. Some August 27 records carry `new: false` despite their post-event date. **Use acquisition time and the native source role, not that Boolean alone, to distinguish pre/post.** Complete pre-event source dates and original image footprint geometry are not exposed by the activation API; those remain to be checked in native source records and `imageFootprintA` after resolving native access.

Every linked viewer COG below returned HTTP 206 for `bytes=0-16383`. Its TIFF metadata identifies EPSG:3857, pixel-is-area, and nodata 0. Envelopes are `(xmin, ymin, xmax, ymax)` in that CRS, rounded to 0.01 m. These are **published raster rectangles**, not valid-data footprints, cloud-free coverage, or original acquisition swaths. Spacing is the viewer COG's projected grid spacing, not proof of native sensor resolution or absolute accuracy. Pixels were not rendered or read for analysis.

| Product / sensor | Acquisition UTC | Viewer COG (exact URL) | Width × height; grid spacing | EPSG:3857 raster envelope |
| --- | --- | --- | --- | --- |
| AOI01 PRODUCT / WorldView-3 | 2026-08-27 05:05 | [WorldView-3 COG](https://rapidmapping-viewer.s3.eu-west-1.amazonaws.com/EMSR927/AOI01/GRA_PRODUCT/EMSR927_AOI01_GRA_PRODUCT_WORLDVIEW3_20260827_0505_ORTHO_cog.tif) | 5582 × 9868; 0.5 m | 9498135, 3267787, 9500926, 3272721 |
| AOI02 PRODUCT / Legion | 2026-08-27 05:05 | [Legion COG](https://rapidmapping-viewer.s3.eu-west-1.amazonaws.com/EMSR927/AOI02/GRA_PRODUCT/EMSR927_AOI02_GRA_PRODUCT_LEGION_20260827_0505_ORTHO_cog.tif) | 5232 × 9498; 0.5 m | 9501907, 3279565.5, 9504523, 3284314.5 |
| AOI03 PRODUCT / Satellogic | 2026-08-27 04:22 | [Satellogic COG](https://rapidmapping-viewer.s3.eu-west-1.amazonaws.com/EMSR927/AOI03/GRA_PRODUCT/EMSR927_AOI03_GRA_PRODUCT_SATELLOGIC_20260827_0422_ORTHO_cog.tif) | 10422 × 19198; 1 m | 9473205, 3230924, 9483627, 3250122 |
| AOI03 PRODUCT / BlackSky | 2026-08-27 12:09 | [BlackSky COG](https://rapidmapping-viewer.s3.eu-west-1.amazonaws.com/EMSR927/AOI03/GRA_PRODUCT/EMSR927_AOI03_GRA_PRODUCT_BLACKSKY_20260827_1209_ORTHO_cog.tif) | 10256 × 12857; ~0.97 m | 9473204.30, 3230923.53, 9483152.62, 3243394.82 |
| AOI03 MONIT01 / PeruSAT-1 | 2026-08-27 04:47 | [PeruSAT-1 COG](https://rapidmapping-viewer.s3.eu-west-1.amazonaws.com/EMSR927/AOI03/GRA_MONIT01/EMSR927_AOI03_GRAMONIT01_PERUSAT1_20260827_0447_ORTHO_cog.tif) | 11614 × 21393; ~0.897414 m | 9473204.75, 3230923.82, 9483627.31, 3250122.19 |
| AOI03 MONIT01 / Resurs-P | 2026-08-28 08:29 | [Resurs-P COG](https://rapidmapping-viewer.s3.eu-west-1.amazonaws.com/EMSR927/AOI03/GRA_MONIT01/EMSR927_AOI03_GRAMONIT01_RESURSP_20260828_0829_ORTHO_cog.tif) | 10432 × 19200; 1 m | 9473205, 3230922, 9483637, 3250122 |
| AOI05 PRODUCT / Pleiades | 2026-08-31 05:27 | [Pleiades COG](https://rapidmapping-viewer.s3.eu-west-1.amazonaws.com/EMSR927/AOI05/GRA_PRODUCT/EMSR927_AOI05_GRA_PRODUCT_PLEIADES_20260831_0527_ORTHO_cog.tif) | 24532 × 14227; ~0.500445 m | 9462013.18, 3225104.34, 9474290.10, 3232224.17 |
| AOI05 PRODUCT / Pleiades Neo | 2026-08-31 05:01 | [Pleiades Neo COG](https://rapidmapping-viewer.s3.eu-west-1.amazonaws.com/EMSR927/AOI05/GRA_PRODUCT/EMSR927_AOI05_GRA_PRODUCT_PNEO_20260831_0501_ORTHO_cog.tif) | 10955 × 6977; 1 m | 9455623, 3222912, 9466578, 3229889 |
| AOI05 MONIT01 / Pleiades Neo | 2026-09-05 04:57 | [Monitoring Pleiades Neo COG](https://rapidmapping-viewer.s3.eu-west-1.amazonaws.com/EMSR927/AOI05/GRA_MONIT01/EMSR927_AOI05_GRA_MONIT01_PNEO_20260905_0457_ORTHO_cog.tif) | 18667 × 9312; 1 m | 9455623, 3222912, 9474290, 3232224 |
| AOI05 MONIT01 / Legion | 2026-09-05 06:32 | [Monitoring Legion COG](https://rapidmapping-viewer.s3.eu-west-1.amazonaws.com/EMSR927/AOI05/GRA_MONIT01/EMSR927_AOI05_GRA_MONIT01_LEGION_20260905_0632_ORTHO_cog.tif) | 18667 × 9312; 1 m | 9455623, 3222912, 9474290, 3232224 |

The source-role/footprint blocker is material for paired input selection: the saved SAR observation on August 28 is later than the August 27 CEMS interpretation, while Phosretar products represent August 31/September 5 conditions. Source timestamps, analysis masks, and actual intersections must be matched before scoring. A common activation ID does not align observation times.

## UNOSAT: native access, labels, dependence, and rights

Official page metadata is available through small public records at [4256](https://unosat.org/our_products/4256), [4257](https://unosat.org/our_products/4257), [4258](https://unosat.org/our_products/4258), [4259](https://unosat.org/our_products/4259), and [4260](https://unosat.org/our_products/4260). All returned HTTP 200. Product pages are [4259](https://unosat.org/products/4259/) and [4260](https://unosat.org/products/4260); their current HTML is a JavaScript shell. The records explicitly state that the analyses are preliminary and not validated in the field.

| Product | Native links returned by official record | Role and limitation |
| --- | --- | --- |
| 4256 live web map | [GDB](https://unosat.org/static/unosat_filesystem/4256/FL20260826NPL.gdb.zip) | Aggregation includes UNOSAT, CEMS, SERTIT and BGS. Provider diversity is not proof of independent measurements. |
| 4257 Rasuwa extent | [GDB](https://unosat.org/static/unosat_filesystem/4257/FL20260826NPL.gdb.zip) | Cumulative mudflow/rockflow; August 26–27 imagery. |
| 4258 Nuwakot extent | [GDB](https://unosat.org/static/unosat_filesystem/4258/FL20260826NPL_gdb.zip), [SHP](https://unosat.org/static/unosat_filesystem/4258/FL20260826NPL_SHP.zip) | Same event and mixed target, not a new event trial. |
| 4259 impact assessment | [GDB](https://unosat.org/static/unosat_filesystem/4259/FL20260826NPL_gdb.zip), [SHP](https://unosat.org/static/unosat_filesystem/4259/FL20260826NPL_SHP.zip) | Cumulative mudflow/rockflow and infrastructure exposure. GET headers verified 200: GDB 28,362,347 B; SHP 23,323,043 B. ZIP bodies unread. |
| 4260 barrier lakes | [GDB](https://unosat.org/static/unosat_filesystem/4260/FL20260826NPL_gdb.zip), [SHP](https://unosat.org/static/unosat_filesystem/4260/FL20260826NPL_SHP.zip) | Two newly formed lakes from CARTOSAT-3 August 28; water-specific, separate geography. SHP GET headers verified 200, 23,323,043 B; body unread. |

Do not merge current `_gdb.zip` links with the previously recorded `4259/FL20260826NPL.gdb.zip` source on filename similarity. The local prior archive SHA-256 is `1c09bd5cff4e5dee870cd8413af0eb036e0dcd75d254cf1a337aa49096aaec2e`; hashes of current endpoint bodies were not measured. Equal reported SHP lengths for 4259 and 4260 do not establish identical content or independent datasets.

**Dependence is explicit:** 4259's `sources` field attributes building damage assessment in **Timure and Syapru Besi to Copernicus EMS**. Its buildings/roads also use Overture. Consequently, agreement with those building labels is not an independent second-provider validation of CEMS or CEMS-derived claims. Prior local `FL20260826NPL.gdb` inspection records `FieldValidation: 0` for event/exposure layers and null sensor-date attributes in several layers. Do not manufacture per-feature dates from filenames.

The 4259 source record lists Sentinel-2 on **August 12 and 27 at 04:56 UTC** (10 m), PlanetScope **August 26 at 05:45 UTC** (3 m), Pleiades **August 27** (50 cm), and Landsat-9 **April 19, 2024** (15 m). Their roles require native source inspection rather than treating every listed item as post-event truth. Product 4260 identifies CARTOSAT-3 **August 28** (1.1 m) for the new lakes, and also lists S2 August 27, PlanetScope August 26, and Landsat-9 August 26 for context. These are provider metadata, not a pixel-level temporal or cloud audit.

**UNOSAT redistribution licence: NOT VERIFIED for these native packages.** The product records have no dataset-specific open-licence field. UNOSAT's public client links “Terms of Use” to [UNITAR Legal](https://unitar.org/legal), whose general website conditions permit acknowledged research/private-study extracts and require prior written authorization for substantial reproduction or commercial uses. That is not evidence that native ZIPs are CC BY or freely redistributable. Retain source links and attribution for internal research; verify package-specific licence/metadata before redistribution. This task did not contact the provider or request permission. PlanetScope, Pleiades, CARTOSAT-3, and basemap imagery have their own stated copyrights; downloading an analytical vector does not transfer rights to their pixels.

## CEMS product and source-imagery licensing

The [CEMS On-Demand Mapping terms](https://mapping.emergency.copernicus.eu/terms-and-conditions/) permit reuse of CEMS information with required source acknowledgement, provide it without warranty, and distinguish third-party information. Use the [official citation guidance](https://mapping.emergency.copernicus.eu/about/citation-guidelines/) for individual products, for example: Copernicus Emergency Management Service (© 2026 European Union), [EMSR927] Syapru Besi (AOI01): Grading Map. Retain the actual version and download date in provenance alongside that attribution.

The [official FAQ](https://mapping.emergency.copernicus.eu/about/faqs/) says that CEMS delivers analysis rather than the source satellite images, and directs Authorised/Associated Users to CDSE for imagery access. Public viewer COG HTTP 200/206 therefore verifies technical access only. **Unrestricted source-image download, model training, and redistribution rights are not verified.** The API's `sensitive: false` is an activation visibility flag, not a blanket licence to commercial source imagery. Prefer separately licensed Sentinel inputs for a reproducible released workflow; keep CEMS vectors as appropriately attributed references.

## Matching GLO-30 and GLO-90 Nepal elevation inputs

The [dataset maintainer's AWS readme](https://copernicus-dem-30m.s3.amazonaws.com/readme.html) defines the filename resolution code in arc-seconds: `_10_` is **1.0 arc-second / GLO-30**, while `_30_` is **3.0 arc-seconds / GLO-90**. The [AWS registry](https://registry.opendata.aws/copernicus-dem/) identifies these public COGs as the 2021 release and documents anonymous access. It is an AWS-hosted derivative with edge trimming/overviews, not an assertion that it is the latest CDSE release.

| Input | Exact public tile endpoint | Verified header evidence |
| --- | --- | --- |
| GLO-30 N28E085 | [30 m COG](https://copernicus-dem-30m.s3.amazonaws.com/Copernicus_DSM_COG_10_N28_00_E085_00_DEM/Copernicus_DSM_COG_10_N28_00_E085_00_DEM.tif) | HEAD 200; 38,402,839 B; ETag `0e1522e26e1a768bdaa827aa64436a0b`; Range 206. TIFF EPSG:4326, 3600 × 3600, 1/3600 degree spacing, tiepoint (85,29), pixel-is-point. |
| GLO-90 N28E085 | [90 m COG](https://copernicus-dem-90m.s3.amazonaws.com/Copernicus_DSM_COG_30_N28_00_E085_00_DEM/Copernicus_DSM_COG_30_N28_00_E085_00_DEM.tif) | HEAD 200; 4,731,595 B; ETag `318b8a5526c5f778167f3054f25fbef6`; Range 206. TIFF EPSG:4326, 1200 × 1200, 1/1200 degree spacing, same tiepoint, pixel-is-point. |

N28E085 is the nominal 85–86°E / 28–29°N cell containing Syapru and Timure. Handle the TIFF pixel-is-point convention explicitly when aligning grids; a nominal one-degree tile cell is not proof of identical outer pixel boundaries after processing. Bidur extends south of 28°N and Phosretar crosses 85°E, so N28E085 alone cannot cover those other AOIs. No additional tile endpoints were verified during this task.

The [official Copernicus DEM collection page](https://dataspace.copernicus.eu/explore-data/data-collections/copernicus-contributing-missions/collections-description/COP-DEM) describes a **digital surface model**, with principal TanDEM-X acquisitions in 2011–2015 and local infilling. This is historical surface elevation, not 2026 bare-earth terrain. The [GLO-30 licence](https://documentation.dataspace.copernicus.eu/APIs/SentinelHub/Data/DEM/resources/license/License-COPDEM-30.pdf) is free for public use with attribution and other terms; retain the required original/adapted-data notices. GLO-90 has its own corresponding notice. A provider ETag is not a SHA-256 checksum.

CDSE is another official access route via `COP-DEM_GLO-30-DGED`, but [current API documentation](https://documentation.dataspace.copernicus.eu/APIs/SentinelHub/Data/DEM.html) requires CCM registration for the 30 m view service and defaults an unspecified `demInstance` to `COPERNICUS_90`. The [July 2026 access announcement](https://dataspace.copernicus.eu/news/2026-7-17-copernicus-dem-30m-view-service-license-acceptance) confirms that service-access change. Explicitly request the intended instance and verify returned metadata; a 10 m output grid does not demonstrate a 10 m input DEM.

**Role:** the verified GLO-30 tile makes a controlled elevation-resolution sensitivity study technically accessible. It does not by itself validate slopes, heights, inundation depth, road passability, building exposure, or building damage. Compare aligned terrain-screen results under fixed settings, inspect source/infill/nodata and vertical assumptions, and assess compatible reference outcomes. Thirty-metre sampling still cannot resolve individual small buildings or narrow channels reliably merely because it is finer than 90 m.

## Other contextual inputs already relevant to this event

[JRC Global Surface Water](https://global-surface-water.appspot.com/download) is a historical water-context source, not August 2026 event truth. Its current official download page now lists V1.5 through 2024, with a Collection 1/2 co-registration warning and an unresolved monthly-recurrence issue. Pin the release; do not silently substitute a newer water baseline for the saved one. [Google Open Buildings](https://sites.research.google/open-buildings/) supplies model-derived footprints/confidence, not damage labels or guaranteed event-date inventory. [Overture attribution](https://docs.overturemaps.org/attribution/) identifies buildings/transportation themes as ODbL and preserves upstream attribution. Because UNOSAT uses Overture assets, reference-count agreement can share inventory errors with an Overture-based prediction path.

The [GFM API](https://api.gfm.eodc.eu/v2/) and [public Swagger schema](https://api.gfm.eodc.eu/v2/swagger.json) are accessible. The schema names authenticated `GET /v2/aoi/{aoi_id}/products` with `time=range`, `from`, `to`, and download routes such as `/v2/download/scene-file/{scene_id}/{aoi_id}/{layer_id}`. No account operation, AOI creation, archive order, or Nepal product query was run. GFM is an automated Sentinel-1 flood/reference-water estimate with exclusion/likelihood layers, so it would be a secondary algorithm comparison, not independent field truth; matched Nepal coverage/date remains unverified. Retain [CEMS GloFAS/GFM terms](https://global-flood.emergency.copernicus.eu/terms-of-service/) if used.

## Closure and blockers

Proved: official activation identity/times; exact current product/version URLs; landslide semantics for the inspected/published layers; cancelled cloud-limited areas; image acquisition metadata and published raster rectangles; current public DEM tile access; public UNOSAT native-link availability; explicit CEMS-to-UNOSAT building-label dependence; prior workspace exposure of all delivered EMSR927 areas.

Not proved: water-only Syapru flood truth; field-validated damage/access; complete native pre/post source/footprint records for the newly listed products; successful CEMS native ZIP download this session; unrestricted UNOSAT or commercial source-image redistribution/training rights; any predictive accuracy or benefit from GLO-30.

Next admissible work is to freeze the intended target and reference role, resolve the native/source/licence blockers, then run the already defined diagnostic. Do not create a new water-accuracy or blind-holdout claim by renaming these existing layers.
