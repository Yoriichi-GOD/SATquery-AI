"""Development count probe; related crops are not independent scenes."""
import json,re,time
from pathlib import Path
from PIL import Image,ImageOps,ImageDraw
import torch
from transformers import AutoProcessor,Qwen2VLForConditionalGeneration
from huggingface_hub import snapshot_download
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/reliability-20260907/counting'
im=Image.open(OUT/'sample.png').convert('RGB')
# References are visually annotated before generating predictions. Partials count
# only when the diamond is identifiable; each physical field is counted once.
cases=[('full',im,4),('mirror',ImageOps.mirror(im),4),
       ('rotate',im.transpose(Image.Transpose.ROTATE_90),4),
       ('top-single',im.crop((160,70,420,300)),1),
       ('right-single',im.crop((350,170,680,470)),1),
       ('top-and-right',im.crop((170,70,660,455)),None),
       ('blank',Image.new('RGB',(512,512),(80,100,60)),0),
       ('farmland',Image.open(ROOT/'results/reliability-20260907/vqa/fresh-245.png').convert('RGB'),0),
       ('river',Image.open(ROOT/'results/reliability-20260907/scenes/sundarbans-coast/rgb.png').convert('RGB'),0)]
manifest=[]
for name,image,reference in cases:
 image.save(OUT/f'{name}.png')
 manifest.append(dict(id=name,image=str(OUT/f'{name}.png'),reference=reference))
(OUT/'development-cases.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
path=snapshot_download('AdaptLLM/remote-sensing-Qwen2-VL-2B-Instruct',revision='7f5dd71bf0f40c282193d50160e848a387a08ffe',local_files_only=True)
processor=AutoProcessor.from_pretrained(path,use_fast=False,min_pixels=256*28*28,max_pixels=512*28*28,size={'shortest_edge':256*28*28,'longest_edge':512*28*28})
model=Qwen2VLForConditionalGeneration.from_pretrained(path,torch_dtype=torch.bfloat16,device_map={'':'cuda:0'},attn_implementation='sdpa').eval()
rows=[]
for case in manifest:
 question='How many baseball fields are visible in this image? Count each distinct baseball or softball diamond once. Include a partial field only if its diamond is clearly identifiable. Do not count an infield and its outfield separately. Answer with one integer, or uncertain if you cannot distinguish the fields.'
 messages=[{'role':'user','content':[{'type':'image'},{'type':'text','text':question}]}]
 prompt=processor.apply_chat_template(messages,tokenize=False,add_generation_prompt=True)
 inputs=processor(text=[prompt],images=[Image.open(case['image'])],return_tensors='pt').to('cuda')
 start=time.perf_counter()
 with torch.inference_mode():output=model.generate(**inputs,max_new_tokens=128,do_sample=False,temperature=None,top_p=None,top_k=None)
 answer=processor.batch_decode(output[:,inputs.input_ids.shape[1]:],skip_special_tokens=True)[0]
 row=dict(**case,question=question,answer=answer,seconds=time.perf_counter()-start)
 rows.append(row)
 (OUT/'development-predictions.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
 print(case['id'],case['reference'],repr(answer),flush=True)
