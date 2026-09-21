"""Optical correspondence diagnostics. Does not silently warp or claim geographic truth."""
import sys
sys.path.insert(0,'/root/satquery/paired-lab/deps')
import cv2,numpy as np
def diagnose(a,b):
    a=np.asarray(a);b=np.asarray(b)
    if np.array_equal(a,b):return {'status':'identical','method':'exact decoded pixels','max_displacement_pixels':0.0}
    gray=lambda z:cv2.cvtColor(z.astype(np.uint8),cv2.COLOR_RGB2GRAY)
    detector=cv2.SIFT_create(nfeatures=1500)
    ka,da=detector.detectAndCompute(gray(a),None);kb,db=detector.detectAndCompute(gray(b),None)
    if da is None or db is None:return {'status':'unverified','reason':'Too few distinct optical features.'}
    pairs=cv2.BFMatcher().knnMatch(da,db,k=2)
    good=[m for pair in pairs if len(pair)==2 for m,n in [pair] if m.distance<.7*n.distance]
    if len(good)<10:return {'status':'unverified','reason':'Fewer than ten reliable optical feature matches.','matches':len(good)}
    x=np.float32([ka[m.queryIdx].pt for m in good]);y=np.float32([kb[m.trainIdx].pt for m in good])
    cv2.setRNGSeed(42)
    affine,inliers=cv2.estimateAffinePartial2D(x,y,method=cv2.RANSAC,ransacReprojThreshold=1.5,maxIters=3000,confidence=.99)
    if affine is None or int(inliers.sum())<10 or inliers.mean()<.5:return {'status':'unverified','reason':'No stable shared optical geometry.','matches':len(good)}
    h,w=a.shape[:2];corners=np.array([[0,0,1],[w-1,0,1],[0,h-1,1],[w-1,h-1,1]],dtype=float)
    displacement=np.linalg.norm(corners@affine.T-corners[:,:2],axis=1)
    maximum=float(displacement.max())
    return {'status':'misaligned' if maximum>1.5 else 'consistent','method':'SIFT ratio test + RANSAC similarity transform','matches':len(good),'inliers':int(inliers.sum()),'max_displacement_pixels':maximum,'estimated_affine':affine.tolist(),'limit_pixels':1.5,'warning':'A diagnostic of shared visible features; not surveyed geolocation or a subpixel registration certificate.'}
