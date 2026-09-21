"""Isolated Grounding DINO -> SAM experiment. All coordinates are image pixels."""
import gc, hashlib, json, time
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

CATEGORIES={'stadium':'a stadium.', 'car':'a car.', 'aircraft':'an airplane.', 'building':'a building.', 'ship':'a ship.', 'sports field':'a sports field.'}
COLORS=[(231,189,92),(98,210,188),(132,161,255),(235,133,178),(255,166,99),(175,220,126)]

def suppress(boxes,scores,threshold=.5,limit=24):
    order=sorted(range(len(boxes)),key=lambda i:scores[i],reverse=True);kept=[]
    for i in order:
        a=boxes[i];area=max(0,a[2]-a[0])*max(0,a[3]-a[1])
        if area<4:continue
        duplicate=False
        for j in kept:
            b=boxes[j];inter=max(0,min(a[2],b[2])-max(a[0],b[0]))*max(0,min(a[3],b[3])-max(a[1],b[1]))
            union=area+max(0,b[2]-b[0])*max(0,b[3]-b[1])-inter
            if union and inter/union>threshold:duplicate=True;break
        if not duplicate:kept.append(i)
    return kept[:limit],len(kept)>limit

def process(source,out,category='stadium',threshold=.3,mode='both',progress=lambda s:None):
    import torch
    from transformers import AutoProcessor, AutoModelForZeroShotObjectDetection, SamProcessor, SamModel
    started=time.perf_counter();out=Path(out);out.mkdir(parents=True,exist_ok=True)
    records=json.loads(Path('/root/satquery/grounding-lab/models.json').read_text())
    if category not in CATEGORIES or not .15<=threshold<=.8 or mode not in ('both','boxes'):raise ValueError('Invalid lab selection')
    if not torch.cuda.is_available():raise RuntimeError('The lab needs the local GPU.')
    free,total=torch.cuda.mem_get_info()
    if free<3*1024**3:raise RuntimeError('The GPU has less than 3 GiB free. Close other GPU-heavy applications and retry; SatQuery already releases its VQA model before a lab run.')
    torch.set_num_threads(4);torch.cuda.reset_peak_memory_stats()
    image=Image.open(source).convert('RGB');w,h=image.size
    image.save(out/'source.png');trace=[]
    def mark(name,t):trace.append(dict(step=name,seconds=round(time.perf_counter()-t,3)))
    progress('Loading grounding specialist');t=time.perf_counter()
    proc=AutoProcessor.from_pretrained(records[0]['path'],local_files_only=True)
    model=AutoModelForZeroShotObjectDetection.from_pretrained(records[0]['path'],local_files_only=True).to('cuda').eval();mark('Load pinned Grounding DINO',t)
    progress('Finding candidate objects');t=time.perf_counter()
    inputs=proc(images=image,text=CATEGORIES[category],return_tensors='pt').to('cuda')
    with torch.inference_mode():outputs=model(**inputs)
    result=proc.post_process_grounded_object_detection(outputs,inputs.input_ids,box_threshold=threshold,text_threshold=.25,target_sizes=[(h,w)])[0]
    boxes=result['boxes'].detach().cpu().numpy();scores=result['scores'].detach().cpu().numpy()
    boxes[:,[0,2]]=np.clip(boxes[:,[0,2]],0,w);boxes[:,[1,3]]=np.clip(boxes[:,[1,3]],0,h)
    raw_candidates=[dict(box_xyxy=b.tolist(),score=float(s)) for b,s in zip(boxes,scores)]
    # Drop a nearly full-frame proposal only when it encloses a much tighter
    # proposal of the same queried category. Retain all raw proposals for audit.
    enclosing=[]
    for i,b in enumerate(boxes):
        area=(b[2]-b[0])*(b[3]-b[1])
        if area >= .97*w*h:
            enclosing.append(i);continue
        if area < .9*w*h:continue
        for j,c in enumerate(boxes):
            ca=(c[2]-c[0])*(c[3]-c[1])
            overlap=max(0,min(b[2],c[2])-max(b[0],c[0]))*max(0,min(b[3],c[3])-max(b[1],c[1]))
            if i!=j and 0<ca<.6*area and overlap/ca>.98:enclosing.append(i);break
    valid=[i for i in range(len(boxes)) if i not in enclosing]
    boxes=boxes[valid];scores=scores[valid]
    keep,capped=suppress(boxes,scores);raw_count=len(raw_candidates);boxes=boxes[keep].tolist();scores=scores[keep].tolist();mark('Detect, threshold, remove enclosing frame proposals and suppress duplicates',t)
    del model,proc,inputs,outputs,result;gc.collect();torch.cuda.empty_cache()
    detections=[dict(id=i+1,box_xyxy=b,detector_score=s) for i,(b,s) in enumerate(zip(boxes,scores))]
    masks=[]
    if mode=='both' and boxes:
        progress('Loading segmentation specialist');t=time.perf_counter()
        proc=SamProcessor.from_pretrained(records[1]['path'],local_files_only=True)
        model=SamModel.from_pretrained(records[1]['path'],local_files_only=True).to('cuda').eval();mark('Load pinned SAM Base',t)
        progress('Tracing object outlines');t=time.perf_counter()
        inputs=proc(images=image,input_boxes=[boxes],return_tensors='pt').to('cuda')
        with torch.inference_mode():
            embeddings=model.get_image_embeddings(inputs['pixel_values'])
            # Batch four boxes to bound GPU and output-mask memory.
            for offset in range(0,len(boxes),4):
                outputs=model(image_embeddings=embeddings,input_boxes=inputs['input_boxes'][:,offset:offset+4],multimask_output=True)
                qualities=outputs.iou_scores[0].detach().cpu().numpy()
                selected=qualities.argmax(axis=-1)
                chosen=torch.stack([outputs.pred_masks[0,i,int(k)] for i,k in enumerate(selected)])[None,:,None]
                full=proc.image_processor.post_process_masks(chosen.cpu(),inputs['original_sizes'].cpu(),inputs['reshaped_input_sizes'].cpu())[0][:,0].numpy().astype(bool)
                for j,mask in enumerate(full):
                    d=detections[offset+j];d.update(mask_pixels=int(mask.sum()),sam_predicted_iou=float(qualities[j,selected[j]]));masks.append(mask)
        mark('Box-prompted segmentation; choose highest SAM predicted IoU mask',t)
        del model,proc,inputs,outputs,embeddings;gc.collect();torch.cuda.empty_cache()
    progress('Preparing evidence views');t=time.perf_counter()
    box_image=image.copy();draw=ImageDraw.Draw(box_image);labels=np.zeros((h,w),dtype=np.uint16)
    rgba=np.zeros((h,w,4),dtype=np.uint8)
    for i,d in enumerate(detections):
        color=COLORS[i%len(COLORS)];b=d['box_xyxy'];draw.rectangle(b,outline=color,width=max(2,round(w/450)))
        label=f"{d['id']} {category} | score {d['detector_score']:.2f}";x,y=b[:2]
        draw.rectangle((x,max(0,y-17),min(w,x+len(label)*6+8),max(17,y)),fill=(15,15,15));draw.text((x+3,max(0,y-16)),label,fill=color)
        if i<len(masks):
            mask=masks[i];labels[(labels==0)&mask]=d['id'];rgba[mask]=(*color,95)
    overlay=Image.alpha_composite(image.convert('RGBA'),Image.fromarray(rgba)).convert('RGB')
    outline=ImageDraw.Draw(overlay)
    for i,mask in enumerate(masks):
        binary=Image.fromarray((mask*255).astype('uint8'));edge=np.asarray(binary)!=np.asarray(binary.filter(ImageFilter.MinFilter(3)))
        arr=np.asarray(overlay).copy();arr[edge]=COLORS[i%len(COLORS)];overlay=Image.fromarray(arr)
    box_image.save(out/'boxes.png');overlay.save(out/'outlines.png');Image.fromarray(labels).save(out/'instances.png')
    maskview=np.zeros((h,w,3),dtype=np.uint8)
    for i in range(len(detections)):maskview[labels==i+1]=COLORS[i%len(COLORS)]
    Image.fromarray(maskview).save(out/'masks.png')
    union=np.any(masks,axis=0) if masks else np.zeros((h,w),dtype=bool)
    np.savez_compressed(out/'masks.npz',masks=np.asarray(masks,dtype=bool).reshape((-1,h,w)))
    mark('Render boxes, outlines and instance masks',t)
    report=dict(version='grounding-lab-v1',category=category,prompt=CATEGORIES[category],mode=mode,
        image=dict(width=w,height=h,sha256=hashlib.sha256(Path(source).read_bytes()).hexdigest()),
        models=records,settings=dict(box_threshold=threshold,text_threshold=.25,nms_iou=.5,max_objects=24,reject_frame_area_fraction=.97,enclosing_area_fraction=.9,enclosed_smaller_ratio=.6),
        raw_candidates=raw_count,raw_proposals=raw_candidates,excluded_enclosing_proposals=enclosing,detections=detections,objects=len(detections),capped=capped,
        segmented_objects=len(masks),union_mask_pixels=int(union.sum()),total_image_pixels=w*h,
        union_mask_percent=round(100*int(union.sum())/(w*h),4),
        pixel_statistics_available=mode=='both',trace=trace,seconds=round(time.perf_counter()-started,3),
        peak_gpu_GiB=round(torch.cuda.max_memory_allocated()/2**30,3),
        limitations=['Experimental pretrained models; no remote-sensing fine-tuning or general accuracy claim.',
            'Detector score and SAM predicted IoU are model scores, not measured correctness.',
            'A mask follows a proposed box; it cannot prove the object identity.',
            'Pixel coverage is the union of predicted masks, not NDVI, hectares or surveyed area.',
            'Instance PNG assigns overlaps to the first score-ranked object; NPZ preserves overlapping masks.',
            'Small, obscured or densely packed objects may be missed. Zero candidates means none passed the settings, not proof of absence.'])
    (out/'result.json').write_text(json.dumps(report,indent=2));return report

if __name__=='__main__':
    import sys
    config=json.loads(Path(sys.argv[1]).read_text());out=Path(config['out'])
    def progress(stage):(out/'progress.json').write_text(json.dumps(dict(stage=stage)))
    try:process(**config,progress=progress)
    except Exception as exc:
        import traceback
        (out/'error.json').write_text(json.dumps(dict(error=str(exc))));traceback.print_exc();sys.exit(1)
