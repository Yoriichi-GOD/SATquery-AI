"""Conservative single-image intent grammar. No model calls or confidence scores.

Unsupported rules run first. Only whole-question allowlists dispatch a tool;
unrecognized and compound requests fail closed. Version saved with each run.
"""
import math
import re

VERSION = 'rules-v8'


def visual_context_question(question):
    """Whole-question descriptive location/context; never boxes or physical units."""
    q = ' '.join(question.lower().strip().split()).rstrip('?.!')
    q = re.sub(r'^(?:please |(?:can|could) you )', '', q)
    if re.search(r'\b(and|or|then|count|measure|coordinates?|latitude|longitude|meters?|metres?|hectares?|depth|predict\w*|forecast\w*|chang\w*|before|after)\b', q):
        return False
    noun = r"[a-z][a-z -]{0,80}"
    return bool(re.fullmatch(r'where (?:is|are) (?:the |a |an )?' + noun + r' (?:situated|located|positioned) in (?:this|the) (?:image|scene|picture)', q)
                or re.fullmatch(r'what (?:kind|type) of area surrounds (?:the |a |an )?' + noun, q))

def route(question, *, ndvi_supported=False, threshold=0.5):
    def decision(tool, rule, reason):
        return dict(tool=tool, rule=rule, reason=reason, version=VERSION)

    def refuse(rule, reason):
        return decision('refuse', rule, reason)

    q = ' '.join(question.lower().replace('’', "'").strip().split())
    q = re.sub(r'[?.!]+$', '', q).strip()
    q = re.sub(r'^please\s+', '', q)
    q = re.sub(r'^(?:can|could) you\s+', '', q)
    if not q or len(question) > 500:
        return refuse('question_length', 'Enter a question between 1 and 500 characters.')
    if visual_context_question(question):
        return decision('vqa', 'visual_context', 'Descriptive image-relative context; model interpretation, not coordinates, boxes or measurement.')
    rural_q=re.sub(r'\brural\s*/\s*urban\b', 'rural or urban', q)
    rural_patterns=[
        r'is (?:this|the)(?: (?:image|scene|photo|picture|area))? (?:a |an )?rural or urban(?: (?:area|scene|image))?',
        r'(?:is|would you classify) (?:this|the) (?:image|scene|area) (?:as )?rural or urban',
        r'(?:classify|describe) (?:this|the) (?:image|scene|area) as rural or urban',
        r'rural or urban',
    ]
    if any(re.fullmatch(pattern,rural_q) for pattern in rural_patterns):
        result=decision('vqa','rural_urban_classification','Single-image rural/urban classification; not an area measurement.')
        result['canonical_question']='Is this image rural or urban?'
        return result
    # Presence depends on question structure, not a closed object vocabulary.
    noun = r"[a-z][a-z'-]*(?: [a-z][a-z'-]*){0,7}"
    image_context = r'(?: (?:visible |present )?in (?:this|the) (?:image|scene|photo|picture))?'
    presence_patterns = [
        r'(?:is|are) there (?P<subject>' + noun + r')' + image_context,
        r'(?:is|are) (?P<subject>' + noun + r') (?:visible|present)' + image_context,
        r'does (?:this|the) (?:image|scene|photo|picture) (?:contain|show) (?P<subject>' + noun + r')',
        r'(?:do you |can you )?see (?P<subject>' + noun + r')' + image_context,
    ]
    presence = False
    for pattern in presence_patterns:
        match = re.fullmatch(pattern, q)
        if match:
            # Exclude appended tasks, comparisons and nonvisual propositions.
            subject = match['subject']
            if not re.search(r'\b(and|or|then|than|more|less|fewer|enough|whether|that|which|because|without|not|no|ndvi|percentage|percent|calculate|ignore|tell|explain|describe|why|how|when|will|would|could|should|was|were|yesterday|tomorrow)\b', subject):
                presence = True
                break
    blockers = [
        (r'\b(sar|radar|sentinel[- ]?1|backscatter|fusion|fuse)\b', 'sar_unavailable', 'SAR analysis and optical/SAR fusion are planned, not implemented.'),
        (r'\b(chang\w*|temporal|last\s+(year|month|week|season)|previous|earlier|before|after|since|trend\w*|over time|20\d{2}|19\d{2})\b', 'temporal_unavailable', 'Temporal/change analysis requires dated image pairs and is not implemented.'),
        (r'\b(compare|compared|comparison|pair\w*|both|another|second|two images|two photos|other image|other photo|versus|vs)\b', 'comparison_unavailable', 'Paired-image and comparison requests are not supported by this router. Ask a descriptive question about one image.'),
        (r'\b(show|locate|find|ground\w*|detect\w*|segment\w*|outline|highlight|draw|box\w*|polygon\w*|coordinates?|latitude|longitude|where)\b', 'grounding_unavailable', 'Text-guided grounding is planned. No validated object boxes, masks or locations are available.'),
        (r'\b(count\w*|how many|number of)\b', 'counting_unavailable', 'Counting currently supports identifiable baseball/softball diamonds only. Other object counts are unavailable.'),
        (r'\b((?:un)?health\w*|stress\w*|biomass|yield|species|density|disease\w*|carbon|ndwi|evi|savi|temperature)\b', 'unsupported_measurement', 'This measurement or diagnosis is not implemented. NDVI supports only threshold-selected pixel coverage.'),
        (r'\b(green|greener|greenness|greenest)\b', 'ambiguous_green', 'Green wording is ambiguous. Ask for a vegetation description, or explicitly request NDVI threshold coverage.'),
        (r'\b(area|hectares?|acres?|kilomet\w*|meters?|metres?|distance|length|width|height|volume|measure\w*)\b', 'measurement_unavailable', 'Free-form area and object measurements are not supported. NDVI coverage reports threshold-selected pixels and projected grid area only when available.'),
    ]
    # A whole-question allowlist; compound and other counting requests still refuse.
    baseball_count = bool(re.fullmatch(
        r'(?:how many (?:baseball|softball) (?:fields|diamonds)(?: (?:are(?: (?:there|visible|present))?|can you see|do you see))?(?: in (?:this|the) (?:image|scene|photo))?|(?:count (?:the |these )?|what is (?:the )?number of )(?:baseball|softball) (?:fields|diamonds)(?: in (?:this|the) (?:image|scene|photo))?)', q))
    for pattern, rule, reason in blockers:
        if rule in ('counting_unavailable', 'ambiguous_green', 'comparison_unavailable'):
            continue
        if presence and rule == 'ambiguous_green':
            continue  # A green object is an appearance question, not NDVI.
        if presence and rule == 'measurement_unavailable' and not re.search(pattern, re.sub(r'\barea\b', '', q)):
            continue  # Presence of a grass/water area is not an area measurement.
        if presence and rule == 'grounding_unavailable':
            # "Does this image show a mountain?" asks presence, not boxes.
            remainder = re.sub(r'^does (?:this|the) (?:image|scene|photo|picture) show ', '', q)
            if not re.search(pattern, remainder):
                continue
        if rule == 'counting_unavailable' and baseball_count:
            continue
        if re.search(pattern, q):
            return refuse(rule, reason)

    if baseball_count:
        return decision('vqa', 'baseball_count', 'Baseball/softball field count estimated by VQA; an original and mirrored image must agree. No object boxes or verified detection are produced.')

    if presence:
        return decision('vqa', 'single_image_presence', 'Visual presence question; model interpretation, not independently verified detection or a measurement.')

    # An explicit numerical threshold is accepted only if it matches the control.
    suffix = r'(?: at (?:the )?selected threshold| at (?:a )?threshold(?: of)? (-?\d+(?:\.\d+)?)|\s*(?:>=|≥)\s*(-?\d+(?:\.\d+)?))?'
    ndvi = re.fullmatch(r'(?:calculate |compute |what is (?:the )?|give (?:me )?(?:the )?)?ndvi(?: (?:coverage|threshold coverage))?(?: (?:for|on|in) (?:this|the) (?:image|raster|crop))?' + suffix, q)
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
    if re.search(r'\b(ndvi|percentage|percent|fraction|coverage)\b|%', q):
        return refuse('unsupported_measurement', 'For measured coverage, request NDVI with calibrated bands and a selected threshold.')
    if re.search(r'\b(ignore|override)\b.*\b(rules|instructions)\b', q):
        return refuse('instruction_override', 'Ask a question about the uploaded image.')
    if re.search(r'\b(two images|two photos|both images|another image|other image|last image|previous image)\b', q):
        return refuse('comparison_unavailable', 'Upload one image and ask about what is visible within it.')
    if re.search(r'\b(count\w*|how many|number of)\b', q):
        return decision('vqa', 'visual_count', 'General visual count from the original model; an estimate, not validated object detection.')
    return decision('vqa', 'general_visual_question', 'Open visual question answered by the original model; interpretation may be incorrect.')
