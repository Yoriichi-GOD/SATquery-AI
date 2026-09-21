# Geospatial input
Reader preserves original TIFF, explicit band mapping/descriptions, scales/offsets, nodata, size, CRS, affine, bounds, WGS84 envelope, resolution and optional source/acquisition tags.
Datatype/count are known to reader but not dedicated API fields. geo.coordinate is a tested pixel-centre helper, not a UI coordinate-picker feature.
Projected metre-based area only; no geographic/geodesic or terrain area.
Dehradun: Sentinel2A,25Nov2021,EPSG32643 (not32644),512x512,10m,five packaged bands RGB/NIR/SCL. SCL nearest20m→10m.
Projected bounds[788360,3353910,793480,3359030]. WGS84 envelope[77.99766300376905,30.281402875774386,78.05225589782314,30.328772451280432].
Full dump: metrics/dehradun_metadata.json. Source: raw/reference-item.json.
GeoTIFF limits20MB,4194304pixels,16bands; labelled RGB required. PNG/JPEG/WebP <=25million pixels. Unit tags from user files are trusted, not externally certified.
