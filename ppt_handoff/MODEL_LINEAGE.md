# Model lineage and ownership
Qwen2-VL-2B → Qwen2-VL-2B-Instruct → AdaptLLM remote-sensing-Qwen2-VL-2B-Instruct → our lora-pilot-v1 adapter.

The starting checkpoint already contains remote-sensing post-training. We did not create Qwen's architecture, its pretraining, the upstream RS adaptation, LoRA, RSVQA or NDVI. The upstream model card describes its ancestry and links its RS instruction data: https://huggingface.co/AdaptLLM/remote-sensing-Qwen2-VL-2B-Instruct .

Our work: select/pin the checkpoint; construct a documented RSVQA-LR subset and source-scene-separated development split; train the adapter; measure paired development outputs; implement the local app and deterministic geospatial workflow; audit/calibrate the sample and independently reproduce its measurement.

We trained LoRA matrices attached to q_proj and v_proj, rank 4, 544768 trainable parameters. The original model weights remain frozen. No full-model finetune and no new foundation model.

Training inputs: RGB images with Qwen chat templates and restricted answer-label suffixes; assistant-answer-only loss. Inference loads pinned base, then PEFT adapter when selected. Baseline uses disable_adapter() after an adapter has been attached. Pilot modes use 64–128 visual tokens and max 16 output tokens; general baseline UI uses 256–512 and max 128, so those UI modes are not an apples-to-apples benchmark.
