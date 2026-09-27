# Evidence storage policy

Source control contains current code, software tests, reports, provenance, benchmark summaries and per-question predictions. The CDVQA prediction files intentionally remain readable JSON so reviewers and CI can recompute reported metrics.

Raw satellite imagery, downloaded benchmark label collections, PDFs, intermediate raster/array outputs, model weights and ZIP archives remain local. `.gitignore` prevents new copies entering Git. [The local asset manifest](LOCAL_EVIDENCE_MANIFEST.json) records paths, sizes and SHA256 hashes for this publication; it is an inventory, not a download service. References to those assets in run records require the original local files or reacquisition from the cited provider. Do not interpret an omitted asset as independently reproduced by CI.

Existing tracked historical evidence is retained to avoid breaking earlier audit trails; the new ignore rules do not retroactively delete it. Earlier archives and the existing water checkpoint are not new uploads in this publication. This pass does not rewrite Git history.

CDVQA checkpoint backups: `CDVQA_MODEL_RELEASE.zip` in the local `cdvqa-results` deliverables directory and `/root/satquery/cdvqa/` in WSL. Dataset/encoder redistribution rights are not inferred from a code repository license. The trained CDVQA specialist remains separate from the main UI.

CI installs only `requirements-test.txt`, runs software regression, checks new-commit repository hygiene, and recomputes CDVQA OA/AA from saved predictions. It neither runs GPU models nor re-downloads official sensor products. Logs are uploaded as Actions artifacts even if a check fails.
