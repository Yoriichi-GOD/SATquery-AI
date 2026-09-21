"""Single entry point for supported single-image and paired workflows."""
import importlib.util,re,math
from pathlib import Path
from inputs import route as paired_route
VERSION='unified-lab-rules-v2'
spec=importlib.util.spec_from_file_location('preserved_single_router',Path(__file__).resolve().parent.parent/'routing.py')
single=importlib.util.module_from_spec(spec);spec.loader.exec_module(single)
def plan(query,records,threshold=.5):
    if not isinstance(query,str) or not query.strip() or len(query)>500:raise ValueError('Ask one question of up to 500 characters.')
    if not isinstance(threshold,(int,float)) or not math.isfinite(threshold) or not -1<=threshold<=1:raise ValueError('NDVI threshold must be a finite number from -1 to 1.')
    if len(records)==1:
        r=records[0]
        if r.get('modality')=='sar':raise ValueError('Single-image optical VQA cannot interpret SAR. Supply a supported optical–SAR pair.')
        d=single.route(query,ndvi_supported=(r.get('geo') or {}).get('ndvi_supported',False),threshold=threshold)
        if d['tool']=='refuse':
            reason=d['reason']
            if d['rule']=='temporal_unavailable':reason='Temporal analysis needs two dated optical images; only one image was supplied.'
            elif d['rule']=='sar_unavailable':reason='Cross-sensor analysis needs a supported optical image and SAR image together.'
            raise ValueError(reason)
        return {'task':d['tool'],'version':VERSION,'steps':['validate image','preserved '+d['tool'],'save evidence'],'decision':d,'mode':'pilot_rural' if d['rule']=='rural_urban_classification' else 'baseline','threshold':threshold}
    if len(records)!=2:raise ValueError('Supply one optical image, two optical dates, or one optical and one SAR image.')
    q=query.lower();modes=sorted(r['modality'] for r in records)
    if modes==['optical','sar'] and any(r['count']==13 for r in records if r['modality']=='optical'):
        if re.search(r'\b(change\w*|before|after|increase\w*|decrease\w*)\b',q):raise ValueError('This optical–SAR pair supports single-date water mapping, not change over time.')
        if re.search(r'\b(buildings?|built-up|urban|forest|cars?|count|how many|hectares?)\b',q):raise ValueError('This spatial model maps water only; it cannot map buildings or count objects.')
        if not re.search(r'\b(water|flood\w*|inundat\w*)\b',q):raise ValueError('Ask to map water in this Sentinel-1 / Sentinel-2 L1C pair.')
        task='water_map'
    else:
        # The new temporal model supports road and building changes.
        normalized=re.sub(r'\broads?\b','building',query,flags=re.I)
        task=paired_route(normalized,records)
    return {'task':task,'version':VERSION,'steps':['validate pair','registration diagnostics' if task=='temporal' else 'check sensor contract',{'temporal':'MCI caption + road/building masks','water_map':'WaterUNet optical / SAR / joint','optical_sar':'BigEarthNet modality comparison'}[task],'save evidence'],'threshold':threshold}
