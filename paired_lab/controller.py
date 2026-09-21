"""One bounded, input-aware routing entry point. No model fallback on failure."""
import importlib.util, math, re
from pathlib import Path
from inputs import route as paired_route
VERSION = 'unified-rules-v6'
spec = importlib.util.spec_from_file_location('preserved_single_router', Path(__file__).resolve().parent.parent / 'routing.py')
single = importlib.util.module_from_spec(spec); spec.loader.exec_module(single)
SPECIALISTS = {
    'spectral_pair': ('NDVI + NDWI observed-date comparison','CPU','experimental'),
    'vqa': ('Remote-sensing Qwen2-VL-2B', 'CUDA GPU', 'supported'),
    'ndvi': ('Deterministic NDVI calculation', 'CPU', 'supported'),
    'temporal': ('MCI road/building change + caption', 'CPU', 'supported'),
    'water_map': ('WaterUNet · SAR / optical / joint', 'CPU', 'supported'),
    'optical_sar': ('BIFOLD ResNet50 · SAR / optical / joint', 'CPU', 'supported'),
    'grounding': ('Grounding DINO tiny → SAM base', 'CUDA GPU · sequential models', 'experimental'),
}
CATEGORIES = {
    'stadium': r'\bstadiums?\b', 'car': r'\b(cars?|vehicles?)\b',
    'aircraft': r'\b(aircraft|airplanes?|aeroplanes?|planes?)\b',
    'building': r'\bbuildings?\b', 'ship': r'\bships?\b',
    'sports field': r'\b(sports? fields?|baseball fields?|football fields?)\b',
}
def selection(task, reason, **extra):
    name, device, maturity = SPECIALISTS[task]
    return dict(task=task, version=VERSION, specialist=name, device=device, maturity=maturity, reason=reason, **extra)

def grounding_request(query):
    """Only explicit spatial requests select the experimental detector."""
    q = query.lower()
    if not re.search(r'\b(outline|segment|highlight|locate|localize|localise|mark|draw|boxes|bounding|where)\b', q): return None
    if re.search(r'\b(ndvi|spectral|hectares?|km2|area|metres?|meters?|count|how many|chang\w*|before|after|sar|radar|health)\b', q):
        raise ValueError('This combines spatial grounding with an unsupported measurement or another task. Ask one supported question.')
    categories = [name for name, pattern in CATEGORIES.items() if re.search(pattern, q)]
    if len(categories) != 1:
        raise ValueError('For experimental grounding, ask for one category: stadium, car, aircraft, building, ship or sports field.')
    if re.search(r'\b(and|or|except|excluding|near|nearest|left|right|behind|beside|largest|smallest|red|blue)\b', q):
        raise ValueError('Grounding supports one object category without relationships, colour filters or multiple tasks. Please simplify the request.')
    mode = 'boxes' if re.search(r'\b(boxes|bounding)\b', q) and not re.search(r'\b(outline|segment|mask)\b', q) else 'both'
    return categories[0], mode

def plan(query, records, threshold=.5):
    if not isinstance(query, str) or not query.strip() or len(query) > 500: raise ValueError('Ask one question of up to 500 characters.')
    if isinstance(threshold, bool) or not isinstance(threshold, (int, float)) or not math.isfinite(threshold) or not -1 <= threshold <= 1:
        raise ValueError('NDVI threshold must be a finite number from -1 to 1.')
    q = ' '.join(query.lower().split())
    if re.search(r'\b(forecast\w*|predict\w*|tomorrow|evacuat\w*|future|next (?:day|week|month|year)|will .*(?:spread|flood|change|increase))\b', q):
        raise ValueError('Forecasting and evacuation advice are not implemented. Ask about water visible now, or supported road/building changes between observed dates. Future rainfall scenarios cannot be analysed by the current specialists.')
    if re.search(r'\b(depth|volume|temperature|soil moisture|population|rainfall|evaporation)\b', q):
        raise ValueError('This measurement is outside the available specialists. Ask about visible features, supported index changes, water mapping or road/building change.')
    if len(records)==2 and all(r.get('modality')=='optical' and r.get('reflectance_units')=='surface_reflectance' for r in records):
        from spectral_pair import requested
        tasks,broad=requested(query)
        if tasks:
            if re.search(r'\b(threshold|above|below|greater|less)\b|[<>]',q):raise ValueError('Set index thresholds in Spectral comparison thresholds rather than embedding a different threshold in the question.')
            if re.search(r'\b(how many|count|depth|volume|health|yield|species|length|cars?|vehicles?)\b',q):raise ValueError('This spectral comparison reports index threshold changes, not object counts, depth, health or species.')
            return selection('spectral_pair','Two optical surface-reflectance dates; compare only requested spectral parameters.',parameters=tasks,include_built_up=broad or bool(re.search(r'\b(urban|built-up|buildings?)\b',q)),threshold=threshold,steps=['validate dates and shared grid','exclude invalid pixels at both dates','compare requested indices','export per-parameter evidence'])
    if len(records) == 2 and re.search(r'\b(ndvi|spectral index|vegetation index)\b', q):
        raise ValueError('Paired spectral comparison requires two Sentinel-2 surface-reflectance TIFFs with labelled Red/Green/NIR, genuine SCL quality bands and dates. These inputs do not establish that contract. Use Single image for a compatible individual NDVI calculation.')
    if len(records) == 1:
        r = records[0]
        if r.get('modality') != 'optical': raise ValueError('Single-image analysis needs an optical image. Supply a supported optical–SAR pair for SAR.')
        grounding = grounding_request(query)
        if grounding:
            w, h = r.get('width', 0), r.get('height', 0)
            if min(w, h) < 64 or w*h > 6_000_000: raise ValueError('Grounding requires at least 64 pixels per side and at most 6 megapixels. Prepare a suitable RGB crop.')
            category, mode = grounding
            p = selection('grounding', 'Explicit spatial request for a supported object category on one optical image.',
                          category=category, mode=mode, score_threshold=.3,
                          steps=['validate optical image', 'detect objects', 'segment boxes' if mode == 'both' else 'render boxes', 'save evidence'])
            if mode == 'boxes': p['specialist'] = 'Grounding DINO tiny · boxes only'
            return p
        d = single.route(query, ndvi_supported=(r.get('geo') or {}).get('ndvi_supported', False), threshold=threshold)
        if d['tool'] == 'refuse':
            reason = d['reason']
            if d['rule'] == 'temporal_unavailable': reason = 'Temporal analysis needs two dated optical images; only one was supplied.'
            elif d['rule'] == 'sar_unavailable': reason = 'Cross-sensor analysis needs a supported optical and SAR pair.'
            raise ValueError(reason)
        mode = 'pilot_rural' if d['rule'] == 'rural_urban_classification' else 'baseline'
        p = selection(d['tool'], d['reason'], decision=d, mode=mode, threshold=threshold, steps=['validate image', d['tool'], 'save evidence'])
        if mode == 'pilot_rural': p['specialist'] += ' + rural/urban LoRA'
        return p
    if len(records) != 2: raise ValueError('Supply one optical image, two optical dates, or one optical and one SAR image.')
    modes = sorted(r['modality'] for r in records)
    if modes == ['optical', 'optical']:
        if re.search(r'\b(sar|radar|fusion|modalities)\b', q): raise ValueError('Both supplied images are optical; SAR analysis requires a SAR input.')
        if not (re.search(r'\b(chang\w*|before|after|dates?|increas\w*|decreas\w*|built|removed|construction|demolition|gain|loss)\b', q) or (re.search(r'\bcompare\b', q) and re.search(r'\b(roads?|buildings?)\b', q))):
            raise ValueError('Ask about road/building change between the two optical dates, or supply one image.')
        if re.search(r'\b(flood\w*|water|forest|trees?|crop\w*|vegetation|cars?|vehicles?|colou?r|stadiums?|ships?|aircraft|ndvi)\b', q): raise ValueError('The temporal specialist supports road/building change only.')
        if re.search(r'\b(how many|count|hectares?|square|km2|meters?|metres?|kilomet\w*|length|miles?)\b', q): raise ValueError('Temporal masks report predicted change pixels, not object counts or physical area.')
        return selection('temporal', 'Two optical dates and a supported change question.', threshold=threshold,
                         steps=['validate pair', 'registration diagnostic', 'road/building masks and caption', 'save evidence'])
    if modes == ['optical', 'sar'] and any(r.get('count') == 13 for r in records if r['modality'] == 'optical'):
        if re.search(r'\b(change\w*|before|after|increase\w*|decrease\w*)\b', q): raise ValueError('This optical–SAR pair supports single-date water mapping, not change over time.')
        if re.search(r'\b(buildings?|roads?|highways?|built-up|urban|forest|vegetation|trees?|crops?|cars?|vehicles?|count|how many|hectares?|square|km2|depth|volume|speed)\b', q): raise ValueError('This specialist maps water pixels only; it cannot map buildings, count objects or measure physical area.')
        if not re.search(r'\b(water|flood\w*|inundat\w*)\b', q): raise ValueError('Ask to map water in this Sentinel-1 / Sentinel-2 L1C pair.')
        return selection('water_map', 'Optical 13-band / SAR pair and a water-mapping question.', threshold=threshold,
                         steps=['validate sensor contract', 'three modality predictions', 'save evidence'])
    if modes == ['optical', 'sar'] and re.search(r'\b(map|mask|segment|outline|locate|locations?|positions?|highlight|delineat\w*|depth|volume|percentage|percent|coverage)\b', q):
        raise ValueError('This optical–SAR scene classifier returns land-cover labels, not pixel maps or coverage measurements. Ask "Identify land-cover classes". Water masks require the supported 13-band Sentinel-2 L1C / Sentinel-1 GRD pair; do not resize or relabel incompatible data to bypass this requirement.')
    task = paired_route(query, records)
    return selection(task, 'Optical–SAR patch and a scene-level land-cover question.', threshold=threshold,
                     steps=['validate sensor contract', 'three modality predictions', 'save evidence'])
