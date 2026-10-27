"""Measure supplied independent point pairs; never invent correspondences."""
import argparse,json,math
from pathlib import Path

def measure(d):
    if d.get('coordinate_unit')!='metre':raise ValueError('Coordinates must share a projected metre CRS')
    if not d.get('projected_crs') or not d.get('reviewer'):raise ValueError('CRS and reviewer required')
    if d.get('used_to_fit_warp') is not False:raise ValueError('Points must be independent of warp fitting')
    pts=d.get('points',[])
    if len(pts)<6:raise ValueError('At least six independent point pairs required')
    if len({p['id'] for p in pts})!=len(pts):raise ValueError('Duplicate IDs')
    vectors=[];upper=[];locations=set()
    for p in pts:
        if not p.get('stable_ground_feature') or not p.get('description'):raise ValueError('Stable feature rationale required')
        a,b=p['optical_xy'],p['sar_xy'];u=p['localization_uncertainty_m']
        if len(a)!=2 or len(b)!=2 or not all(isinstance(x,(int,float)) and math.isfinite(x) for x in [*a,*b,u]) or u<0:raise ValueError('Invalid coordinates or uncertainty')
        if tuple(a) in locations:raise ValueError('Repeated optical point')
        locations.add(tuple(a));dx,dy=b[0]-a[0],b[1]-a[1];r=math.hypot(dx,dy)
        vectors.append(dict(id=p['id'],dx_m=dx,dy_m=dy,residual_m=r));upper.append(r+u)
    ordered=sorted(v['residual_m'] for v in vectors)
    def quantile(q):
        idx=(len(ordered)-1)*q;lo=int(idx);hi=math.ceil(idx)
        return ordered[lo]+(ordered[hi]-ordered[lo])*(idx-lo)
    return dict(count=len(pts),median_m=quantile(.5),p95_m=quantile(.95),rmse_m=math.sqrt(sum(x*x for x in ordered)/len(pts)),
      conservative_rmse_with_uncertainty_m=math.sqrt(sum(x*x for x in upper)/len(pts)),vectors=vectors,
      gate='MEASUREMENT_ONLY: spatial distribution, CRS provenance, reviewer independence and a predeclared task tolerance need review')

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('input',type=Path);a.add_argument('output',type=Path);p=a.parse_args()
    result=measure(json.loads(p.input.read_text()))
    with p.output.open('x') as f:json.dump(result,f,indent=2)
