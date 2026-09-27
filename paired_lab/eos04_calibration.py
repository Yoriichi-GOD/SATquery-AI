"""EOS-04 detected-product beta0 calibration; no semantic model inference.
Reference: NRSC EOS-04 Handbook section 4.5, printed pages 66-68.
"""
import numpy as np

def beta0(dn, calibration_db, noise_bias):
    """Return signed linear beta0 and positive-only beta0 dB.

    Negative noise-corrected power is retained in linear output. It is not
    clipped into fabricated positive backscatter; dB is undefined there.
    Input masks/nodata remain the caller's responsibility.
    """
    a=np.asarray(dn,dtype=np.float64)
    if not np.isfinite(a).all() or np.any(a<0):
        raise ValueError('Expected finite nonnegative detected-image digital numbers.')
    if not np.isfinite(calibration_db) or not np.isfinite(noise_bias) or noise_bias<0:
        raise ValueError('Valid product beta0 calibration and nonnegative noise bias are required.')
    scale=10.0**(float(calibration_db)/10.0)
    if not np.isfinite(scale) or scale<=0:raise ValueError('Invalid calibration scale.')
    linear=(np.square(a)-float(noise_bias))/scale
    db=np.full(a.shape,np.nan,dtype=np.float64)
    positive=linear>0
    db[positive]=10*np.log10(linear[positive])
    return linear,db
