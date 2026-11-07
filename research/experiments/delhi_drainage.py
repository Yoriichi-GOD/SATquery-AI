"""Official mapped-drain context and DSM/reference agreement, not exposure truth."""
import argparse,json,csv,math
from pathlib import Path
from collections import Counter
import numpy as np
import rasterio
from shapely.geometry import shape,LineString,MultiLineString,Polygon,Point,mapping
from shapely.ops import unary_union
from shapely import points,distance,line_interpolate_point,get_parts
from pyproj import Transformer
from research.cases.process_campaign import roi,roi_geometry,metric_grid,warp,terrain,safe_stats
from research.terrain_exposure.graph import mask_geometry
from research.terrain_exposure.io import Grid,save_json,sha256

ROOT=Path(__file__).resolve().parents[2]
PROTOCOL=ROOT/'research/experiments/validation-closure-20261107.json'

def esri_geometry(geom,kind):
    if geom is None:return None
    if kind=='esriGeometryPolyline':return MultiLineString(geom['paths'])
    if kind=='esriGeometryPoint':return Point(geom['x'],geom['y'])
    if kind=='esriGeometryPolygon':
        # ArcGIS rings use clockwise shells and counterclockwise holes. Keep topology.
        from shapely.geometry import LinearRing
        shells=[r for r in geom['rings'] if not LinearRing(r).is_ccw]
        holes=[r for r in geom['rings'] if LinearRing(r).is_ccw]
        polygons=[]
        for shell in shells:
            p=Polygon(shell);owned=[h for h in holes if p.covers(Polygon(h).representative_point())]
            polygons.append(Polygon(shell,owned))
        return unary_union(polygons)
    raise ValueError('Unsupported official native geometry')

def load_layer(folder,record):
    p=folder/record['file']
    if sha256(p)!=record['sha256']:raise ValueError('Official reference hash changed')
    data=json.loads(p.read_text())
    if data['spatialReference']['wkid']!=32643:raise ValueError('Native query CRS mismatch')
    rows=[]
    for feature in data['features']:
        g=esri_geometry(feature.get('geometry'),data['geometryType'])
        if g is None or g.is_empty or not g.is_valid:raise ValueError('Missing/invalid official geometry; no silent repair')
        rows.append((g,feature['attributes']))
    return rows

def coverage_near_gain(gain_geometry,drains,distances=(30,90,150)):
    total=gain_geometry.area
    if drains.is_empty:return {str(d):{'area_ha':None,'fraction':None,'state':'NO_MAPPED_REFERENCE'} for d in distances}
    return {str(d):{'area_ha':gain_geometry.intersection(drains.buffer(d)).area/10000,
        'fraction':None if total==0 else gain_geometry.intersection(drains.buffer(d)).area/total,
        'interpretation':'Proximity association only; not blockage, causality or confirmed exposure'} for d in distances}

def run(sources,reference,output):
    sources=Path(sources);ref=Path(reference);out=Path(output)
    if out.exists():raise FileExistsError('Keep drainage analyses immutable')
    out.mkdir(parents=True);protocol=json.loads(PROTOCOL.read_text());cfg=protocol['delhi_drainage']
    records=json.loads((ref/'acquisition.json').read_text())
    if records['protocol_sha256']!=sha256(PROTOCOL):raise ValueError('Reference extraction protocol changed')
    save_json(out/'protocol.json',protocol);inside=shape(roi_geometry(cfg['bbox'],cfg['crs']))
    inventories={};layer_counts=[];widths=[];inverts=[];nodepairs=[];updates=Counter();knownrows=[];waterlogging=[]
    for record in records['layers']:
        if record['state']!='ACQUIRED_NATIVE_GEOMETRY':continue
        rows=load_layer(ref,record);clipped=[]
        for g,attrs in rows:
            hit=g.intersection(inside)
            if not hit.is_empty:clipped.append((hit,attrs))
        layer_counts.append({'service':record['service'],'name':record['name'],'query_features':len(rows),'positive_measure_intersections':sum(g.length>0 or g.area>0 or g.geom_type=='Point' for g,a in clipped)})
        if record['service']=='DIFC/sangam' and record['layer_id']==3:
            inventories['Sangam_Storm_Drain']=unary_union([g for g,a in clipped]);knownrows=clipped
            for g,attrs in clipped:
                for values,key in [(widths,'Drn_Wd_m'),(inverts,'IL_MSL')]:
                    value=attrs.get(key)
                    if isinstance(value,(int,float)) and np.isfinite(value) and value>0:values.append(value)
                updates[str(attrs.get('Upd_date'))]+=1
                n0,n1=attrs.get('INLETNODE'),attrs.get('OUTLETNODE')
                if isinstance(n0,str) and n0.strip() and isinstance(n1,str) and n1.strip():nodepairs.append((n0,n1))
        elif record['service'].endswith('08082024'):
            inventories.setdefault('Aug2024_Agency_Drains',[])
            inventories['Aug2024_Agency_Drains'] += [g for g,a in clipped]
        elif record['name']=='WaterLogging_50m':waterlogging=clipped
    inventories['Aug2024_Agency_Drains']=unary_union(inventories.get('Aug2024_Agency_Drains',[]))
    main=inventories.get('Sangam_Storm_Drain',LineString())
    # Native10m gains retain the same class and ROI contract as the parent release.
    with rasterio.open(sources/'lulc-2017.tif') as before,rasterio.open(sources/'lulc-2023.tif') as after:
        if before.shape!=after.shape or before.transform!=after.transform or before.crs!=after.crs:raise ValueError('Annual native grids differ')
        a,b=before.read(1),after.read(1);r=roi(cfg['bbox'],a.shape,before.transform,before.crs)
        valid=r&(before.read_masks(1)>0)&(after.read_masks(1)>0)&~np.isin(a,[0,10])&~np.isin(b,[0,10])
        gain=valid&(a!=7)&(b==7)
        grid=Grid(before.shape,before.transform,before.crs.to_string())
        geom=mask_geometry(gain,grid);area=gain.sum()*grid.area
    assert abs(geom.area-area)<.001,'Gain vector/raster area mismatch'
    context={name:{'mapped_unique_clipped_length_m':float(g.length),'gross_built_gain_near_mapped_drains':coverage_near_gain(geom,g)} for name,g in inventories.items()}
    parent=json.loads((ROOT/'research/experiments/case-campaign-20261107.json').read_text())
    casecfg=parent['cases']['sangam-vihar'];acquisition=json.loads((sources/'acquisition.json').read_text())
    tr,hydros=terrain(sources,casecfg,out,parent,acquisition['assets']);agreement={}
    for cell,h in hydros.items():
        # Cell-centre model-stream distance to exact mapped drainage, without matching/tuning.
        rr,cc=np.where(h.streams&h.valid)
        coords=points(h.grid.transform.c+(cc+.5)*cell,h.grid.transform.f-(rr+.5)*cell)
        delta=distance(coords,main) if not main.is_empty else np.full(len(coords),np.nan)
        # Reference-to-model distance: drain points sampled every10m, equal-length quadrature.
        samples=[]
        for line in get_parts(main):
            if line.length>0:samples.extend(line_interpolate_point(line,np.arange(5,line.length,10)).tolist())
        if len(coords) and samples:
            from shapely import STRtree
            tree=STRtree(coords);idx=tree.nearest(samples);refdelta=distance(np.array(samples,dtype=object),coords[idx])
        else:refdelta=np.array([])
        agreement[str(cell)]={'model_stream_cells':int(len(coords)),'stream_to_mapped_drain_m':safe_stats(delta),
            'mapped_drain_to_modelstream_m':safe_stats(refdelta),'reference_sampling':'Every10m along unique clipped lines;modelstreamcellcenters',
            'within30m_fraction':None if not len(delta) else float((delta<=30).mean()),
            'within90m_fraction':None if not len(delta) else float((delta<=90).mean()),
            'interpretation':'Descriptive DSM-vs-engineered-network agreement, not exposure precision/recall'}
    nodes=set(n for pair in nodepairs for n in pair)
    info={'case_id':'southern-sangam-vihar','role':'OFFICIAL_MAPPED_CONTEXT_NOT_SURVEYED_GROUND_TRUTH',
        'protocol_sha256':sha256(PROTOCOL),'native_reference_acquisition_sha256':sha256(ref/'acquisition.json'),
        'layer_counts':layer_counts,'inventories':context,'urban_gross_gain_ha':float(area/10000),
        'reported_width_m_positive_only':safe_stats(widths),'reported_invert_MSL_positive_only':safe_stats(inverts),
        'width_necessary_sampling_median_half_m':None if not widths else float(np.median(widths)/2),
        'reported_width_and_elevation_values':'Nonpositive/null values excluded as unknown, not physical zero; units inferred from published field names; vertical datum not independently verified',
        'attribute_update_strings':dict(updates),'mapped_node_pairs':len(nodepairs),'mapped_distinct_nodes':len(nodes),
        'network_warning':'Node identifiers retained for future verified routing; no network direction/capacity/condition inferred in this experiment',
        'waterlogging_mapped_points':len(waterlogging),'waterlogging_label_coverage':'Positive-only point with unknown eventdate; no exposed/unexposed denominator',
        'terrain_reference_agreement':agreement,'accuracy_metrics':'NOT_ASSESSED:No matched exposuretruth or complete positive/negative labels',
        'official_disclaimer':'GSDL does not guarantee accuracy/reliability/completeness or groundtruthing; supplying department responsible https://gsdl.org.in/',
        'license':'Raw official native geometry retained private locally; redistribution terms not established',
        'limitations':['Drainage vintage and2017/2023network completeness unknown','Drain proximity cannot prove encroachment, blockage or floodcausality',
            'Coarse DSM omits culverts and engineered conveyance; source epochs differ','No future-vintage geometry is used as independent2017/2023exposuretruth']}
    save_json(out/'summary.json',info)
    draw(out,hydros[30],inventories,geom,waterlogging)
    save_json(out/'manifest.json',{'files':{p.name:sha256(p) for p in out.iterdir() if p.is_file()}})
    print(json.dumps({'case':'sangam-vihar','drain_length_m':main.length,'gross_built_gain_ha':area/10000,
        'within90m_ha':context['Sangam_Storm_Drain']['gross_built_gain_near_mapped_drains']['90']['area_ha'],
        'width_median_m':safe_stats(widths)['median']}),flush=True)
    return info

def draw(out,h,inventories,gain,waterlogging):
    import matplotlib;matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from rasterio.plot import plotting_extent
    fig,ax=plt.subplots(figsize=(9,7),layout='constrained')
    ax.imshow(np.where(h.valid,h.original,np.nan),extent=plotting_extent(h.original,h.grid.transform),cmap='Greys',alpha=.5)
    for line in get_parts(inventories['Sangam_Storm_Drain']):
        if not line.is_empty:ax.plot(*line.xy,color='#176a98',lw=1)
    for polygon in get_parts(gain):
        ax.fill(*polygon.exterior.xy,color='#a35028',alpha=.7,lw=0)
    for point,attrs in waterlogging:ax.scatter(point.x,point.y,color='#bd1e25',s=70,marker='x')
    from matplotlib.lines import Line2D
    ax.legend(handles=[Line2D([0],[0],color='#176a98',label='Official mapped drains; vintage uncertain'),
        Line2D([0],[0],color='#a35028',lw=6,label='2017→2023 built-class gains; model output'),
        Line2D([0],[0],color='#bd1e25',marker='x',ls='',label='Mapped waterlogging point; eventdate unknown')],fontsize=8)
    ax.set_aspect('equal');ax.set_xlabel('Easting (m), EPSG:32643');ax.set_ylabel('Northing (m)')
    ax.set_title('Southern Sangam Vihar: observed map relationships\nProximity is not blockage, causality or exposure truth',fontsize=11)
    fig.savefig(out/'drainage-context.png',dpi=170);fig.savefig(out/'drainage-context.pdf');plt.close(fig)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--sources',required=True);p.add_argument('--reference',required=True);p.add_argument('--output',required=True)
    a=p.parse_args();run(a.sources,a.reference,a.output)
