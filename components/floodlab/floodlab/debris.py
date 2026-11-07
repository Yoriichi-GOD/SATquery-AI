"""Fixed diagnostic debris candidates, not a trained or validated debris classifier."""
import numpy as np
def debris_candidates(pre,post,sar_pre,sar_post,sar_valid,inside):
 if pre.shape!=post.shape or pre.shape[0]!=7 or pre.shape[1:]!=inside.shape:raise ValueError('Optical grid/shape mismatch')
 valid=inside&sar_valid&np.isfinite(pre).all(0)&np.isfinite(post).all(0)&(pre[6]==1)&(post[6]==1)&np.isin(pre[5],[4,5])&np.isin(post[5],[4,5])
 def ndvi(a):return np.divide(a[3]-a[2],a[3]+a[2],out=np.zeros_like(a[2]),where=(a[3]+a[2])>1e-6)
 before=ndvi(pre);after=ndvi(post)
 # Locked before examining reference geometry: vegetation-to-bare change plus SAR change.
 candidate=valid&(before>=0.4)&(after<=0.3)&((before-after)>=0.2)&(post[5]==5)&(np.max(np.abs(sar_post-sar_pre),axis=0)>=3)
 out=np.zeros(inside.shape,dtype='uint8');out[candidate]=1;out[~valid]=255
 return out
