# Requirement traceability — provisional source verification
Official URL https://sih.gov.in/sih2026PS could not be retrieved by browsing this session. The user brief and https://sih2026.vuce.in/ps/SIH26167 (explicitly unofficial mirror) support this provisional matrix. Confirm wording on official portal before submission; do not claim full compliance.
| Requirement/theme | Current response | Status/evidence |
|---|---|---|
| RS adaptation | RSVQA pilot LoRA on already-adapted checkpoint | Experimental; TRAINING_REPORT/EVALUATION_REPORT |
| Single-image VQA | Local base+optional adapter | Implemented; VQA screenshots/predictions |
| Additional single-image task | NDVI spectral analysis | Implemented; not necessarily substitute for required captioning/grounding |
| Text-guided grounding | None | Planned |
| Multitemporal/change VQA | None | Planned; refusal has known gap |
| Optical-SAR joint analysis | None | Planned |
| Query-driven tool selection | Manual mode only | Planned; current branch structure not orchestration |
| Input compatibility validation | Single-image formats/bands/limits | Partial; no paired modality/date alignment |
| Visual evidence | NDVI mask | Implemented for spectral threshold only |
| Auditable execution | Model/revision/run ID or NDVI statistics | Partial; no unified registry trace |
| Confidence | No calibrated score | Not implemented |
| BigEarthNet.txt primary adaptation | Not used | Gap; our pilot uses RSVQA |
| VRSBench/RSVQA/CDVQA | Small RSVQA dev/diagnostic only | Partial; no VRSBench/CDVQA |
