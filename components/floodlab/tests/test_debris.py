import numpy as np
from floodlab.debris import debris_candidates
def inputs():
 pre=np.ones((7,2,2),dtype='float32');post=pre.copy();pre[2]=.1;pre[3]=.5;post[2]=.3;post[3]=.3;pre[5]=4;post[5]=5
 return pre,post,np.zeros((2,2,2)),np.ones((2,2,2))*4,np.ones((2,2),bool),np.ones((2,2),bool)
def test_cloud_shadow_and_nodata_remain_unknown():
 a=list(inputs());a[1][5,0,0]=3;a[1][6,0,1]=0
 out=debris_candidates(*a);assert out[0,0]==255 and out[0,1]==255 and out[1,0]==1
def test_stable_bare_surface_is_not_new_debris():
 a=list(inputs());a[0][:]=a[1];assert not (debris_candidates(*a)==1).any()
def test_sar_support_required():
 a=list(inputs());a[3][:]=a[2];assert not (debris_candidates(*a)==1).any()
