"""Render scientific figures directly from measured outputs, never hand-entered scores."""
import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import rasterio

from research.terrain_exposure.io import save_json,sha256


def figures(experiment,terrain_run,output):
    experiment=Path(experiment);terrain_run=Path(terrain_run);output=Path(output)
    output.mkdir(parents=True,exist_ok=False)
    report=json.loads((experiment/'metrics.json').read_text())
    methods=['A_image_only','B_image_temporal','C_temporal_terrain','D_full_graph','proximity_only','terrain_only']
    labels=['A\nSingle date','B\nTemporal','C\n+ Terrain','D\nFull graph','Proximity','Terrain only']
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False})
    fig,axes=plt.subplots(1,2,figsize=(11.5,4.3),layout='constrained')
    for ax,metric,title in zip(axes,['average_precision','precision_at_10'],['Threshold average precision','Precision at 10 (tie-aware)']):
        values=[report['results'][method][metric] for method in methods]
        ax.bar(np.arange(len(methods)),values,color=['.65','.55','.4','.15','.75','.8'],edgecolor='black',linewidth=.5)
        ax.set(xticks=np.arange(len(methods)),xticklabels=labels,ylim=(0,1),title=title,ylabel='Screening association')
        for i,value in enumerate(values):
            if value is not None:ax.text(i,value+.025,f'{value:.3f}',ha='center',fontsize=9)
    fig.suptitle(f'Nepal road-grade screening diagnostic: {report["common_denominator"]} fragments\nNot exposure/damage accuracy; previously inspected event, unverified registration',fontsize=11)
    for extension in ['png','pdf','svg']:fig.savefig(output/('screening-comparison.'+extension),dpi=220)
    plt.close(fig)
    changes=report['paired_differences']
    fig,ax=plt.subplots(figsize=(8,4.8),layout='constrained')
    names=list(changes)
    for i,name in enumerate(names):
        item=changes[name];interval=item['spatial_interval']['interval'];value=item['average_precision_difference']
        if interval is not None:ax.plot(interval,[i,i],color='.3',linewidth=2)
        if value is not None:ax.plot(value,i,'ko',markersize=5)
    ax.axvline(0,color='.6',linestyle='--',linewidth=.8)
    ax.set(yticks=range(len(names)),yticklabels=[n.replace('__to__',' → ').replace('_',' ') for n in names],
           xlabel='Paired difference in average precision',title='Conditional 95% spatial-block bootstrap intervals\nOne event; excludes registration and reference uncertainty')
    for extension in ['png','pdf','svg']:fig.savefig(output/('paired-differences.'+extension),dpi=220)
    plt.close(fig)
    arrays=[]
    for name in ['original_dem','hand_m','fill_depth']:
        with rasterio.open(terrain_run/(name+'.tif')) as ds:arrays.append(ds.read(1,masked=True))
    fig,axes=plt.subplots(1,3,figsize=(11,4),layout='constrained')
    for ax,array,title,cmap in zip(axes,arrays,['Genuine historical DSM (m)','Flowpath HAND (m)','Conditioning fill (m)'],['terrain','viridis','magma']):
        image=ax.imshow(array,cmap=cmap);fig.colorbar(image,ax=ax,shrink=.7);ax.set_title(title,fontsize=10)
        ax.set_xlabel('90 m grid column');ax.set_ylabel('90 m grid row')
    fig.suptitle('Syapru terrain derivations: truncated buffered domain; potential drainage only',fontsize=11)
    for extension in ['png','pdf','svg']:fig.savefig(output/('terrain-derivations.'+extension),dpi=220)
    plt.close(fig)
    save_json(output/'manifest.json',{'source_metrics_sha256':sha256(experiment/'metrics.json'),
        'source_terrain_manifest_sha256':sha256(terrain_run/'manifest.json'),
        'files':{p.name:sha256(p) for p in sorted(output.iterdir()) if p.is_file()},
        'method':'Matplotlib from actual evaluation files; no manually entered performance values'})


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--experiment',required=True);p.add_argument('--terrain-run',required=True);p.add_argument('--output',required=True)
    a=p.parse_args();figures(a.experiment,a.terrain_run,a.output)
