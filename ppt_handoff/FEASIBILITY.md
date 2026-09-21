# Measured feasibility
Local CPU Ryzen9 8940HX; RTX5060 Laptop8GB. Host physical RAM24752529408bytes (~23.05GiB); WSL reports11751124KiB (~11.21GiB).
Pinned snapshot files4896291212bytes (~4.90GB decimal), adapter directory2199814bytes (~2.20MB). These are file sizes, not measured download traffic or minimum RAM.
Stored checkpoint tensor elements2442359296; trainable LoRA544768.
Training experiment peak allocated4.454GiB, feasibility4.43GiB; PyTorch allocated memory is not total device use.
Current server RSS snapshot 2177980KiB; point-in-time, not peak. Full raw snapshot retained.
GPU inference/training is hardcoded CUDA in current runners; CPU VQA not tested. NDVI runs CPU without model inference.
Recorded VQA examples vary by prompt/output length/load state: one saved baseball request17.093s total/4.601s generation, another0.368s total/.329s generation. These are illustrative runs, NOT controlled paired benchmarks. See raw/vqa_completed_runs.json. Do not advertise one universal VQA latency.
NDVI20-run median.049s server, .059297s client submit/poll. Full timing scope in PERFORMANCE_BENCHMARKS.
Cold startup/model-load time not isolated; model lazily loads on first VQA. Current app startup is not a formal availability benchmark.
Image limits20MB; ordinary RGB25million pixels; labelled TIFF4194304pixels/16bands. No hosted model API needed after downloads. Loopback bind and local execution are not a security certification.
