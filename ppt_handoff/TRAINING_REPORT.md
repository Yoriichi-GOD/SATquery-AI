# Training dossier
Source: RSVQA LR v1.0, DOI 10.5281/zenodo.6344334, CC-BY-4.0 (Zenodo API checked). Published OSM-derived labels, not our manual annotations.
720 training Q&A / 120 images, six source scenes. 60 development Q&A / 20 images, one different source scene. Source images 256 x 256 RGB; TIFF-to-PNG RGB conversion; processor dynamically resizes into 64–128 visual-token bounds.
Categories: rural/urban 120 train, presence 240, comparison 360; dev 20 each.
Selection seed 26167; sample order shuffled once, then traversed once. Exact rows/hashes: raw/train.jsonl, raw/dev.jsonl, raw/learning_manifest.json.
Training/dev source scenes disjoint; official diagnostic test scene excluded; image hashes checked. This does not rule out adjacency or upstream checkpoint contamination.

One epoch/pass, 720 optimizer steps, batch 1, accumulation 1, effective batch 1.
AdamW, LR 0.0001, default betas (0.9,0.999), eps 1e-8, weight decay 0.01; no scheduler or warmup.
LoRA rank4 alpha8 dropout0.05, q_proj/v_proj, bias none; 544768 trainable.
BF16; SDPA; non-reentrant gradient checkpointing; clip grad norm 1; answer-only loss; no quantization.
GPU: RTX 5060 Laptop 8GB. Peak allocated recorded 4.454 GiB.
Recorded seconds: 190.024. IMPORTANT: timer starts before training and ends after adapted dev evaluation and save; it is NOT isolated training time. Baseline dev evaluation and reload are outside it.
First loss 0.84840059; final 0.00280530. Different examples: this endpoint difference is not a controlled loss improvement metric. See all 720 values and moving-average curve.
Saved: final adapter and processor; no per-epoch/intermediate checkpoint archive. Reload succeeded.
Historical training-running/terminal screenshots were not saved. We provide raw logged values and honestly labelled plots, not reconstructed terminal screenshots.
