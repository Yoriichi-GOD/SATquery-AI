# NDVI timing: 20 repetitions

| Clock | Mean s | Median s | P95 s | Min s | Max s |
|---|---:|---:|---:|---:|---:|
| server_reported_seconds | 0.057100 | 0.049000 | 0.066500 | 0.043000 | 0.209000 |
| client_submit_poll_seconds | 0.068872 | 0.059297 | 0.077678 | 0.055464 | 0.223925 |

Server timer: server.py ndvi_run sets started=time.time() after validation/busy lock, before executor.submit. run_ndvi sets seconds after geo.analyse returns and answer construction.
Includes queue wait, TIFF open/read/decode, band extraction, identity scaling on prepared physical-reflectance TIFF, masks, arithmetic, threshold, area, PNG overlay creation and NDVI GeoTIFF writing.
Excludes remote download, original source calibration/package creation, upload/RGB preview, final run JSON write, response serialization and browser rendering.
Client timer: immediately before POST /api/ndvi until completion observed by polling (10ms sleeps). Includes HTTP/poll overhead, not upload/rendering.
Warm OS cache; not flushed; 512x512x5 crop; first repetition retained. Server rounds to milliseconds; P95 uses NumPy linear interpolation. Not trained-model timings.
CPU Ryzen9 8940HX; GPU not invoked by NDVI. WSL visible RAM ~11.21GiB; host RAM separate. No minimum-RAM claim.
