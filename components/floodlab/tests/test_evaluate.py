import numpy as np
import pytest
from floodlab.evaluate import binary_metrics,evaluate
from floodlab.fixture import create
from floodlab.pipeline import run

def test_metrics_known_counts():
    m=binary_metrics(np.array([1,1,0,0]),np.array([1,0,1,0]),np.ones(4,bool))
    assert (m['tp'],m['fp'],m['fn'],m['tn'])==(1,1,1,1)
    assert m['iou']==1/3 and m['f1']==.5

def test_empty_is_not_perfect():
    m=binary_metrics(np.zeros(4),np.zeros(4),np.ones(4,bool))
    assert m['iou'] is None and m['recall'] is None

def test_no_coverage():
    m=binary_metrics(np.ones(4),np.ones(4),np.zeros(4,bool))
    assert m['valid_pixels']==0 and m['iou'] is None

def test_semantics_required():
    with pytest.raises(ValueError,match='semantics'):evaluate('absent','absent')

def test_freeze_rejects_mutation(tmp_path):
    m=create(tmp_path/'input');r=tmp_path/'run';run(m,r);(r/'result.json').write_text('{}')
    with pytest.raises(ValueError,match='Frozen'):evaluate(r,'absent',True)
