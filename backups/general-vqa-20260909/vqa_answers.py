"""Conservative answer presentation, not a visual verifier or confidence model.

Keep raw_answer in each run. Rules can suppress known overclaims, but cannot
establish that a land-cover/object label is correct. No model-generated rationale
is presented as independent evidence.
"""
import re

VERSION = 'bounded-answer-v2'
UNCERTAIN = 'Cannot determine reliably from this image. Try a simpler visible-feature question or a clearer image.'
LIMITATION = 'Model interpretation; object identities and locations are not independently verified.'
_UNSUPPORTED = re.compile(
    r'\b(?:likely|possibly|perhaps|could|might|suggest\w*|impli\w*|indicat\w*|'
    r'appear\w* to be|seems?|due to|because|used for|designed for|purpose\w*|'
    r'traffic|congestion|accidents?|condition|well[- ]maintained|maintained|'
    r'health\w*|stress\w*|safety|safe|danger\w*|disease\w*|yield|biomass|'
    r'commercial|residential|business|recreation\w*|affluent|economic|'
    r'protected|remote|undisturbed|inhabitants|population|habitation|'
    r'species|types? of crops?|stages? of|season\w*|summer|winter|spring|autumn|'
    r'irrigat\w*|crop rotation|snow|ice|snow-covered|\d+(?:\.\d+)?\s*(?:%|hectares?|acres?))\b', re.I)
_NEGATED = re.compile(r'\b(?:no|not|without|absence|lack|cannot|can.t)\b', re.I)
_FEATURE = re.compile(r'\b(?:fields?|farmland|agricultur\w*|forest\w*|vegetation|greenery|'
                      r'green spaces?|water|lakes?|rivers?|ocean|sea|beach|buildings?|'
                      r'roads?|runways?|airport|urban|built-up|bare|land|structures?)\b', re.I)


def _generalize(text):
    # Only weaken use/population claims into appearance-level descriptions.
    # These substitutions do not add new objects, evidence, or spatial positions.
    replacements = [
        (r'\bdensely populated area(s?)\b', r'dense built-up area\1'),
        (r'\bdensely packed residential area(s?)\b', r'densely packed built-up area\1'),
        (r'\bdense residential\b', 'dense built-up area'),
        (r'\bresidential area(s?)\b', r'built-up area\1'),
        (r'\bresidential buildings\b', 'buildings'),
    ]
    for pattern, replacement in replacements:
        text = re.sub(pattern, replacement, text, flags=re.I)
    return text


def present_answer(question, raw, *, truncated=False):
    text = raw.strip()
    q = question.lower().strip()
    q = re.sub(r'^please\s+', '', q)
    q = re.sub(r'^(?:can|could) you\s+', '', q)
    category = 'rural_urban' if 'rural or urban' in q else 'binary' if re.match(r'^(?:is|are|does)\b', q) else 'description'
    result = dict(policy=VERSION, category=category, limitation=LIMITATION,
                  raw_truncated=bool(truncated), changed=False, withheld=False, reasons=[])

    def withhold(reason):
        result.update(answer=UNCERTAIN, changed=True, withheld=True, reasons=[reason])
        return result

    if not text:
        return withhold('empty_output')
    final = re.search(r'\btherefore,?\s+the answer is\s+(.+)$', text, flags=re.I | re.S)
    if category != 'description':
        allowed = ('rural', 'urban') if category == 'rural_urban' else ('yes', 'no')
        pattern = '(?:' + '|'.join(allowed) + ')'
        candidate = final.group(1).strip() if final else text
        exact = re.fullmatch('(' + pattern + r')[.!?\s]*', candidate, re.I)
        if not exact:
            return withhold('missing_unambiguous_final_label')
        answer = exact.group(1).lower()
        initial = re.match(r'^(yes|no)\b', text, re.I) if category == 'binary' else None
        if initial and initial.group(1).lower() != answer:
            return withhold('conflicting_initial_and_final_labels')
        result.update(answer=answer.capitalize(), changed=text != answer.capitalize())
        if result['changed']:
            result['reasons'].append('explanation_omitted_final_label_only')
        return result

    # Keep at most two complete observation sentences. Never repair a cut-off
    # sentence by completing it, and never turn a negative into a positive claim.
    body = text[:final.start()] if final else text
    observations = []
    for match in re.finditer(r'[^.!?]+[.!?]', body):
        sentence = match.group().strip()
        simplified = _generalize(sentence)
        if _UNSUPPORTED.search(simplified):
            # Preserve an already complete main clause when only a following
            # relative clause speculates. Keep source words; add no observations.
            main = re.split(r',\s+(?:which\b|indicating\b|suggesting\b|likely\b)', simplified, maxsplit=1, flags=re.I)[0]
            if main != simplified and re.search(r'\b(?:features? .+? (?:is|are)|fields? (?:is|are)|image shows)\b', main, re.I):
                simplified = main.rstrip(',; ') + '.'
                result['reasons'].append('speculative_relative_clause_withheld')
        if (_FEATURE.search(simplified) and not _UNSUPPORTED.search(simplified)
                and not _NEGATED.search(simplified)
                and not re.search(r'\b(?:image does|image provides|therefore|answer is)\b', simplified, re.I)):
            observations.append(simplified)
            if simplified != sentence:
                result['reasons'].append('use_or_population_claim_generalized')
        elif sentence:
            result['reasons'].append('unsupported_or_nonobservational_sentence_withheld')
        if len(observations) == 2:
            break
    if not observations and final:
        candidate = _generalize(final.group(1).strip())
        # A complete, short scene label is useful when the narrative is speculative.
        if re.fullmatch(r'(?:The aerial scene is )?(?:farmland|forest|beach|urban|rural|'
                        r'dense built-up area|airport|river|lake|wetland)[.!?\s]*', candidate, re.I):
            observations = [re.sub(r'^The aerial scene is ', '', candidate, flags=re.I).rstrip('.!?') + '.']
            result['reasons'].append('short_final_scene_label_only')
    if not observations:
        return withhold('no_complete_bounded_observation')
    answer = ' '.join(observations)
    result.update(answer=answer + '\n\n' + LIMITATION, changed=True)
    result['reasons'] = list(dict.fromkeys(result['reasons']))
    return result
