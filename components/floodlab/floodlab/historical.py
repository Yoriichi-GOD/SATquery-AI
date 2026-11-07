"""Historical road adapters: preserve original node IDs and fail closed on mismatch."""
from datetime import datetime
from shapely.geometry import shape,mapping
from shapely.ops import transform
DRIVABLE={'motorway','trunk','primary','secondary','tertiary','unclassified','residential','service','living_street','motorway_link','trunk_link','primary_link','secondary_link','tertiary_link'}
def historical_road(row,element,project,snapshot):
    tags=dict(row['tags'])
    if row['osm_type']!='way' or tags.get('highway') not in DRIVABLE:return None,'not_drivable_class'
    access=next((tags[k] for k in ('motor_vehicle','vehicle','access') if k in tags),'yes')
    if access in ('no','private','agricultural','forestry'):return None,'restricted_access'
    if element['id']!=row['osm_id'] or element['version']!=row['version']:raise ValueError('Historical way identity mismatch')
    stamp=datetime.fromisoformat(element['timestamp'].replace('Z','+00:00'))
    if stamp>snapshot or not row['edit_timestamp']<=snapshot<row['valid_to_timestamp']:raise ValueError('Post-event or wrong-snapshot way')
    geom=shape(row['geometry'])
    if geom.geom_type!='LineString' or not geom.is_valid:raise ValueError('Invalid graph geometry')
    nodes=element['nodes']
    if len(nodes)!=len(geom.coords):raise ValueError('Node-coordinate count mismatch')
    direction=tags.get('oneway','yes' if tags.get('junction')=='roundabout' or tags.get('highway')=='motorway' else 'no')
    if direction not in ('yes','no','1','0','-1','true','false'):return None,'unsupported_direction'
    return {'type':'Feature','id':f"way/{row['osm_id']}",'geometry':mapping(transform(project,geom)),'properties':{'kind':'bridge' if tags.get('bridge') not in (None,'no') else 'road','node_ids':nodes,'oneway':direction,'osm_version':row['version'],'tags':tags}},None
