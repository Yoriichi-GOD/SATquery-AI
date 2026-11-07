"""Typed measurement-support gate, not a natural-language truth or causality judge."""
import math
from pathlib import Path
from research.terrain_exposure.io import sha256

def check(claim,facts,artifacts):
    fact=facts.get(claim.get('fact_id'))
    if fact is None:return 'UNKNOWN_FACT'
    if fact.get('value') is None:return 'UNAVAILABLE_EVIDENCE'
    if claim.get('kind')!=fact['kind']:return 'UNSUPPORTED_INTERPRETATION'
    if claim.get('unit')!=fact['unit']:return 'UNIT_MISMATCH'
    if claim.get('artifact')!=fact['artifact']:return 'WRONG_SOURCE'
    path=artifacts.get(fact['artifact'])
    if path is None or not Path(path).is_file():return 'MISSING_SOURCE'
    if claim.get('sha256')!=fact['sha256'] or sha256(path)!=fact['sha256']:return 'SOURCE_HASH_MISMATCH'
    value=claim.get('value')
    if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value):return 'INVALID_NUMBER'
    if not math.isclose(value,fact['value'],rel_tol=1e-10,abs_tol=1e-10):return 'VALUE_MISMATCH'
    return 'SUPPORTED_TYPED_MEASUREMENT'
