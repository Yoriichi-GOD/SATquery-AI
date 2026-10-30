# Data and dependency sources

## Historical Flood Lab

Copernicus Sentinel-1/2 observations and historical OpenStreetMap are prior work. Source dates/scene identifiers and hashes come from each saved manifest. Contains modified Copernicus Sentinel data 2026. OSM attribution: https://www.openstreetmap.org/copyright ; ODbL terms apply to the data. Satellite overlap is not field-confirmed damage. Flood Lab https://github.com/Yoriichi-GOD/SatQuery---Flood-Lab retains its MIT software license; dataset terms are separate.

## New numerical terrain

Public Copernicus GLO-90 COG, AWS 2021 release, accessed 30 October 2026 after explicit participant approval. Source tile `Copernicus_DSM_COG_30_N28_00_E085_00_DEM`, not a 30m-resolution tile: the provider code `30` identifies GLO-90 at 3 arcseconds. Nominal resolution is 90 m.

- Source/access/license links: https://registry.opendata.aws/copernicus-dem/ and https://copernicus-dem-30m.s3.amazonaws.com/readme.html . Registry links the governing Copernicus license; data license is not MIT.
- Downloaded TIFF SHA-256: `2ef95b224a1290ca7661316642efd8dbb8b824b41acd52732962892cce26fe96`.
- Native DSM tile is stored only in ignored `.runtime/jai/terrain`, with its cropped/reprojected metric analysis TIFF and provenance JSON. No credential or original tile is published in the source commit.
- Analysis window: 85.3232, 28.1552, 85.3483, 28.1820 WGS84. Bilinear reprojection to EPSG:32645 with 90m cells. Mesh is capped at 128×128. Source-wide analysis extrema are retained separately from display samples.
- DSM, orthometric height EGM2008; includes surface objects and vegetation. Terrain acquisition date is not satellite observation date. No flood-depth, HAND, hydrological-flow or independent vertical-accuracy claim.

CDSE documentation was reviewed before choosing the public fallback: https://documentation.dataspace.copernicus.eu/APIs/SentinelHub/Data/DEM.html ; https://documentation.dataspace.copernicus.eu/APIs/SentinelHub/Process/Examples/DEM.html ; https://documentation.dataspace.copernicus.eu/APIs/SentinelHub/Overview/Authentication.html . OAuth and CCM 30m authorization were not checked and are not claimed.

Slope uses the published Horn 3×3 derivative (1981; https://doi.org/10.1109/PROC.1981.11918), with a complete finite-data neighbourhood. Border and missing-neighbour cells remain unavailable. Geometry unit tests are software checks, not external validation of source heights.

## Local 3D dependency

Plotly.js v4.1.1 from https://cdn.plot.ly/plotly-4.1.1.min.js , as linked by https://plotly.com/javascript/getting-started/ . Surface API: https://plotly.com/javascript/reference/surface/ . MIT notice in `jai_extension/web/vendor/PLOTLY-LICENSE.txt`; distribution's embedded dependency notices retained. No CDN request is made by the running viewer.
