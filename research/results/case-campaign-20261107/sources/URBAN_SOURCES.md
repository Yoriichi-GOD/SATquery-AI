# Public urban and water raster sources — acquisition note

Checked 2026-11-07. Scope: Varanasi `[82.95,25.22,83.08,25.38]`; **southern Sangam Vihar / Devli–Asola, Delhi** `[77.225,28.47,77.28,28.51]`. Coordinates are west,south,east,north, EPSG:4326. These are analysis windows, not verified administrative boundaries. No northern Delhi settlement with the same name was substituted.

## Acquisition decision

Use **Impact Observatory annual LULC V2** for native categorical 2017–2023 comparison, **WorldCover 2020/2021** for a separately named categorical reference, and **JRC GSW v1.5 occurrence** for historical surface-water context. These public rasters support HTTP range reads. GHSL 2015/2020 remains useful for longer urban history, but the verified provider distribution is a DEFLATE-compressed ZIP around a TIFF, not a verified directly readable built-surface COG.

This pass verified metadata, exact URLs and small byte ranges, not a completed AOI pixel download, map, or independent scientific validation. Typically 16 KiB per raster was read; GHSL header decoding used 64 KiB for one archive. No full raster tile or GHSL archive was downloaded. The small official GHSL grid index (10,941 bytes) was read in memory. Network checks required the permitted external-network execution route; the initial restricted route failed DNS. No source files or application code were changed.

## 1. Impact Observatory / Esri annual LULC V2

The live [Microsoft collection metadata](https://planetarycomputer.microsoft.com/api/stac/v1/collections/io-lulc-annual-v02) reports **2017–2023**, 10 m, CC-BY-4.0. These are annual composites of Sentinel-2 model predictions, not interpolation between two map dates or direct event observations. Nine mapped classes plus nodata are encoded as:

| Code | Meaning |
|---:|---|
| 0 | No data |
| 1 | Water |
| 2 | Trees |
| 4 | Flooded vegetation |
| 5 | Crops |
| 7 | Built area |
| 8 | Bare ground |
| 9 | Snow/ice |
| 10 | Clouds |
| 11 | Rangeland |

Source: [collection metadata and native asset description](https://planetarycomputer.microsoft.com/api/stac/v1/collections/io-lulc-annual-v02). Codes 3 and 6 are absent; do not recode the labels into a guessed contiguous sequence. Mask 0 and exclude cloud class 10 from comparable land-area denominators.

### Exact catalog and asset routes

Searches returned all seven annual items, without a next page:

- [Varanasi catalog query](https://planetarycomputer.microsoft.com/api/stac/v1/search?collections=io-lulc-annual-v02&bbox=82.95,25.22,83.08,25.38&limit=100): supercell `44R`, EPSG:32644.
- [Southern Sangam Vihar catalog query](https://planetarycomputer.microsoft.com/api/stac/v1/search?collections=io-lulc-annual-v02&bbox=77.225,28.47,77.28,28.51&limit=100): supercell `43R`, EPSG:32643.

Native asset pattern, `year=2017…2023`, `nextyear=year+1`:

```text
https://ai4edataeuwest.blob.core.windows.net/io-lulc/io-annual-lulc-v02/{44R|43R}_{year}0101-{nextyear}0101.tif
```

For example: [Varanasi 2017 asset](https://ai4edataeuwest.blob.core.windows.net/io-lulc/io-annual-lulc-v02/44R_20170101-20180101.tif), [Varanasi 2023 asset](https://ai4edataeuwest.blob.core.windows.net/io-lulc/io-annual-lulc-v02/44R_20230101-20240101.tif), [southern Delhi 2023 asset](https://ai4edataeuwest.blob.core.windows.net/io-lulc/io-annual-lulc-v02/43R_20230101-20240101.tif).

Read the anonymous [SAS token endpoint](https://planetarycomputer.microsoft.com/api/sas/v1/token/ai4edataeuwest/io-lulc), then append `?` plus its returned `token` to the asset URL. Tokens expire; obtain a fresh one at acquisition, do not freeze the expiring query string as permanent provenance. The public endpoint returned a token without login. Both 2023 assets returned HTTP 206 / `Accept-Ranges: bytes` for `Range: bytes=0-16383`, with valid BigTIFF signatures. Their full sizes were 215,485,094 bytes (`44R`) and 153,327,839 (`43R`); these full objects were not downloaded.

Both native grids have STAC shape `[89013,61044]` (height,width) and affine transform `[10,0,194780,0,-10,3544360]` in their respective UTM CRS. Transform the AOI into that CRS and use an integer pixel window. Preserve the native class band and CRS in the clipped output. These projection details came from the live AOI item records linked above.

## 2. ESA WorldCover 2020 v100 and 2021 v200

[Official data access](https://esa-worldcover.org/en/data-access) documents public anonymous AWS access, EPSG:4326 COGs, 3° tiles and CC-BY-4.0. **2020 and 2021 use different algorithm versions; an interyear difference includes algorithm changes.** Use any difference as an apparent map-class change with this limitation, not verified development or removal.

| AOI | Tile | 2020 full bytes | 2021 full bytes |
|---|---|---:|---:|
| Varanasi | `N24E081` | 123,094,162 | 126,723,055 |
| Southern Sangam Vihar | `N27E075` | 87,000,059 | 91,078,639 |

All four exact raster URLs below returned HTTP 206 with a 16,384-byte body and `Accept-Ranges: bytes`:

- [Varanasi 2020](https://esa-worldcover.s3.eu-central-1.amazonaws.com/v100/2020/map/ESA_WorldCover_10m_2020_v100_N24E081_Map.tif)
- [Varanasi 2021](https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/map/ESA_WorldCover_10m_2021_v200_N24E081_Map.tif)
- [Southern Sangam Vihar 2020](https://esa-worldcover.s3.eu-central-1.amazonaws.com/v100/2020/map/ESA_WorldCover_10m_2020_v100_N27E075_Map.tif)
- [Southern Sangam Vihar 2021](https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/map/ESA_WorldCover_10m_2021_v200_N27E075_Map.tif)

Sampled native 2021 Varanasi header: 36,000 × 36,000, one uint8 band, EPSG:4326, pixel size `0.00008333333333333333°` (= 1/12000°), origin `(81,27)`, tagged nodata `0`. This is nominal 10 m; geographic pixels do not have constant ground area. Use geodesic area or an appropriate equal-area/projected grid for hectares.

Map codes: 0 nodata; 10 trees; 20 shrubs; 30 grassland; 40 cropland; 50 built-up; 60 bare/sparse vegetation; 70 snow/ice; 80 permanent water; 90 herbaceous wetland; 95 mangroves; 100 moss/lichen. [ESA categorical-data guide](https://ge-config-builder.apex.esa.int/guide/workshops/05-categorical-data/03-categories-cog.html). Read `Map` values directly; the official [access page](https://esa-worldcover.org/en/data-access) explicitly says RGB WMS/WMTS representations are unsuitable for analysis.

Attribution prescribed by provider: © ESA WorldCover project [year] / Contains modified Copernicus Sentinel data ([year]) processed by ESA WorldCover consortium. Dataset DOIs are [2020](https://doi.org/10.5281/zenodo.5571936) and [2021](https://doi.org/10.5281/zenodo.7254221).

## 3. JRC Global Surface Water: current native v1.5 endpoints

The [official download page](https://global-surface-water.appspot.com/download), updated 15 October 2026, now describes the **1984–2024** release. Its [official download-script instructions](https://global-surface-water.appspot.com/gsw/Download_Instructions.html) specify:

```text
https://s3.waw4-1.cloudferro.com/swift/v1/global-surface-water/download2024/Aggregated/VER1-5/{dataset}/{dataset}_{longitude}_{latitude}_v1_5_2024.tif
```

Use `80E_30N` for Varanasi and `70E_30N` for southern Delhi. Here the latitude names the **north** tile edge. Verified HTTP 206 endpoints:

| Product/AOI | URL | Full object bytes |
|---|---|---:|
| Occurrence / Varanasi | [native TIFF](https://s3.waw4-1.cloudferro.com/swift/v1/global-surface-water/download2024/Aggregated/VER1-5/occurrence/occurrence_80E_30N_v1_5_2024.tif) | 95,259,734 |
| Occurrence / Delhi | [native TIFF](https://s3.waw4-1.cloudferro.com/swift/v1/global-surface-water/download2024/Aggregated/VER1-5/occurrence/occurrence_70E_30N_v1_5_2024.tif) | 54,259,473 |
| Seasonality / Varanasi | [native TIFF](https://s3.waw4-1.cloudferro.com/swift/v1/global-surface-water/download2024/Aggregated/VER1-5/seasonality/seasonality_80E_30N_v1_5_2024.tif) | 32,066,358 |

Delhi seasonality follows the same official pattern but its individual URL was not range-tested in this pass. Sampled Varanasi occurrence and seasonality headers: 40,000 × 40,000, one uint8 band, EPSG:4326, `0.00025°` pixels, origin approximately `(80,30)`. Compression tag **50000 (ZSTD)** requires a compatible GDAL build. No GDAL_NODATA tag was present in the inspected native IFD; explicitly mask **255** according to the guide.

Semantics: occurrence 0=not water, 1–100=percentage water occurrence across 1984–2024; seasonality 0=not water, 1–12=months with water, 255=nodata. Seasonality is a latest-year product, not a 41-year sum. Neither is an event flood label. [JRC v5 guide](https://storage.googleapis.com/water-world/downloads_ancillary/DataUsersGuidev2024_v.5.pdf), especially occurrence/seasonality tables.

The same guide warns that 2022–2024 use Landsat Collection 2 while earlier observations use Collection 1; residual positional offsets can reach a 30 m pixel. It also documents corrected v1.5 occurrence processing. Do not silently mix v1.4 and v1.5. The old guessed `https://storage.googleapis.com/global-surface-water/downloads2021/occurrence/...v1_4_2021.tif` URLs returned **404** for both AOIs. Use verified provider endpoints above. [Current release notes](https://global-surface-water.appspot.com/download).

JRC supplies the data freely under Copernicus terms, requests the Pekel et al. 2016 citation, and prescribes map attribution `Source: EC JRC/Google`. [License and citation](https://global-surface-water.appspot.com/download).

## 4. GHSL GHS-BUILT-S R2023A, 2015 / 2020

GHS-BUILT-S measures **built-up surface in m² per grid cell**, not a categorical urban mask or all impervious cover. The official [product information](https://human-settlement.emergency.copernicus.eu/ghs_buS2023.php) gives uint16, nodata 65535 for 3 arcsec WGS84 grids. A sampled Varanasi TIFF header confirms one uint16 band, 12,000 × 12,000, EPSG:4326, approximately `0.00083333333°` pixels; it did not expose a GDAL_NODATA tag, so mask 65535 explicitly.

**Epoch qualification:** 2015 and 2020 are modelled historical epochs produced with spatial-temporal interpolation/extrapolation from observational collections centered on 1975, 1990, 2000, 2014 and 2018. They are not directly acquired 2015 and 2020 images. 2025/2030 are projections. [JRC data-package methodology](https://publications.jrc.ec.europa.eu/repository/bitstream/JRC133256/JRC133256_01.pdf), [JRC recent technical summary](https://publications.jrc.ec.europa.eu/repository/bitstream/JRC143916/JRC143916_01.pdf).

### Exact tile selection and URLs

Tile IDs were spatially selected by decoding the provider's small [WGS84 tiling schema](https://human-settlement.emergency.copernicus.eu/download/GHSL_data_4326_shapefile.zip), linked by its official [tile-selector script](https://human-settlement.emergency.copernicus.eu/script/dldReady.js). This grid is offset; rounding coordinates to ordinary 10° cells would select it incorrectly.

| AOI | Tile | Native tile bounds W,S,E,N |
|---|---|---|
| Southern Sangam Vihar | `R7_C26` | 69.99208308,19.09958346,79.99208304,29.09958342 |
| Varanasi | `R7_C27` | 79.99208304,19.09958346,89.99208300,29.09958342 |

```text
https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/GHSL/GHS_BUILT_S_GLOBE_R2023A/GHS_BUILT_S_E{year}_GLOBE_R2023A_4326_3ss/V1-0/tiles/GHS_BUILT_S_E{year}_GLOBE_R2023A_4326_3ss_V1_0_{tile}.zip
```

All four archive endpoints returned HTTP 206 / byte ranges:

| Year | Tile | Full archive bytes |
|---:|---|---:|
| 2015 | R7_C26 | 57,336,954 |
| 2015 | R7_C27 | 61,759,346 |
| 2020 | R7_C26 | 62,866,608 |
| 2020 | R7_C27 | 66,169,566 |

However, ZIP local headers identify method 8 (**DEFLATE**) around the main TIFF. Archive byte-range support alone does not make this an efficient arbitrary AOI read; avoid claiming a verified small-window GHSL COG path. The provider's [COG_test directory](https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/GHSL/COG_test/) contains a built-characteristics product, not a verified multiepoch BUILT-S equivalent. An explicit later decision is needed if downloading these ~57–66 MB archives is acceptable.

The distributed [copyright file](https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/GHSL/GHS_BUILT_S_GLOBE_R2023A/GHS_BUILT_S_E2015_GLOBE_R2023A_4326_3ss/V1-0/copyright.txt) states CC-BY-4.0, appropriate credit and indication of modifications. Dataset DOI: [10.2905/9F06F36F-4B11-47EC-ABB0-4F8B7B1D72EA](https://doi.org/10.2905/9F06F36F-4B11-47EC-ABB0-4F8B7B1D72EA).

## 5. Southern Sangam Vihar: official drainage evidence available, network not verified

The official [I&FC jurisdiction list](https://ifc.delhi.gov.in/ifc/organizational-setup) identifies **Sangam Vihar (AC-49)** with Devli/Chattarpur/Mehrauli area responsibilities under CD-V and lists **Asola Drain**. This is evidence for the intended southern settlement and relevant drainage jurisdiction; it does not geolocate each drain segment.

Public official materials:

- [Delhi Drainage Map PDF](https://ifc.delhi.gov.in/sites/default/files/ifc/universal/delhi_map.pdf), linked from [Our Services](https://ifc.delhi.gov.in/doit-content/our-services), listed at 783.12 KB.
- [Drainage Master Plan final report, July 2018](https://ifc.delhi.gov.in/sites/default/files/ifc/universal/main_report_dmp_version51.pdf), IIT Delhi for I&FC, 153 pages; live headers identify 4,113,681 bytes.
- [Draft Drainage Master Plan landing page](https://ifc.delhi.gov.in/ifc/draft-drainage-master-plan), with report and Appendix IV–XIV PDFs. Appendix VI is longitudinal profiles of Barapullah drains; these are report products, not independently verified as-built vector data.
- [Natural-drain records](https://ifc.delhi.gov.in/ifc/natural-drains-mpd-1976): lists of 201 historic drains and 44 untraceable drains, as defined by the 1976 plan.

The 2018 report discusses GIS datasets, drainage sections/invert levels and data limitations. **No open native vector/API for current Sangam Vihar drain geometry, cross-sections, blockage, culverts, pump operations or as-built capacity was verified here.** Absence of a verified download is not proof no government dataset exists. Do not label OSM waterways or terrain-derived flow as the official network. Do not convert an existing sewage project into stormwater-drain capacity evidence: the official [2022 planning record](https://delhiplanning.delhi.gov.in/sites/default/files/Planning/vol-2_f_29-12-22.pdf) includes Sangam Vihar sewer works under Okhla drainage terminology, but sewer and stormwater systems have different meanings.

## 6. Varanasi flood reference availability and limits

There are official event and historical products, but **no native event-matched, georeferenced pixel label for this exact Varanasi bbox was acquired or validated in this pass**.

- [NRSC Uttar Pradesh satellite flood analysis, 30 November 2022](https://www.nrsc.gov.in/nrscnew/assets/pdf/maps_dms/SatelliteBasedAnalysis_FloodMappingandMonitoringinUP_30112022.pdf) contains district-level cumulative mapped flood information, including Varanasi. A district total cannot validate an AOI event mask.
- [NRSC 24 October 2021 UP inundation map](https://ndem.nrsc.gov.in/documents/Disaster_Document/2021/UP/upflood50dsc24102021/upflood50dsc24102021_map.pdf) is a rapid mapping PDF from Resourcesat-2A AWiFS, names Varanasi in geographic context, and expressly reports preliminary interpretation without ground verification. Its image footprint, mapped flooded region and date must be checked before any local comparison; a district label alone does not prove inundation in our bbox.
- [Bhuvan disaster flood portal](https://bhuvan-app1.nrsc.gov.in/disaster/usrtasks/flood/flood.php?uname=empty) advertises annual flood layers, metadata and webservice URLs. Its caveat says coverage depends on satellite passes/swaths and actual flooded area may be larger. A WMS visualization is not automatically a native categorical reference raster.
- [NDRF's August 2016 event account](https://ndrf.mha.gov.in/en/operations/flood-uttar-pradesh-and-madhya-pradesh.html) explicitly includes Varanasi among affected districts. It supports event occurrence, not a pixelwise extent label.
- [Varanasi Flood Hub station page](https://sites.research.google/floods/l/25.3236/83.0375/13/g/CWC_006-MGD3VNS) is a model forecast context source, not independently observed flood truth.

Do not score a flood detector against long-term JRC occurrence, annual LULC water, a forecast extent, a historical flood envelope or a regional PDF rendered as RGB. First establish matched date, native label semantics, footprint, resolution, georeferencing, and independence from the detection inputs. A reproducible mask calculation remains an output check until that independent reference exists.

## Window-processing checks before closure

1. Save source href, collection/version/item, acquisition time, bbox and CRS; save refreshed-token expiry separately without treating it as permanent source identity.
2. Read native single-band values, never WMS colors; mask provider nodata explicitly (and annual LULC clouds where used).
3. Clip in native coordinates; document reprojected grid, categorical nearest-neighbor resampling and area method if comparing grids.
4. Report valid-pixel area, denominator exclusions, class histogram, observed value range and each time interval before interpreting change.
5. Treat built class as a proxy; GHSL surface and categorical built area measure different things. Preserve map-version changes, model assumptions and untested flood truth in the report.
