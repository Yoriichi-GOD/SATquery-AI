"""Versioned inference instructions; no answer rewriting or invented evidence."""
VERSION = 'visible-evidence-v1'


def effective_question(question, mode='baseline'):
    # Preserve the exact prompts used for the saved LoRA development comparison.
    if mode == 'pilot_binary':
        return question + ' Answer with only yes or no.'
    if mode == 'pilot_rural':
        return question + ' Answer with only rural or urban.'
    return (
        'Answer the question using only features visibly distinguishable in this satellite image. '
        'Do not infer road condition, traffic, accidents, safety, vegetation health, building use, '
        'or activity from appearance. Do not invent counts, percentages, names or locations. '
        'If a requested feature cannot be distinguished at this resolution, say "Cannot determine from this image." '
        'For a yes/no question, answer Yes, No, or Cannot determine from this image. '
        'For rural or urban, answer Rural, Urban, or Cannot determine from this image. '
        'For a description, give at most two short sentences about visible land cover and structures. '
        'Answer only the question.\nQuestion: ' + question
    )
