"""Normalize whole-scene caption requests only; preserve specific questions."""
import re
VERSION = 'scene-description-v1'
PROMPT = 'Describe this image in detail.'

def is_scene_description(question):
    q = ' '.join(question.lower().strip().split())
    q = re.sub(r'[.!?]+$', '', q).strip()
    q = re.sub(r'^please\s+', '', q)
    q = re.sub(r'^(?:can|could) you\s+', '', q)
    noun = r'(?:image|scene|picture|photo)'
    patterns = [r'describe (?:this|the) '+noun+r'(?: in detail)?',
                r'describe (?:the )?(?:major |main )?visible features(?: in detail)?',
                r'what (?:is in|do you see in|is visible in|can be seen in) (?:this|the) '+noun,
                r'what does (?:this|the) '+noun+r' show']
    return any(re.fullmatch(p,q) for p in patterns)
