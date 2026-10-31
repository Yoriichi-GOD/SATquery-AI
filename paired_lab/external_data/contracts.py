"""Conservative external-entry contracts derived from the current specialist code."""
import csv
import io
from datetime import datetime
from pathlib import Path
import numpy as np

S1=['VV','VH']
S2=['B02','B03','B04','B05','B06','B07','B08','B8A','B11','B12']
L1C=['B01','B02','B03','B04','B05','B06','B07','B08','B8A','B09','B10','B11','B12']
REGISTRY = {
    'vqa':dict(name='Qwen2-VL optical description',workflow='vqa',files=1,source=['geo.py:ingest','paired_lab/single_bridge.py'],scope='Optical interpretation; no measured object count or geospatial accuracy.'),
    'ndvi':dict(name='Calibrated Red/NIR NDVI',workflow='numerical',files=1,source=['geo.py:analyse'],scope='Thresholded spectral index, not vegetation ground truth.'),
    'spectral_pair':dict(name='Dated Sentinel-2 spectral comparison',workflow='numerical',files=2,source=['paired_lab/spectral_pair.py:validate'],scope='Quality-valid NDVI/NDWI differences, not land-cover conversion.'),
    'temporal':dict(name='MCI road/building change',workflow='temporal',files=2,source=['paired_lab/inputs.py:validate','paired_lab/mci.py'],scope='Prepared RGB road/building change masks; caption is interpretation.'),
    'water_map':dict(name='WaterUNet optical/SAR water',workflow='water',files=2,source=['paired_lab/inputs.py:validate','paired_lab/flood.py'],scope='Single-date water, including permanent water; no flood-depth inference.'),
    'optical_sar':dict(name='BIFOLD multilabel land cover',workflow='land-cover',files=2,source=['paired_lab/inputs.py:_legacy_validate','paired_lab/engine.py:fusion'],scope='Scene-level multilabel classes, never pixel segmentation.'),
    'sar_scene':dict(name='Sentinel-1 SAR scene classes',workflow='sar-scene',files=1,source=['paired_lab/sar_single.py:validate'],scope='Scene-level classes, not unrestricted radar VQA.'),
    'cdvqa':dict(name='Experimental CDVQA',workflow='cdvqa',files=2,source=['paired_lab/cdvqa_bridge.py','paired_lab/cdvqa-questions.json'],scope='Exact supported question templates; user-declared alignment/order.'),
    'flood_lab':dict(name='Flood Lab prepared SAR',workflow=None,files=2,source=['SatQuery---Flood-Lab/floodlab/core.py','SatQuery---Flood-Lab/floodlab/pipeline.py'],scope='Prepared event/OSM bundle required; arbitrary TIFFs cannot replace it.'),
    'terrain':dict(name='Metric elevation context',workflow='numerical',files=1,source=['jai_extension/terrain.py:slope_degrees'],scope='Known metre elevation units and projected grid; no automatic reprojection.'),
}


def asset_inventory():
    # The existing read-only provisioner checks pinned manifests/dependencies.
    import sys
    from runtime_paths import PAIRED
    from scripts.preflight import check
    vendor=PAIRED/'deps'
    # The existing engine uses this explicitly configured dependency directory.
    # Include it consistently in the CLI and isolated-worker audit as well.
    if vendor.is_dir() and str(vendor) not in sys.path:sys.path.insert(0,str(vendor))
    result={}
    for key, spec in REGISTRY.items():
        if spec['workflow'] is None:
            result[key]=dict(status='unsupported_external_adapter',assets=[],reason='Use the existing prepared Flood Lab event workflow; arbitrary bundles are not executed here.')
        else:
            report=check(spec['workflow'],False,False)
            result[key]=dict(status=report['status'],assets=report['assets'],dependencies=report['dependencies'],
                limitation=report['limitation'])
    return result


def band_names(record):
    names=record.get('bands',[])
    aliases={'b04':'red','b4':'red','red':'red','b03':'green','b3':'green','green':'green',
        'b02':'blue','b2':'blue','blue':'blue','b08':'nir','b8':'nir','nir':'nir','scl':'scl'}
    colour=record.get('colorinterp',[])
    return [aliases.get((name or '').lower(),name) if name else colour[i] if i<len(colour) and colour[i] in ('red','green','blue') else None for i,name in enumerate(names)]


def preflight(dataset, selected=None, assets=None, declarations=None,root=None):
    declarations=declarations or {}
    files=[f for f in dataset['files'] if f.get('role','input')=='input' and f.get('raster')]
    if selected is not None:files=[f for f in files if f['id'] in selected]
    needs_selection=len(files)>2
    if needs_selection:files=[]
    common=None
    if len(files)==2 and root is not None:
        a,b=[f['raster'] for f in files]
        if a['crs']==b['crs'] and a['width']==b['width'] and a['height']==b['height'] and a['transform']==b['transform'] and a['full_pixels']<=1_048_576:
            import rasterio
            from .common import contained
            from .raster import ENV,windows
            with rasterio.Env(**ENV),rasterio.open(contained(root,files[0]['path'])) as left,rasterio.open(contained(root,files[1]['path'])) as right:
                common=0
                for window in windows(left.width,left.height):
                    valid=np.ones((int(window.height),int(window.width)),dtype=bool)
                    for ds in (left,right):
                        for band in ds.indexes:
                            arr=ds.read(band,window=window,masked=True);valid&=~np.ma.getmaskarray(arr)&np.isfinite(arr.data)
                    common+=int(valid.sum())
    reports=[]
    for key,spec in REGISTRY.items():
        rows=[]
        def add(parameter,expected,observed,status,blocks=True,explanation='',step='Prepare a new artifact explicitly; retain the original.'):
            rows.append(dict(parameter=parameter,expected=expected,observed=observed,status=status,
                severity='blocking' if blocks and status not in ('MATCH','NOT_APPLICABLE') else 'warning' if status not in ('MATCH','NOT_APPLICABLE') else 'informational',
                explanation=explanation or ('Contract verified from inspected data.' if status=='MATCH' else 'This requirement has not been established.'),
                suggested_preparation=step if status not in ('MATCH','NOT_APPLICABLE') else 'None.',
                prevents_execution=bool(blocks and status not in ('MATCH','NOT_APPLICABLE'))))
        def requirement(parameter,expected,observed,passed,blocks=True):
            status='MISSING' if observed is None or observed=='' or observed==[] else 'MATCH' if passed else 'MISMATCH'
            add(parameter,expected,observed,status,blocks)
        requirement('dataset.input_count',spec['files'],len(files),len(files)==spec['files'])
        rejected=[dict(name=f['name'],error=f.get('error'),state=f['state']) for f in dataset['files'] if f.get('role')=='input' and f['state']!='INSPECTED' and (selected is None or f['id'] in selected)]
        if rejected:add('dataset.input_integrity','Every selected input inspected successfully',rejected,'MISMATCH',True,'A rejected/corrupt input is not a compatible model source.','Supply intact original bytes and rerun inspection; retained failures are available in the inventory.')
        if needs_selection:add('dataset.case_selection','Select at most two input TIFFs for one case','More than two inputs; batch evaluation is deferred','MISSING',True,'Files were inventoried without guessing which pair belongs together.','Choose the exact files for this analysis case.')
        for fi,f in enumerate(files):
            r=f['raster'];tags=r['tags'];p=f['name']+'.';n=r['width']*r['height'];bands=band_names(r)
            add(p+'driver','GTiff',r['driver'],'MATCH' if r['driver']=='GTiff' else 'MISMATCH')
            requirement(p+'structure_readable','Every native raster window readable',r.get('all_blocks_read'),r.get('all_blocks_read') is True)
            requirement(p+'input_bytes','At most 20 MiB for the existing bounded specialist',f['bytes'],f['bytes']<=20*1024**2,key!='flood_lab')
            requirement(p+'dimensions','At most 1,048,576 pixels', [r['height'],r['width']],n<=1_048_576)
            requirement(p+'band_limit','At most 14 bands',r['count'],r['count']<=14)
            add(p+'metadata_completeness','Complete contract metadata without truncation',r.get('metadata_truncated',False),'MISMATCH' if r.get('metadata_truncated') else 'MATCH',True,
                'Oversized metadata was bounded during inspection; it cannot silently stand in for the full input contract.','Reduce excessive nonessential metadata in a separate preparation artifact, preserving the original.')
            requirement(p+'transform','Finite nonsingular affine',r['transform'],r['valid_transform'],key not in ('vqa','cdvqa'))
            requirement(p+'CRS','Declared spatial reference',r['crs'],bool(r['crs']),key not in ('vqa','ndvi','cdvqa'))
            requirement(p+'scale_offset','Finite scale and offset for every band', [r['scales'],r['offsets']],all(v is not None for v in r['scales']+r['offsets']))
            partial=key in ('ndvi','water_map','spectral_pair','terrain')
            requirement(p+'valid_pixels','At least one valid pixel' if partial else 'Fully finite/valid native input',r['common_valid_pixels'],r['common_valid_pixels']>0 if partial else r['common_valid_pixels']==r['full_pixels'])
            add(p+'nodata_nan_infinity','Reported, never silently filled',dict(nodata=r['nodata_repr'],band_statistics=r['statistics'],valid_fraction=r['valid_fraction']),'MATCH',False)
            add(p+'storage','Metadata inspected; decode block at most 16 MiB',dict(compression=r['compression'],tiled=r['tiled'],blocks=r['blocks'],overviews=r['overviews'],layout=r['layout']),'MATCH',False)
            add(p+'source_authenticity','Independent provenance verification',tags.get('source_item') or tags.get('source_id'),'UNKNOWN',False,
                'Sensor/product tags and metadata matching do not authenticate the pixels.','Supply acquisition records and an independent provenance review.')
            add(p+'numerical_range','Recorded native values; no unit inference from magnitude',r['statistics'],'MATCH',False)
            add(p+'acquisition_date','Actual acquisition date',tags.get('acquisition_date') or tags.get('acquired'),'MATCH' if tags.get('acquisition_date') or tags.get('acquired') else 'MISSING',False)
            if key in ('vqa','ndvi','spectral_pair'):
                required=['red','green','blue'] if key=='vqa' else ['red','nir'] if key=='ndvi' else ['red','green','nir','scl']
                requirement(p+'band_identities',required,r['bands'],all(v in bands for v in required) and len(bands)==len(set(bands)))
            if key in ('ndvi','spectral_pair'):
                requirement(p+'calibration','surface_reflectance',tags.get('reflectance_units'),tags.get('reflectance_units')=='surface_reflectance')
                requirement(p+'quality_mask','Genuine SCL labels; retained values 4,5,6,7','scl' if 'scl' in bands else None,'scl' in bands,key=='spectral_pair')
                if 'scl' in bands:
                    scl=bands.index('scl');requirement(p+'SCL_scale_offset',[1,0],[r['scales'][scl],r['offsets'][scl]],r['scales'][scl]==1 and r['offsets'][scl]==0)
            if key=='spectral_pair':requirement(p+'sensor','Sentinel-2 or Sentinel-2 L2A',tags.get('sensor'),tags.get('sensor') in ('Sentinel-2','Sentinel-2 L2A'))
            if key in ('temporal','cdvqa'):
                rgb=[str(v).lower() if v else v for v in r['bands']] if key=='temporal' else bands
                requirement(p+'RGB_order',['red','green','blue'],dict(descriptions=r['bands'],colour_interpretation=r['colorinterp']),rgb==['red','green','blue'])
                requirement(p+'RGB_dtype','uint8',r['dtypes'],all(t=='uint8' for t in r['dtypes']))
                requirement(p+'RGB_scale_offset','Identity', [r['scales'],r['offsets']],all(v==1 for v in r['scales']) and all(v==0 for v in r['offsets']))
                if key=='temporal':requirement(p+'checkpoint_dimensions',[256,256],[r['height'],r['width']],r['height']==r['width']==256)
                else:requirement(p+'minimum_side',32,min(r['height'],r['width']),min(r['height'],r['width'])>=32)
            if key in ('water_map','optical_sar','sar_scene','flood_lab'):
                sar=tags.get('sensor') in ('Sentinel-1','Sentinel-1 GRD') or r['bands']==S1
                expected=S1 if sar else L1C if key=='water_map' else S2
                requirement(p+'band_order',expected,r['bands'],r['bands']==expected)
                sensors=['Sentinel-1 GRD'] if sar and key=='water_map' else ['Sentinel-1','Sentinel-1 GRD'] if sar else ['Sentinel-2 L1C'] if key=='water_map' else ['Sentinel-2']
                requirement(p+'sensor_product',sensors,tags.get('sensor'),tags.get('sensor') in sensors)
                requirement(p+'units','dB' if sar else 'reflectance_x10000',tags.get('units'),tags.get('units')==('dB' if sar else 'reflectance_x10000'))
                requirement(p+'scale_offset_applied','Identity; these specialists consume calibrated native values',[r['scales'],r['offsets']],all(v==1 for v in r['scales']) and all(v==0 for v in r['offsets']))
                dim=512 if key=='water_map' else 120 if key in ('optical_sar','sar_scene') else None
                if dim:requirement(p+'checkpoint_dimensions',[dim,dim],[r['height'],r['width']],r['height']==r['width']==dim)
                if key in ('optical_sar','sar_scene','flood_lab'):
                    requirement(p+'projected_metre_grid','Projected CRS in metres',r['linear_units'],r['projected'] and r['linear_units'] in ('metre','meter'))
                    requirement(p+'north_up','North-up unrotated grid',r['transform'],r['north_up'])
                if key in ('optical_sar','sar_scene'):requirement(p+'resolution',[10,10],r['resolution'],np.allclose(r['resolution'],[10,10],rtol=0,atol=1e-7))
                if key=='sar_scene':requirement(p+'SAR_only',['VV','VH'],r['bands'],r['bands']==S1)
                if key=='flood_lab':
                    for field in ('terrain_corrected','relative_orbit','orbit_state','scene_id'):
                        requirement(p+field,'Declared in verified prepared-event manifest',tags.get(field),bool(tags.get(field)))
            if key=='terrain':
                requirement(p+'native_vertical_calibration','Identity scale/offset for metre elevations',[r['scales'],r['offsets']],r['scales']==[1] and r['offsets']==[0])
                requirement(p+'elevation_bands',1,r['count'],r['count']==1)
                requirement(p+'vertical_units','metre, meter, metres, meters or m',tags.get('units') or tags.get('vertical_units'),(tags.get('units') or tags.get('vertical_units')) in ('m','metre','meter','metres','meters'))
                requirement(p+'metric_grid','Projected metre, north-up, unrotated',r['linear_units'],r['projected'] and r['linear_units'] in ('metre','meter') and r['north_up'])
                add(p+'vertical_datum','Declared vertical datum',tags.get('vertical_datum'),'MATCH' if tags.get('vertical_datum') else 'UNKNOWN',False)
        if len(files)==2:
            a,b=[f['raster'] for f in files]
            requirement('pair.dimensions','Equal width and height',[[a['height'],a['width']],[b['height'],b['width']]],a['height']==b['height'] and a['width']==b['width'])
            same=a['crs']==b['crs'] and a['width']==b['width'] and a['height']==b['height'] and np.allclose(a['transform'],b['transform'],rtol=0,atol=1e-10)
            requirement('pair.grid','Equal CRS, dimensions and affine; no reprojection',[a['crs'],b['crs'],a['transform'],b['transform']],same,key!='cdvqa')
            add('pair.physical_registration','Independent control points/content validation','Matching headers do not prove physical co-registration','UNKNOWN',False)
            add('pair.common_valid_coverage','At least one jointly valid native pixel',common,'MATCH' if common else 'MISMATCH' if common==0 else 'UNKNOWN',key in ('water_map','spectral_pair'))
            bounds=[a['bounds'],b['bounds']]
            comparable=a['crs'] and a['crs']==b['crs'] and all(v is not None for row in bounds for v in row)
            overlap=max(0,min(bounds[0][2],bounds[1][2])-max(bounds[0][0],bounds[1][0]))*max(0,min(bounds[0][3],bounds[1][3])-max(bounds[0][1],bounds[1][1])) if comparable else None
            add('pair.bounds_overlap','Positive overlap in the same declared CRS',overlap,'MATCH' if overlap else 'MISMATCH' if overlap==0 else 'UNKNOWN',False)
            dates=[r['tags'].get('acquisition_date') or r['tags'].get('acquired') for r in (a,b)]
            try:parsed=[datetime.strptime(d,'%Y-%m-%d') for d in dates]
            except (ValueError,TypeError):parsed=[]
            if key in ('temporal','spectral_pair','water_map','optical_sar','flood_lab'):
                add('pair.acquisition_dates','Two valid YYYY-MM-DD dates',dates,'MATCH' if parsed else 'MISSING')
                if key in ('temporal','spectral_pair','flood_lab'):requirement('pair.chronological_order','First date < second date',dates,bool(parsed and parsed[0]<parsed[1]))
                if key in ('water_map','optical_sar'):requirement('pair.interval_days','At most 14 days',abs((parsed[1]-parsed[0]).days) if parsed else None,bool(parsed and abs((parsed[1]-parsed[0]).days)<=14))
            if key in ('water_map','optical_sar'):
                requirement('pair.modalities','One SAR and one optical input',[r['tags'].get('sensor') for r in (a,b)],sum(r['bands']==S1 for r in (a,b))==1)
            if key=='spectral_pair':requirement('pair.product_convention','Same declared sensor/product',[r['tags'].get('sensor') for r in (a,b)],a['tags'].get('sensor')==b['tags'].get('sensor'))
            if key=='cdvqa':
                requirement('pair.aligned_ordered_declaration','Explicit true; same area, aligned, before then after',declarations.get('aligned_ordered'),declarations.get('aligned_ordered') is True)
                from paired_lab.cdvqa_bridge import supported
                requirement('question.template','One exact supported CDVQA template',declarations.get('question'),supported(declarations.get('question','')))
        if key=='flood_lab':add('prepared_event_adapter','Existing Flood Lab event/OSM manifest route','Arbitrary-TIFF execution adapter is not enabled','MISMATCH',True,'Flood Lab calculations are preserved, not rebuilt.','Prepare and validate the full event bundle in the existing Flood Lab workflow.')
        if key=='vqa':add('external_execution_adapter','Verifiable cancellation of the actual model operation','Shared single-image service has no cancellation API','MISSING',True,'The original Workspace remains available; external execution is withheld rather than leaving a shared operation running after Stop.','Use the existing optical Workspace; add a cancellable isolated Qwen adapter before enabling this external path.')
        references=[f['name'] for f in dataset['files'] if f.get('role')=='reference']
        for reference in [f for f in dataset['files'] if f.get('role')=='reference']:
            r=reference.get('raster');prefix='reference.'+reference['name']+'.'
            add(prefix+'format','Categorical raster or protocol-compatible label table','TIFF' if r else Path(reference['name']).suffix,'MATCH' if r or reference['name'].lower().endswith('.csv') else 'UNKNOWN',False)
            if r:
                aligned=bool(files and all(r[k]==files[0]['raster'][k] for k in ('crs','transform','width','height')) and r['crs'])
                add(prefix+'grid_alignment','Equal prediction/source dimensions, CRS and affine',dict(crs=r['crs'],transform=r['transform'],dimensions=[r['height'],r['width']]),'MATCH' if aligned else 'MISMATCH',False)
                add(prefix+'label_dtype','One integer categorical band',r['dtypes'],'MATCH' if r['count']==1 and all(np.dtype(t).kind in 'ui' for t in r['dtypes']) else 'MISMATCH',False)
                add(prefix+'ignore_nodata_convention','Explicit protocol ignore values plus native NoData',dict(nodata=r['nodata_repr'],protocol=(declarations.get('protocol') or {}).get('ignore_values')),'MATCH' if 'ignore_values' in (declarations.get('protocol') or {}) else 'MISSING',False)
            add(prefix+'class_semantics','Explicit native-reference mapping to declared model class semantics',(declarations.get('protocol') or {}).get('reference_class_mapping'),'MATCH' if (declarations.get('protocol') or {}).get('reference_class_mapping') else 'MISSING',False)
        add('evaluation.ground_truth','Independent compatible labels and predeclared class/ignore mapping',references,'UNKNOWN' if references else 'MISSING',False,
            'Labels are not required for prediction. No score is produced until their semantics/grid/protocol are verified.','Attach independent labels and freeze an evaluation protocol; predictions are never ground truth.')
        asset=(assets or {}).get(key,dict(status='not_checked',assets=[]))
        ready=asset['status']=='checks_passed_inference_unverified'
        add('model.assets','Pinned assets and dependencies present',asset['status'],'MATCH' if ready else 'MISSING' if asset['status']=='blocked' else 'UNKNOWN',True,
            'Presence is distinct from a real model execution. Weight hashes are recorded at execution.','Run scripts/preflight.py and provision the documented checkpoint without substituting a model.')
        blockers=[r for r in rows if r['prevents_execution']]
        data_blocks=[r for r in blockers if r['parameter'] not in ('model.assets','external_execution_adapter','prepared_event_adapter')]
        status='READY_FOR_ANALYSIS' if not blockers else ('MISSING_METADATA' if all(r['status'] in ('MISSING','UNKNOWN') for r in data_blocks) else 'INCOMPATIBLE_INPUT') if data_blocks else 'UNSUPPORTED_TASK' if any(r['parameter'] in ('external_execution_adapter','prepared_event_adapter') for r in blockers) else 'MISSING_MODEL_ASSETS'
        reports.append(dict(specialist=key,**spec,status=status,input_compatible=not data_blocks,eligible=not blockers,
            blocking_reasons=blockers,parameters=rows,model_availability=asset))
    return dict(dataset_id=dataset['id'],dataset_revision=dataset.get('revision'),
        selected_inputs=[f['id'] for f in files],specialists=reports,
        eligible_specialists=[r['specialist'] for r in reports if r['eligible']],
        ineligible_specialists=[r['specialist'] for r in reports if not r['eligible']],
        preparation='Diagnostic only. No resizing, reprojection, band invention, filling or unit conversion occurred.',
        unsupported_requests=['Flood depth, damage, safe routes, evacuation, forecasting','Accuracy without independent compatible reference labels'])


def report_csv(report):
    out=io.StringIO();fields=['specialist','parameter','expected','observed','status','severity','explanation','suggested_preparation','prevents_execution']
    writer=csv.DictWriter(out,fieldnames=fields);writer.writeheader()
    for specialist in report['specialists']:
        for row in specialist['parameters']:
            values={**row,'specialist':specialist['specialist']}
            # Prevent spreadsheet formula interpretation of untrusted metadata.
            for k,v in values.items():
                if isinstance(v,str) and v.startswith(('=','+','-','@','\t','\r')):values[k]="'"+v
            writer.writerow(values)
    return out.getvalue()
