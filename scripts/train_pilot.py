import json,time,math,gc
from pathlib import Path
import torch
from PIL import Image
from transformers import AutoProcessor,Qwen2VLForConditionalGeneration
from huggingface_hub import snapshot_download
from peft import LoraConfig,get_peft_model,PeftModel
root=Path('/root/satquery');out=root/'experiments/lora-pilot-v1';out.mkdir(parents=True,exist_ok=False)
model_id='AdaptLLM/remote-sensing-Qwen2-VL-2B-Instruct';revision='7f5dd71bf0f40c282193d50160e848a387a08ffe'
path=snapshot_download(model_id,revision=revision,local_files_only=True)
torch.manual_seed(26167)
proc=AutoProcessor.from_pretrained(path,use_fast=False,min_pixels=64*28*28,max_pixels=128*28*28,size={'shortest_edge':64*28*28,'longest_edge':128*28*28})
base=Qwen2VLForConditionalGeneration.from_pretrained(path,torch_dtype=torch.bfloat16,device_map={'':'cuda:0'},attn_implementation='sdpa')
def evaluate(m,label):
    m.eval();m.config.use_cache=True
    dev=[json.loads(x) for x in (root/'data/dev.jsonl').read_text().splitlines()]
    results=[]
    for r in dev:
        suffix=' Answer with only rural or urban.' if r['category']=='rural_urban' else ' Answer with only yes or no.'
        prompt=proc.apply_chat_template([{'role':'user','content':[{'type':'image'},{'type':'text','text':r['question']+suffix}]}],tokenize=False,add_generation_prompt=True)
        batch=proc(text=[prompt],images=[Image.open(r['image']).convert('RGB')],return_tensors='pt').to('cuda')
        with torch.inference_mode():generated=m.generate(**batch,max_new_tokens=16,do_sample=False,temperature=None,top_p=None,top_k=None)
        answer=proc.batch_decode(generated[:,batch.input_ids.shape[1]:],skip_special_tokens=True)[0]
        clean=' '.join(answer.strip().lower().split()).rstrip(' .!?')
        results.append({**r,'prediction':answer,'correct':clean==r['answer'].lower(),'valid_format':clean in (['rural','urban'] if r['category']=='rural_urban' else ['yes','no'])})
    (out/(label+'_predictions.jsonl')).write_text(''.join(json.dumps(r)+'\n' for r in results))
    score={'correct':sum(r['correct'] for r in results),'total':len(results),'invalid_format':sum(not r['valid_format'] for r in results),'per_category':{}}
    for cat in ['rural_urban','presence','comp']:
        rs=[r for r in results if r['category']==cat];score['per_category'][cat]={'correct':sum(r['correct'] for r in rs),'total':len(rs)}
    (out/(label+'_summary.json')).write_text(json.dumps(score,indent=2));print(label,json.dumps(score),flush=True)
    return score
baseline_score=evaluate(base,'baseline_dev')
config=LoraConfig(r=4,lora_alpha=8,lora_dropout=0.05,target_modules=['q_proj','v_proj'],task_type='CAUSAL_LM',bias='none')
model=get_peft_model(base,config);model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={'use_reentrant':False});model.enable_input_require_grads();model.config.use_cache=False;model.train()
params=[p for p in model.parameters() if p.requires_grad];optimizer=torch.optim.AdamW(params,lr=1e-4)
rows=[json.loads(x) for x in (root/'data/train.jsonl').read_text().splitlines()]
log=[];torch.cuda.reset_peak_memory_stats();start=time.perf_counter()
for i,r in enumerate(rows):
 suffix=' Answer with only rural or urban.' if r['category']=='rural_urban' else ' Answer with only yes or no.'
 user={'role':'user','content':[{'type':'image'},{'type':'text','text':r['question']+suffix}]}
 prompt=proc.apply_chat_template([user],tokenize=False,add_generation_prompt=True)
 full=proc.apply_chat_template([user,{'role':'assistant','content':[{'type':'text','text':r['answer']}]}],tokenize=False,add_generation_prompt=False)
 im=Image.open(r['image']).convert('RGB')
 prefix=proc(text=[prompt],images=[im],return_tensors='pt')
 batch=proc(text=[full],images=[im],return_tensors='pt').to('cuda')
 assert torch.equal(prefix.input_ids[0],batch.input_ids[0,:prefix.input_ids.shape[1]].cpu())
 labels=batch.input_ids.clone();labels[:,:prefix.input_ids.shape[1]]=-100;assert (labels!=-100).sum()>0
 result=model(**batch,labels=labels);loss=result.loss;assert torch.isfinite(loss)
 loss.backward();torch.nn.utils.clip_grad_norm_(params,1.0);optimizer.step();optimizer.zero_grad(set_to_none=True)
 item={'step':i+1,'loss':loss.item(),'tokens':int(batch.input_ids.shape[1]),'peak_allocated_GiB':torch.cuda.max_memory_allocated()/2**30};log.append(item)
 if (i+1)%30==0:print(json.dumps(item),flush=True)
 del result,loss,batch,labels
adapted_score=evaluate(model,'adapted_dev')
model.save_pretrained(out/'adapter');proc.save_pretrained(out/'processor')
summary={'purpose':'One-pass pilot; development comparison only, not held-out test performance','model':model_id,'revision':revision,'steps':len(rows),'baseline_dev':baseline_score,'adapted_dev':adapted_score,'trainable_parameters':sum(p.numel() for p in params),'seconds':time.perf_counter()-start,'peak_allocated_GiB':torch.cuda.max_memory_allocated()/2**30,'losses':log,'train_manifest':json.loads((root/'data/learning_manifest.json').read_text())['train']['sha256'],'visual_tokens':'64-128','rank':4,'lr':1e-4,'batch_size':1,'gradient_checkpointing':True,'answer_only_loss':True}
del optimizer,params,model,base;gc.collect();torch.cuda.empty_cache()
base=Qwen2VLForConditionalGeneration.from_pretrained(path,torch_dtype=torch.bfloat16,device_map={'':'cuda:0'},attn_implementation='sdpa').eval()
reloaded=PeftModel.from_pretrained(base,out/'adapter').eval();summary['adapter_reload_passed']=True
(out/'result.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2),flush=True)
