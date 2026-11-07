# Kedarnath 2013: public input and reference access

Checked 2026-11-07. Research only: catalogs, source pages, a ZIP central directory, and tiny raster header requests were inspected. No full raster, full reference ZIP, or application code was downloaded or changed by this research task.

## Actionable decision

**A credential-free historical Landsat optical-change experiment is feasible. A 2013 Sentinel-1/Sentinel-2 paired experiment is impossible. Independent native flood/debris polygons remain unverified.** Microsoft Planetary Computer supplied anonymously signed raster URLs; 16-byte range reads of both selected Landsat red bands returned HTTP 206 and valid TIFF headers. These checks prove access, not local cloud-free coverage or scientific detection accuracy.

Use May 22 / June 23 as the first optical pair; read their QA before committing to a comparison. The June 23 scene is 62.92% cloudy at scene scale. A local clear-support denominator is essential. Treat the result as candidate surface/channel/debris change; June 23 is six days after June 17 and is not an observation of peak inundation.

## Exact Landsat pair and anonymous access

The following records were returned by both [Earth Search](https://earth-search.aws.element84.com/v1/collections/landsat-c2-l2) and the [Microsoft public STAC collection](https://planetarycomputer.microsoft.com/api/stac/v1/collections/landsat-c2-l2). Source record properties give 30 m ground sampling and EPSG:32644.

| Role | Exact item | Acquisition UTC | Whole-scene cloud |
|---|---|---|---:|
| Before | [LC08_L2SP_145039_20130522_02_T1](https://planetarycomputer.microsoft.com/api/stac/v1/collections/landsat-c2-l2/items/LC08_L2SP_145039_20130522_02_T1) | 2013-05-22 05:14:18.421613 | 12.50% |
| After | [LC08_L2SP_145039_20130623_02_T1](https://planetarycomputer.microsoft.com/api/stac/v1/collections/landsat-c2-l2/items/LC08_L2SP_145039_20130623_02_T1) | 2013-06-23 05:14:11.594610 | 62.92% |

Machine-readable search, covering the initial small Kedarnath window used during discovery:

```text
GET https://planetarycomputer.microsoft.com/api/stac/v1/search?collections=landsat-c2-l2&bbox=79.02,30.70,79.15,30.82&datetime=2013-05-01T00:00:00Z/2013-07-15T23:59:59Z&limit=100
GET https://earth-search.aws.element84.com/v1/search?collections=landsat-c2-l2&bbox=79.02,30.70,79.15,30.82&datetime=2013-05-01T00:00:00Z/2013-07-15T23:59:59Z&limit=100
```

The Microsoft item `assets` dictionary is authoritative for each exact URL. Relevant keys are `blue`, `green`, `red`, `nir08`, `swir16`, `swir22`, `qa_pixel`, `qa_radsat`, and `mtl.json`. Landsat 8 bands map to B2/B3/B4/B5/B6/B7. Reflectance scale and offset in the collection are `0.0000275` and `-0.2`. Preserve raw QA as categorical values.

Exact red assets:

```text
https://landsateuwest.blob.core.windows.net/landsat-c2/level-2/standard/oli-tirs/2013/145/039/LC08_L2SP_145039_20130522_20200912_02_T1/LC08_L2SP_145039_20130522_20200912_02_T1_SR_B4.TIF
https://landsateuwest.blob.core.windows.net/landsat-c2/level-2/standard/oli-tirs/2013/145/039/LC08_L2SP_145039_20130623_20200912_02_T1/LC08_L2SP_145039_20130623_20200912_02_T1_SR_B4.TIF
```

Anonymous signer, tested without an account, subscription key, login cookie, or supplied credential:

```text
GET https://planetarycomputer.microsoft.com/api/sas/v1/sign?href=<percent-encoded original Azure asset URL>
```

Read `href` from the JSON response and pass that signed URL to the raster reader. The signature expires; persist the original asset URL and item ID, and sign again when needed. Microsoft [documents public anonymous catalog/data access with throttling](https://planetarycomputer.microsoft.com/docs/), and its [Landsat example notebook](https://github.com/microsoft/PlanetaryComputerExamples/blob/main/datasets/landsat-c2/landsat-c2-example.ipynb) demonstrates this dataset workflow.

Observed access checks:

| Asset | Request | Observed response |
|---|---|---|
| May 22 red | `Range: bytes=0-15` on signed URL | `206`, `bytes 0-15/90767230`, TIFF magic `49492a00` |
| June 23 red | Same | `206`, `bytes 0-15/91546479`, TIFF magic `49492a00` |

Do not confuse Earth Search with anonymous raster hosting: its Landsat assets point into `s3://usgs-landsat/collection02/...`. The [USGS AWS registry](https://registry.opendata.aws/usgs-landsat/) identifies that bucket as **requester pays**. The Microsoft route above resolves the no-credentials constraint. Landsat data have no USGS reuse restrictions; credit NASA/USGS.

## Other exact scenes discovered

Live STAC search returned these alternatives. This is catalog evidence only; no pixel support or clear coverage was checked. The search window can intersect overlapping WRS rows/paths, and an intersecting scene need not cover a later expanded AOI fully.

| Item | Date | Whole-scene cloud | Role/limit |
|---|---|---:|---|
| `LC08_L2SP_146039_20130529_02_T1` | 2013-05-29 | 7.11% | Alternative pre-event optical |
| `LC08_L2SP_146038_20130529_02_T1` | 2013-05-29 | 14.62% | Overlapping alternative; inspect footprint |
| `LC08_L2SP_145039_20130607_02_T1` | 2013-06-07 | 59.26% | Closer pre-event date, cloudy |
| `LC08_L2SP_146039_20130614_02_T1` | 2013-06-14 | 77.76% | Near-event baseline, very cloudy |
| `LC08_L2SP_146039_20130630_02_T1` | 2013-06-30 | 37.02% | Later post-event fallback |
| `LC08_L2SP_146038_20130630_02_T1` | 2013-06-30 | 8.03% | Later overlapping fallback |
| `LE07_L2SP_146039_20130622_02_T1` | 2013-06-22 | 16% | Landsat 7 fallback; SLC-off gaps |

## Sensor and interpretation constraints

Sentinel-1A launched [April 3, 2014](https://www.esa.int/Newsroom/Press_Releases/Europe_lofts_first_Copernicus_environmental_satellite); Sentinel-2A launched [June 23, 2015](https://blogs.esa.int/rocketscience/2015/06/19/sentinel-2-launch-timeline/). Neither can supply 2013 observations. Landsat 8 [launched February 11, 2013](https://www.usgs.gov/landsat-missions/landsat-8), and the May 22 scene is present in the current processed archive despite preceding the May 30 operational handover. Its L2 spectral inputs are 30 m; 15 m refers to the separate panchromatic band, not these L2 surface-reflectance bands. Landsat 7 is available in 2013, but its [May 2003 SLC failure](https://www.usgs.gov/landsat-missions/landsat-7?page=1) means gap handling must be explicit.

Snow retreat, mountain shadow, cloud, changed illumination, moving sediment, exposed gravel, and water all matter here. An optical difference or water-index change does not by itself establish a flood/debris label, building loss, causation, or historical flood maximum. These are methodological limits, not measured results from this research.

## Reference layers: what actually exists

### CEMS EMSR049: usable base vectors, not flood truth

The [official activation](https://mapping.emergency.copernicus.eu/activations/EMSR049/) covers AOI01 **Kedarnath** and AOI02 Gangotri. Its four listed products are all **Reference** maps. The [Kedarnath detailed PDF](https://cems-mapping-website.s3.eu-west-1.amazonaws.com/static/activations/EMSR049/EMSR049_01KEDARNATH_REFERENCE_DETAIL01_v1_200dpi.pdf) explicitly describes basic topography interpreted from pre-event IKONOS imagery dated 2012-10-23, with SRTM elevations. It does not supply a flood/debris delineation legend. Its printed `10/06/2013` event date is not an acquisition timestamp for post-event imagery.

Exact downloadable vector packages:

- [Kedarnath detail vector ZIP](https://cems-mapping-website.s3.eu-west-1.amazonaws.com/static/activations/EMSR049/EMSR049_01KEDARNATH_REFERENCE_DETAIL01_v1_vector.zip)
- [Kedarnath overview vector ZIP](https://cems-mapping-website.s3.eu-west-1.amazonaws.com/static/activations/EMSR049/EMSR049_01KEDARNATH_REFERENCE_OVERVIEW_v2_vector.zip)

The detail ZIP's central directory was read with range requests, without downloading its 8,210,171-byte payload. It contains 90 entries for AOI, GenericLayer_P, Hydrology_A_LAF, Hydrology_L, Physiography_L, PointsOfInterest_P, Settlements_A, Transportation_A/L/P, including SHP/DBF/PRJ and KMZ. There is no explicitly named flood/debris/damage layer. The PDF says publication of the mapping is unrestricted; this does not grant redistribution rights for the underlying commercial IKONOS image.

### NRSC Bhuvan: historical event display is present; native vector access unresolved

The [official flood panel](https://bhuvan-app1.nrsc.gov.in/disaster/usrtasks/flood/flood.php?uname=empty) exposes Kedarnath June 16–17, 2013 inventory and affected-area entries. Live HTML identifies:

| Public UI label | Actual layer identifier |
|---|---|
| Kedarnath landslide inventory, June 16–17, 2013 | `lhz_invent_kedarnath` |
| Affected areas along Mandakini | `mandakani` |
| Enhanced visualization, June 21, 2013 | `ukpost_c2` |
| Resourcesat-2 LISS-IV, June 21, 2013 | `upuk_post` |

The portal's [own JavaScript](https://bhuvan-app1.nrsc.gov.in/disaster/lib/uncomp/disaster09122022_v2.js) routes those display overlays to `https://bhuvan-ras2.nrsc.gov.in/mapcache?`. A live [WMS GetCapabilities](https://bhuvan-ras2.nrsc.gov.in/mapcache?SERVICE=WMS&REQUEST=GetCapabilities&VERSION=1.1.1) returned `lhz_invent_kedarnath`, marked `queryable="0"`, supporting EPSG:4326/3857. The older `mandakani` and imagery layer names were present in the panel but not found in that capabilities check. Thus some UI entries may be stale. The advertised inventory bounds are global service bounds, not the actual inventory footprint.

This proves an official historical **display layer**, not a native GIS polygon download, pixel acquisition, event-wide completeness, or a reusable-label license. No working native flood/debris GeoJSON/SHP/WFS download was verified. The [NRSC Landslide Atlas page](https://www.nrsc.gov.in/nrscnew/resources_atlas_landslide.php) confirms event-based Kedarnath mapping in its national inventory; counts or scientific claims in an atlas/paper do not substitute for delivered reference polygons.

## Public DEM: two verified choices

**Preferred historical terrain context:** [NASADEM item `NASADEM_HGT_n30e079`](https://planetarycomputer.microsoft.com/api/stac/v1/collections/nasadem/items/NASADEM_HGT_n30e079), asset key `elevation`:

```text
https://nasademeuwest.blob.core.windows.net/nasadem-cog/v001/NASADEM_HGT_n30e079.tif
```

Sign with the same anonymous Microsoft signer. A 16-byte request returned HTTP 206, `bytes 0-15/24158504`, valid TIFF. The [NASA product page](https://doi.org/10.5067/MEASURES/NASADEM/NASADEM_HGT.001) identifies 1 arc-second elevation, February 2000 SRTM telemetry, with additional processing and void filling; it is not a measured 2013 DEM. NASA data are openly shared without restriction; preserve the NASA JPL (2020) DOI citation. Source/fill timing in glacier and void regions needs care.

**Readily accessible alternative:** [Copernicus GLO-30 item](https://earth-search.aws.element84.com/v1/collections/cop-dem-glo-30/items/Copernicus_DSM_COG_10_N30_00_E079_00_DEM), asset `data`:

```text
https://copernicus-dem-30m.s3.amazonaws.com/Copernicus_DSM_COG_10_N30_00_E079_00_DEM/Copernicus_DSM_COG_10_N30_00_E079_00_DEM.tif
```

This URL needs no signer/account. Verified 16-byte HTTP 206, total size 41,706,694 bytes, valid TIFF. The [AWS dataset registry](https://registry.opendata.aws/copernicus-dem/) explicitly allows no-account access. Copernicus describes a [DSM acquired mainly 2011–2015](https://dataspace.copernicus.eu/explore-data/data-collections/copernicus-contributing-missions/collections-description/COP-DEM), including surface objects and some older infill. The catalog's 2021-04-22 datetime is a release/catalog date, not a 2021 terrain survey. Use the product's license/attribution requirements. It cannot establish pre/post 2013 terrain change.

## Proposed campaign AOI and next evidence gate

The parent campaign proposes `[78.96,30.60,79.12,30.80]` (WGS84), working CRS EPSG:32644. It contains the NRSC Kedarnath layer center `(79.0661,30.7333)` and the CEMS detail map's approximately 79°03′30″–79°04′30″ E / 30°43′45″–30°44′30″ N graticule. It is a reasonable **exploratory upper-Mandakini window**, not an event boundary, catchment, complete flood footprint, or entire Kedarnath–Rudraprayag corridor. Full selected-scene coverage of that larger box was not established by this note's smaller-window search.

Before reporting a candidate area: crop all selected bands and QA on a shared 30 m grid; confirm footprint/nodata coverage; report clear/snow/cloud/shadow support separately for before, after, and their intersection; inspect true/false color; quantify only supported pixels. Independent validation stays **NOT VERIFIED** until an appropriate native event reference is acquired and its coverage, timestamp, semantics, and license are checked.
