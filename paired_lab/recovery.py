"""Recovery guidance; never guesses or repairs scientific metadata."""
def detail(message):
    message=str(message)
    lower=message.lower()
    specific = [
        ('Choose what to compare', 'Select one of the compatible suggested questions below, or specify the feature you want to compare.'),
        ('Forecasting and evacuation', 'Ask about an observed state, for example "Map water", using a supported input pair. Forecasting is outside SatQuery scope.'),
        ('Paired NDVI comparison', 'For joint index comparison supply two calibrated Sentinel-2 dates with the required bands and quality mask, or run NDVI separately on compatible single images.'),
        ('This optical–SAR scene classifier', 'Ask "Identify land-cover classes" for this pair, or supply inputs that meet the water-mapping contract for a pixel mask.'),
    ]
    for prefix, action in specific:
        if message.startswith(prefix):
            return {'code':'unsupported_task','message':message,'next_steps':[action],'analysis_started':False}
    actions=[]
    if any(x in lower for x in ['crs','geographic grid','georeferenced','dimensions','misaligned','registration','transform','shared optical']):
        actions.append('Check that both images cover the same location and share the required CRS, pixel grid and alignment. Reproject or align them outside SatQuery; matching headers alone do not prove alignment.')
    if any(x in lower for x in ['acquisition','date','14 days']):
        actions.append('Use the actual acquisition dates from the source metadata. Enter them for both uploads; for temporal analysis select the earlier image first. Do not invent dates.')
    if any(x in lower for x in ['bands','units','sensor','processing level','checkpoint','training']):
        actions.append('Check Input requirements against the original product metadata. Supply the required sensor, processing level, ordered bands and units; do not rename incompatible bands or change units tags without valid preprocessing.')
    if 'ndvi' in lower and any(x in lower for x in ['red','nir','rgb','calibrat']):
        actions.append('For an RGB-only image, ask for a visual description instead. NDVI requires real calibrated Red and NIR measurements.')
    if any(x in lower for x in ['tiff','file format','supported file format']):
        actions.append('Use a readable TIFF for paired scientific analysis. PNG/JPEG can be used in Single image for visual questions; changing a filename extension is not conversion.')
    if not actions:actions.append('Revise the question to one supported task or check the input requirements. No specialist was started for this refused request.')
    return {'code':'input_or_request_not_supported','message':message,'next_steps':actions,'analysis_started':False}
