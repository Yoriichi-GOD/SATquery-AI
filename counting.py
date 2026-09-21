"""Bounded baseball/softball VQA counting, with abstention; no detector or boxes."""
from contextlib import nullcontext
import re
import time
from PIL import ImageOps

VERSION='baseball-two-view-v1'
PROMPT=('How many baseball fields are visible in this image? Count each distinct baseball or softball diamond once. '
        'Include a partial field only if its diamond is clearly identifiable. Do not count an infield and its outfield separately. '
        'Answer with one integer, or uncertain if you cannot distinguish the fields.')
WORDS=dict(zip('zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen twenty'.split(),range(21)))


def parse_count(raw):
    text=raw.strip().lower()
    final=re.search(r'\btherefore,?\s+the answer is\s+(.+)$',text,re.S)
    if final:text=final.group(1)
    text=text.strip().rstrip('.!?').strip()
    if text in WORDS:return WORDS[text]
    if re.fullmatch(r'\d{1,2}',text) and 0<=int(text)<=20:return int(text)
    return None


def count_fields(model,processor,image):
    import torch
    start=time.perf_counter()
    result=dict(policy=VERSION,kind='VQA estimate',views=[],count=None,withheld=True,
                limitation='Agreement between transformed views is not independent validation. Small, obscured or edge-cropped fields may be missed.',
                generated_tokens=0,generation_seconds=0.,max_new_tokens=32,peak_allocated_GiB=0.)
    if min(image.size)<96 or ImageOps.grayscale(image).entropy()<1.0:
        result.update(answer='Cannot determine a field count from this image: there is too little visible detail.',reason='insufficient_image_detail')
        return result
    torch.cuda.reset_peak_memory_stats()
    adapter_context=model.disable_adapter() if hasattr(model,'peft_config') else nullcontext()
    with torch.inference_mode(),adapter_context:
        for name,view in [('original',image),('mirrored',ImageOps.mirror(image))]:
            messages=[{'role':'user','content':[{'type':'image'},{'type':'text','text':PROMPT}]}]
            prompt=processor.apply_chat_template(messages,tokenize=False,add_generation_prompt=True)
            inputs=processor(text=[prompt],images=[view],return_tensors='pt').to('cuda')
            torch.cuda.synchronize();started=time.perf_counter()
            output=model.generate(**inputs,max_new_tokens=32,do_sample=False,temperature=None,top_p=None,top_k=None)
            torch.cuda.synchronize()
            tokens=int(output.shape[1]-inputs.input_ids.shape[1])
            raw=processor.batch_decode(output[:,inputs.input_ids.shape[1]:],skip_special_tokens=True)[0]
            parsed=parse_count(raw) if tokens<32 else None
            result['views'].append(dict(view=name,raw_answer=raw,count=parsed,generated_tokens=tokens,seconds=time.perf_counter()-started))
            result['generated_tokens']+=tokens
    counts=[view['count'] for view in result['views']]
    if counts[0] is not None and counts[0]==counts[1]:
        count=counts[0]
        result.update(count=count,withheld=False,reason='two_view_agreement',
            answer=f'{count} identifiable baseball/softball '+('diamond' if count==1 else 'diamonds')+' visible.\n\nVQA estimate; partial or obscured fields can affect the count.')
    else:
        result.update(answer='Cannot determine a reliable field count: the image checks were inconclusive. Try a clearer view with distinct ball diamonds.',reason='inconclusive_or_disagreeing_views')
    result['generation_seconds']=round(sum(v['seconds'] for v in result['views']),3)
    result['peak_allocated_GiB']=round(torch.cuda.max_memory_allocated()/2**30,3)
    return result
