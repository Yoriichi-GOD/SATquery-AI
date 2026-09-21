
import json,csv,html,shutil
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
import tifffile
h=Path(__file__).resolve().parents[1]
r=json.loads((h/'raw/training_result.json').read_text())
loss=[x['loss'] for x in r['losses']]
fig,ax=plt.subplots(figsize=(10,4));ax.plot(range(1,721),loss,alpha=.3,lw=.8,label='Actual per-example loss');ax.plot(range(30,721),np.convolve(loss,np.ones(30)/30,mode='valid'),label='30-step moving average');ax.set(xlabel='Optimizer step',ylabel='Answer-token loss',title='Recorded LoRA pilot: one pass / 720 steps');ax.legend();fig.tight_layout();fig.savefig(h/'diagrams/training_loss.png',dpi=180);plt.close(fig)
fig,ax=plt.subplots(figsize=(10,5));x=np.arange(4)
for offset,values,label,color in [(-.25,[0,50,65,23/60*100],'Original','#777777'),(0,[75,75,85,47/60*100],'Adapter','#b78c36'),(.25,[55,80,50,37/60*100],'Dev majority','#466b7e')]:
 bars=ax.bar(x+offset,values,.24,label=label,color=color);ax.bar_label(bars,fmt='%.1f%%',fontsize=9)
ax.set_xticks(x,['Rural/urban','Presence','Comparison','Total']);ax.set_ylim(0,105);ax.set_ylabel('Exact-label accuracy (%)');ax.set_title('Development only: 60 questions / 20 images');ax.legend(loc='upper left');fig.tight_layout();fig.savefig(h/'diagrams/development_comparison.png',dpi=180);plt.close(fig)
a=tifffile.imread(h/'exports/ndvi.tif');fig,ax=plt.subplots(figsize=(7,6));im=ax.imshow(a,vmin=-1,vmax=1,cmap='RdYlGn');ax.set_title('Continuous NDVI — corrected Dehradun sample');ax.axis('off');fig.colorbar(im,ax=ax,label='NDVI (unitless)');fig.tight_layout();fig.savefig(h/'exports/ndvi-continuous.png',dpi=180);plt.close(fig)
def diagram(name,title,boxes,edges):
 fig,ax=plt.subplots(figsize=(12,7));ax.set(xlim=(0,12),ylim=(0,8));ax.axis('off');ax.set_title(title,fontsize=16,pad=15)
 for key,(x,y,text) in boxes.items():
  ax.add_patch(FancyBboxPatch((x-1.65,y-.48),3.3,.96,boxstyle='round,pad=.06',facecolor='#f1e5cf',edgecolor='#654d29'));ax.text(x,y,text,ha='center',va='center',fontsize=10)
 for a,b in edges:
  x,y,_=boxes[a];xx,yy,_=boxes[b];ax.annotate('',xy=(xx,yy+.52),xytext=(x,y-.52),arrowprops={'arrowstyle':'->','color':'#555555'})
 fig.tight_layout();fig.savefig(h/'diagrams'/name,dpi=180);plt.close(fig)
diagram('architecture_current.png','CURRENT — explicit modes, not automatic routing',{
 'u':(6,7,'Local browser UI\nIMPLEMENTED'),'a':(6,5.5,'FastAPI / serial worker\nIMPLEMENTED'),
 'v':(2.5,3.5,'RS VQA + optional LoRA\nIMPLEMENTED / EXPERIMENTAL'),'n':(9.5,3.5,'NDVI CPU arithmetic\nIMPLEMENTED'),
 'o':(6,1.3,'Answers / overlay / exports\nIMPLEMENTED within scope')},[('u','a'),('a','v'),('a','n'),('v','o'),('n','o')])
diagram('architecture_target.png','TARGET — planned components are explicitly labelled',{
 'u':(6,7,'Natural-language controller\nPLANNED'),'a':(6,5.4,'Validated tool registry\nPLANNED'),
 'v':(2,3.4,'VQA + NDVI\nIMPLEMENTED'),
 'g':(6,3.4,'Text grounding\nPLANNED'),'s':(10,3.4,'Temporal / optical-SAR\nPLANNED'),
 'e':(6,1.2,'Unified evidence / provenance\nPARTIAL')},[('u','a'),('a','v'),('a','g'),('a','s'),('v','e'),('g','e'),('s','e')])
diagram('ndvi_flow.png','ACTUAL NDVI FLOW — manual selection',{
 'u':(3,7,'Upload / geo.ingest\nretain TIFF + preview'),'a':(3,5.3,'Explicit NDVI mode\nPOST /api/ndvi'),
 'r':(3,3.5,'run_ndvi → geo.analyse\nread calibrated bands'),
 'n':(9,3.5,'geo.calculate\nvalidity + NDVI + threshold'),
 'o':(9,1.5,'Area / raster / overlay\npoll and display')},[('u','a'),('a','r'),('r','n'),('n','o')])
# Evidence viewer is explicitly a rendering of saved records, not a historic terminal.
sections=[]
for title,file in [('Training record','raw/training_result.json'),('Adapter config','raw/adapter_config.json'),('Independent audit','raw/independent-ndvi-check.json'),('Raster metadata','metrics/dehradun_metadata.json'),('Timing benchmark','metrics/ndvi_timing_summary.json')]:
 d=json.loads((h/file).read_text())
 if 'losses' in d:d={k:v for k,v in d.items() if k!='losses'}
 sections.append('<section><h2>'+title+'</h2><p>Saved record: '+file+'</p><pre>'+html.escape(json.dumps(d,indent=2))+'</pre></section>')
text='<!doctype html><meta charset="utf-8"><title>SATquery evidence records</title><style>body{font:18px system-ui;background:#eee;color:#222;margin:40px;max-width:1300px}section{background:white;padding:25px;margin:25px 0;break-inside:avoid}pre{font:15px monospace;white-space:pre-wrap}img{max-width:100%}</style><h1>SATquery — recorded engineering evidence</h1><p>Rendered saved records. Not a historical training-running screenshot.</p><img src="diagrams/training_loss.png">'+''.join(sections)
(h/'engineering.html').write_text(text)
print('Plots and evidence viewer written')
