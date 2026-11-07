# Sources, method foundations and independent-reference compatibility

Reviewed 5 November 2026. Exact local source identities are in the run manifests and
[dataset registry](../../research/datasets/registry.json). Access to a reference does not make it
class-compatible, field truth or permissible training data. No reference labels were used to tune thresholds.

| Source | Consulted methodological relevance | What this work does not inherit |
|---|---|---|
| Barnes, Lehman & Mulla (2014), [Priority-Flood](https://rbarnes.org/sci/2014_depressions.pdf), DOI 10.1016/j.cageo.2013.04.024 | Edge-inward priority-queue depression filling; explicit flat routing | Published performance or validation of this implementation on real flood propagation |
| Nobre et al. (2011), [HAND](https://www.esalq.usp.br/lcb/lerf/divulgacao/recomendados/artigos/nobre2011.pdf), DOI 10.1016/j.jhydrol.2011.03.051 | Relative height to drainage reached along the flow path | Water depth, dynamic inundation, or transfer of Amazonian landscape calibration to Nepal/Delhi |
| Lehner & Grill (2013), [HydroRIVERS methods and documentation](https://www.hydrosheds.org/products/hydrorivers), DOI 10.1002/hyp.9740 | Directed reach topology and basin relationships | Street-drain topology; the product's 15 arc-second foundation is too coarse for that role |
| [Rasterio feature documentation](https://rasterio.readthedocs.io/en/stable/topics/features.html) | Native mask polygonization and explicit centre/all-touched rasterization rules | Physical co-registration from matching headers |
| [OpenCV similarity-transform documentation](https://docs.opencv.org/4.11.0/d9/d0c/group__calib3d.html) | SIFT matching plus train-only RANSAC similarity estimation | Trustworthy absolute ground control or sensor cross-registration |
| Scheffler et al. (2017), [AROSICS documentation](https://danschef.git-pages.gfz-potsdam.de/arosics/doc/about.html) | Reviewed frequency-domain global/local shift diagnostics and masks | AROSICS execution: not installed/run; current diagnostic deliberately reuses existing OpenCV |
| Pekel et al. (2016), DOI [10.1038/nature20584](https://doi.org/10.1038/nature20584); [JRC GSW guide](https://developers.google.com/earth-engine/tutorials/tutorial_global_surface_water_01) | Historical/permanent-water context distinct from event change | A 2026 event-water reference; this layer was not downloaded or used in scoring |

## Nepal source inspection

[Copernicus EMSR927](https://mapping.emergency.copernicus.eu/activations/EMSR927/) AOI01 GRA v1
was read from the original retained GeoPackage, SHA-256
`56b3d9e0ea870a025492d84b61a0462b21c486bef52a903ccd0bb00b33c17920`.
Its event polygon is `6-Mass Movement` / `Landslide`, not a water-only label or the SATquery vegetation-loss proxy.
The 433 building points have Destroyed/Damaged/Possibly damaged grades and no known-negative grade.
Building precision therefore cannot be computed by treating unlisted buildings as negatives.

The 31 road segments contain 14 Destroyed, 6 Possibly damaged and 11 No visible damage grades.
The source table records pre-event OSM, a Pleiades Neo pre-event image dated 29 November 2025,
and a WorldView-3 post-event image dated 27 August 2026 at 05:05 UTC. Source geometry and grading
are different evidence roles. The published AOI and post-image footprint constrain evaluation coverage.
The diagnostic excludes six uncertain grades and three unsupported/too-short segments, leaving 22 fragments.
It ranks explicit reference grades for inspection; it does not equate connectivity/exposure with damage.

[UNOSAT Product 4259](https://unosat.org/products/4259/) was inspected from its retained FileGDB/archive.
The reference documentation identifies cumulative satellite-detected mudflow/rockflow; field validation is zero
in the inspected extent/affected-building attributes. The archive SHA-256 is
`1c09bd5cff4e5dee870cd8413af0eb036e0dcd75d254cf1a337aa49096aaec2e`.
This is not a class-compatible water/debris segmentation reference. The old external-agreement results
remain historical diagnostics and were not relabelled as new validated accuracy.

[Public Copernicus DEM](https://registry.opendata.aws/copernicus-dem/) is a historical DSM including surface
objects, released here as GLO-90. Metric resampling does not improve its native 90 m information scale.
EGM2008 orthometric heights and a finite buffered domain are explicit in the manifest.
No rainfall, discharge, breach forcing, rheology, calibrated hydraulic solver or dynamic validation is supplied.

## Urban methods and data-access findings

Yadav et al. (2025), [Varanasi flood mapping](https://doi.org/10.1007/s44327-025-00051-9), examines
2017–2023 observations with rainfall/water-table context. It informs temporal/river-corridor study design;
its published exposure totals are not directly comparable to this prototype's small windows.
The supplied [Assi River article](https://www.mdpi.com/2673-7086/5/4/69) could not be fully retrieved
through the publisher during this run (429/access failure). No unverified UAV method or novelty claim is adopted.

The [CSE Sangam Vihar factsheet landing page](https://www.cseindia.org/water-and-wastewater-visioning-for-dense-unplanned-urban-settlements-a-case-of-sangam-vihar-delhi-12617)
describes settlement water/wastewater/stormwater issues. It is contextual literature, not an ingested,
surveyed geospatial drainage reference. Parcel legality is not inferred from report language or spectral change.
The official Delhi [draft drainage master plan](https://ifc.delhi.gov.in/ifc/draft-drainage-master-plan)
and [master report](https://ifc.delhi.gov.in/sites/default/files/inline-files/main_report_dmp_version51.pdf)
provide potential follow-up material. A similarly named Sangam Vihar in northern Delhi appears in a surveyed
map search; it must not be confused with the southern study window. No verified georeferenced local drain/outlet
network or suitable street-scale bare-earth elevations was obtained.

Actual urban execution acquired three public GLO-90 tiles (about 14.9 MB combined), retained hashes/license
links and processed both declared windows. Earth Search STAC queries found candidate Sentinel-2 metadata
for 2020 and 2025. Responses are explicitly truncated discovery, not downloaded/processed imagery or an
urbanization measurement. Categorical temporal-map ingestion is tested; no genuine urban built-up maps
or independent waterlogging labels were supplied. H5 remains untested.

The next external dependency is suitable licensed, georeferenced reference/terrain data and expert review
of alignment, target semantics and drain/outlet completeness. A report image must be georeferenced and
validated before becoming a reference. No high-resolution data access or legal authorization is invented.
