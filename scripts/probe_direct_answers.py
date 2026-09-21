"""Development probe of assistant-prefill decoding; not a held-out benchmark."""
import json
from pathlib import Path
import sys
import time
from PIL import Image
import torch
from transformers import AutoProcessor, Qwen2VLForConditionalGeneration
from huggingface_hub import snapshot_download
root = Path(__file__).resolve().parents[1]
out = root / 'results/reliability-20260907/vqa'
manifest = json.loads((out / 'frozen-cases.json').read_text())
cases = [c for c in manifest['cases'] if c['category'] == 'description']
cases += manifest['cases'][:1] + manifest['cases'][6:7] + manifest['cases'][12:14]
model_id = manifest['model']
path = snapshot_download(model_id, revision=manifest['revision'], local_files_only=True)
processor = AutoProcessor.from_pretrained(path, use_fast=False, min_pixels=256*28*28, max_pixels=512*28*28,
                                         size={'shortest_edge':256*28*28,'longest_edge':512*28*28})
model = Qwen2VLForConditionalGeneration.from_pretrained(path, torch_dtype=torch.bfloat16,
            device_map={'':'cuda:0'}, attn_implementation='sdpa').eval()
pred = out / 'direct-answer-development-probe.jsonl'
assert not pred.exists(), 'Preserve previous trial'
for case in cases:
    desc = case['category'] == 'description'
    question = case['question'] + (' List only the main visible land-cover features. Do not explain their use or condition.' if desc else ' Answer with only rural or urban.' if case['category']=='rural_urban' else ' Answer with only yes or no.')
    messages = [{'role':'user','content':[{'type':'image'},{'type':'text','text':question}]}]
    prefix = 'Visible features: ' if desc else 'Therefore, the answer is '
    prompt = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True) + prefix
    inputs = processor(text=[prompt], images=[Image.open(case['image']).convert('RGB')], return_tensors='pt').to('cuda')
    started=time.perf_counter()
    with torch.inference_mode():
        output=model.generate(**inputs,max_new_tokens=64 if desc else 16,do_sample=False,temperature=None,top_p=None,top_k=None)
    answer=processor.batch_decode(output[:,inputs.input_ids.shape[1]:],skip_special_tokens=True)[0]
    row=dict(**case, effective_question=question, assistant_prefix=prefix, answer=answer,
             generated_tokens=int(output.shape[1]-inputs.input_ids.shape[1]), seconds=time.perf_counter()-started)
    with pred.open('a',encoding='utf-8') as handle:handle.write(json.dumps(row)+'\n')
    print(case['id'],repr(answer),flush=True)
