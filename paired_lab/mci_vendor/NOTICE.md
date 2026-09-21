Source: https://github.com/Chen-Yang-Liu/Change-Agent commit 68cbaa7f388b36e4fc10872f7a2911482d26ae5b.
Changes: omit unused mmseg/mmcv imports and separate ImageNet initialization because full MCI weights load strictly afterward; decoder tensor allocations follow input device instead of forcing CUDA. Architecture and pretrained weights are unchanged. Original source states academic use; checkpoint card states Apache-2.0.
Position-index tensors also follow their input device instead of forcing CUDA.
