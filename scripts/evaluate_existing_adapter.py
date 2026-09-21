"""Fresh-image check of existing pilot weights; no training or weight selection."""
import json
from pathlib import Path
import re
import sys
import time
from PIL import Image
import torch
from transformers import AutoProcessor,Qwen2VLForConditionalGeneration
from peft import PeftModel
from huggingface_hub import snapshot_download
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root))
from vqa_answers import present_answer
out=root/'results/reliability-20260907/vqa'
manifest=json.loads((out/'frozen-cases.json').read_text())
cases=[c for c in manifest['cases'] if c['reference'] is not None]
path=snapshot_download(manifest['model'],revision=manifest['revision'],local_files_only=True)
processor=AutoProcessor.from_pretrained(path,use_fast=False,min_pixels=64*28*28,max_pixels=128*28*28,
 size={'shortest_edge':64*28*28,'longest_edge':128*28*28})
model=Qwen2VLForConditionalGeneration.from_pretrained(path,torch_dtype=torch.bfloat16,
 device_map={'':'cuda:0'},attn_implementation='sdpa').eval()
model=PeftModel.from_pretrained(model,'/root/satquery/experiments/lora-pilot-v1/adapter').eval()
target=out/'existing-adapter-fresh-predictions.jsonl'
assert not target.exists()
rows=[]
for case in cases:
 question=case['question']+(' Answer with only rural or urban.' if case['category']=='rural_urban' else ' Answer with only yes or no.')
 messages=[{'role':'user','content':[{'type':'image'},{'type':'text','text':question}]}]
 prompt=processor.apply_chat_template(messages,tokenize=False,add_generation_prompt=True)
 inputs=processor(text=[prompt],images=[Image.open(case['image']).convert('RGB')],return_tensors='pt').to('cuda')
 started=time.perf_counter()
 with torch.inference_mode():output=model.generate(**inputs,max_new_tokens=16,do_sample=False,temperature=None,top_p=None,top_k=None)
 answer=processor.batch_decode(output[:,inputs.input_ids.shape[1]:],skip_special_tokens=True)[0]
 normalized=re.sub(r'[.!?]+$','',' '.join(answer.lower().strip().split()))
 validation=present_answer(case['question'],answer,truncated=output.shape[1]-inputs.input_ids.shape[1]>=16)
 row=dict(**case,raw_answer=answer,effective_question=question,validation=validation,
          raw_exact_correct=normalized==case['reference'],display_exact_correct=validation['answer'].lower()==case['reference'],
          seconds=time.perf_counter()-started)
 rows.append(row)
 with target.open('a',encoding='utf-8') as handle:handle.write(json.dumps(row)+'\n')
 print(case['id'],repr(answer),'reference',case['reference'],flush=True)
summary=dict(total=len(rows),raw_exact_correct=sum(r['raw_exact_correct'] for r in rows),
 display_exact_correct=sum(r['display_exact_correct'] for r in rows),
 by_category={cat:dict(total=sum(r['category']==cat for r in rows),correct=sum(r['raw_exact_correct'] for r in rows if r['category']==cat)) for cat in ['presence','rural_urban']},
 scope='Existing adapter, 24 fresh images from official test scene, not adapter train/dev. Same frozen cases as prompt diagnostic; not an additional independent test. 64-128 visual tokens, 16 output tokens: deployment pilot settings. Baseline diagnostic used different prompts/token limits, so this is not a controlled adapter-only ablation. Published labels may be noisy; upstream model exposure unknown.')
(out/'existing-adapter-fresh-summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
print(json.dumps(summary,indent=2),flush=True)
