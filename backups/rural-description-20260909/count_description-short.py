"""Separate descriptive inference; never used to calculate or validate a count."""
from contextlib import nullcontext
import time
PROMPT='Describe the main visible objects and their surroundings in one short sentence. Do not give counts or quantities.'
def add_count_description(job,model,processor,image):
    import torch
    started=time.perf_counter()
    job['count_answer']=job['answer']
    try:
        messages=[{'role':'user','content':[{'type':'image'},{'type':'text','text':PROMPT}]}]
        prompt=processor.apply_chat_template(messages,tokenize=False,add_generation_prompt=True)
        inputs=processor(text=[prompt],images=[image],return_tensors='pt').to('cuda')
        context=model.disable_adapter() if hasattr(model,'peft_config') else nullcontext()
        with torch.inference_mode(),context:
            output=model.generate(**inputs,max_new_tokens=64,do_sample=False,temperature=None,top_p=None,top_k=None)
        raw=processor.batch_decode(output[:,inputs.input_ids.shape[1]:],skip_special_tokens=True)[0].strip()
        tokens=int(output.shape[1]-inputs.input_ids.shape[1])
        job['description']={'raw_answer':raw,'prompt':PROMPT,'generated_tokens':tokens,'max_new_tokens':64,'truncated':tokens>=64,'seconds':round(time.perf_counter()-started,3),'policy':'separate-description-v1'}
        if raw:
            job['answer']+='\n\nScene description (model interpretation):\n'+raw
            if tokens>=64:job['answer']+='\nDescription reached the length limit.'
        job['trace'].append({'step':'Generate separate scene description','seconds':job['description']['seconds']})
        job['generated_tokens']+=tokens
        job['generation_seconds']=round(job['generation_seconds']+job['description']['seconds'],3)
        job['peak_allocated_GiB']=max(job.get('peak_allocated_GiB',0),round(torch.cuda.max_memory_allocated()/2**30,3))
    except Exception as exc:
        job['description']={'error':type(exc).__name__,'policy':'separate-description-v1'}
        job['answer']+='\n\nScene description unavailable; count result retained.'
