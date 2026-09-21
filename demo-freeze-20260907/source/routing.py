"""Conservative single-image intent grammar. No model calls or confidence scores.

Unsupported rules run first. Only whole-question allowlists dispatch a tool;
unrecognized and compound requests fail closed. Version saved with each run.
"""
import math
import re

VERSION = 'rules-v1'


def route(question, *, ndvi_supported=False, threshold=0.5):
    def decision(tool, rule, reason):
        return dict(tool=tool, rule=rule, reason=reason, version=VERSION)

    def refuse(rule, reason):
        return decision('refuse', rule, reason)

    q = ' '.join(question.lower().replace('’', "'").strip().split())
    q = re.sub(r'[?.!]+$', '', q)
    q = re.sub(r'^please\s+', '', q)
    q = re.sub(r'^(?:can|could) you\s+', '', q)
    if not q or len(question) > 500:
        return refuse('question_length', 'Enter a question between 1 and 500 characters.')
    blockers = [
        (r'\b(sar|radar|sentinel[- ]?1|backscatter|fusion|fuse)\b', 'sar_unavailable', 'SAR analysis and optical/SAR fusion are planned, not implemented.'),
        (r'\b(chang\w*|temporal|last\s+(year|month|week|season)|previous|earlier|before|after|since|trend\w*|over time|20\d{2}|19\d{2})\b', 'temporal_unavailable', 'Temporal/change analysis requires dated image pairs and is not implemented.'),
        (r'\b(compare|compared|comparison|pair\w*|both|another|second|two images|two photos|other image|other photo|versus|vs)\b', 'comparison_unavailable', 'Paired-image and comparison requests are not supported by this router. Ask a descriptive question about one image.'),
        (r'\b(show|locate|find|ground\w*|detect\w*|segment\w*|outline|highlight|draw|box\w*|polygon\w*|coordinates?|latitude|longitude|where)\b', 'grounding_unavailable', 'Text-guided grounding is planned. No validated object boxes, masks or locations are available.'),
        (r'\b(count\w*|how many|number of)\b', 'counting_unavailable', 'Object counting has no validated specialist and is not supported.'),
        (r'\b(health\w*|stress\w*|biomass|yield|species|density|disease\w*|carbon|ndwi|evi|savi|temperature)\b', 'unsupported_measurement', 'This measurement or diagnosis is not implemented. NDVI supports only threshold-selected pixel coverage.'),
        (r'\b(green|greener|greenness|greenest)\b', 'ambiguous_green', 'Green wording is ambiguous. Ask for a vegetation description, or explicitly request NDVI threshold coverage.'),
        (r'\b(area|hectares?|acres?|kilomet\w*|meters?|metres?|distance|length|width|height|volume|measure\w*)\b', 'measurement_unavailable', 'Free-form area and object measurements are not supported. NDVI coverage reports threshold-selected pixels and projected grid area only when available.'),
    ]
    for pattern, rule, reason in blockers:
        if re.search(pattern, q):
            return refuse(rule, reason)

    # An explicit numerical threshold is accepted only if it matches the control.
    suffix = r'(?: at (?:the )?selected threshold| at (?:a )?threshold(?: of)? (-?\d+(?:\.\d+)?)|\s*(?:>=|≥)\s*(-?\d+(?:\.\d+)?))?'
    ndvi = re.fullmatch(r'(?:calculate |compute |what is (?:the )?|give (?:me )?(?:the )?)?ndvi(?: (?:coverage|threshold coverage))?' + suffix, q)
    coverage = re.fullmatch(r'(?:calculate (?:the )?(?:vegetation coverage|percentage of vegetation)|what (?:percentage|percent|fraction) of (?:this |the )?(?:image|crop|valid pixels) (?:is|are) (?:vegetation|covered (?:by|with) vegetation)|what is (?:the )?vegetation coverage)(?: using ndvi)?' + suffix, q)
    if ndvi or coverage:
        match = ndvi or coverage
        if not math.isfinite(threshold) or not -1 <= threshold <= 1:
            return refuse('invalid_threshold', 'NDVI threshold must be finite and between -1 and 1.')
        explicit = next((float(v) for v in match.groups() if v is not None), None)
        if explicit is not None and explicit != threshold:
            return refuse('threshold_mismatch', 'The question threshold differs from the NDVI control. Set the control to match the question before analyzing.')
        if not ndvi_supported:
            return refuse('calibrated_bands_required', 'NDVI needs labelled, calibrated Red/NIR surface-reflectance bands. RGB alone cannot answer this request.')
        return decision('ndvi', 'ndvi_threshold_coverage', 'Explicit NDVI or vegetation pixel-coverage request with calibrated Red/NIR available. Coverage means pixels meeting the selected NDVI threshold, not surveyed vegetation cover.')

    subjects = r'(?:vegetation|water|water bodies|a water body|a river|rivers|a building|buildings|roads|a road|forest|forests|farmland|land use|land cover|major visible features|main visible features|visible features|features|scene|image)'
    context = r'(?: (?:visible )?in (?:this|the) (?:image|scene|photo))?'
    descriptive = [
        r'describe (?:the )?' + subjects + context + r'(?: briefly)?',
        r'describe this (?:image|scene)(?: briefly)?',
        r'what (?:is in|do you see in) (?:this|the) (?:image|scene)',
        r'what (?:is|can be) (?:visible|seen) in (?:this|the) (?:image|scene)',
        r'what (?:does|do) (?:this|the) (?:image|scene) show',
        r'(?:is|are) there (?:any )?' + subjects + context,
        r'(?:is|are) ' + subjects + r' (?:visible|present)' + context,
        r'does (?:this|the) (?:image|scene) (?:contain|show) ' + subjects,
        r'is (?:this|the) (?:image|scene|area) rural or urban',
    ]
    if any(re.fullmatch(pattern, q) for pattern in descriptive):
        return decision('vqa', 'single_image_description', 'Supported descriptive or presence question about one optical image; no quantitative or spatial output requested.')
    return refuse('unsupported_or_ambiguous', 'This intent is unsupported or ambiguous. Ask a single-image description/presence question, or explicitly request NDVI threshold coverage. No tool was run.')
