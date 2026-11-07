# Data access audit - 2026-10-14 IST

User confirmed: no local Nepal scenes; check public access.

| Probe | Observed response | Consequence |
|---|---|---|
| CDSE public STAC, broad Nepal search bbox 84.9,27.7,86.1,28.5, 10 Aug-10 Sep 2026 | 11 S1 GRD and 69 S2 L1C records | Metadata exists; bbox is exploratory, not final AOI |
| S1 pairs | Relative orbit 85 ascending: Aug 16/Aug 28; 121 descending: Aug 19/Aug 31; 19 descending: Aug 24/Sep 5 | Candidate pairs; footprint overlap and actual pixels still require verification |
| CDSE VV HTTPS asset, byte-range probe | HTTP 401 | Authenticated CDSE access needed |
| Planetary Computer RTC catalogue | 8 records for narrower exploratory bbox | Metadata only |
| PC unsigned VV asset | HTTP 409 PublicAccessNotPermitted | No anonymous raster access |
| PC collection documentation | Account required for RTC SAS tokens; terrain processing uses PlanetDEM | Requires account and permitted-input compatibility review |
| ohsome v1 metadata | HTTP 200; data through 2026-07-27T09:00Z | Pre-event history exists |
| ohsome v1 elements/geometry GET and documented POST | HTTP 403 from server | No historical features obtained |
| ohsome v2 docs | Current examples include authorization API key | Alternative setup requires access configuration |
| EMSR927 webpage | Generic page shell through web tool | Reference assets not yet retrieved; do not inspect labels before prediction freeze |

Responses saved under data/catalogue. Scripts: audit_catalogue.py, check_public_assets.py, diagnose_access.py.

Next action: configure a free Copernicus Data Space account through its official site; keep credentials/tokens out of chat and Git. Establish authenticated scene/preprocessing access and historical OSM extraction. Merely configuring an account does not implement our missing raw-data adapter.

Do not substitute catalogue thumbnails, another entrant's outputs, reference damage maps, or current OSM for permitted event inputs. Do not invent an event run to make the dashboard look complete.

Primary docs: https://documentation.dataspace.copernicus.eu/APIs/STAC.html ; https://planetarycomputer.microsoft.com/api/stac/v1/collections/sentinel-1-rtc ; https://docs.ohsome.org/ohsome-api/v2/how-to-guides/examples/notebook_extraction.html
