import pytest
from floodlab.event_acquisition import validate_area
@pytest.mark.parametrize('bbox',[[1,2,1,3],[1,3,2,2],[170,0,-170,1],[0,85,1,86],[0,0,float('nan'),1]])
def test_invalid_or_unsupported_area_rejected(bbox):
 with pytest.raises(ValueError):validate_area(bbox)
def test_regular_bbox_accepted():assert validate_area([85.32,28.14,85.35,28.19]).area>0


def test_provider_product_suffix_does_not_hide_different_scenes():
 from floodlab.automatic import same_product
 assert same_product('S1D_A_COG.SAFE','S1D_A_COG')
 assert not same_product('S1D_A_COG.SAFE','S1D_B_COG')
