"""Typed source–pathway–receptor evidence, with exact and coarse relationships separate."""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import csv
import math
from pathlib import Path

import numpy as np
from pyproj import Transformer
from rasterio.features import rasterize, shapes
from shapely.geometry import shape, mapping, Point, LineString, box
from shapely.ops import transform as transform_geom, unary_union
from shapely import transform as vector_transform

from . import SCHEMA_VERSION
from .hydrology import path
from .io import Grid, canonical_hash, save_json, write_raster, resolution_status, sha256


@dataclass
class Observation:
    layer: str
    candidate: np.ndarray
    valid: np.ndarray
    grid: Grid
    provenance: dict
    times: list[str]
    method: str
    registration_status: str = "UNVERIFIED"

    def __post_init__(self):
        self.candidate = np.asarray(self.candidate, bool)
        self.valid = np.asarray(self.valid, bool)
        if self.candidate.shape != self.grid.shape or self.valid.shape != self.grid.shape:
            raise ValueError("Observation/grid shape mismatch")
        if (self.candidate & ~self.valid).any():
            raise ValueError("Candidate outside valid observation")
        if not self.times or not self.method or not self.provenance.get("sha256"):
            raise ValueError("Observation times, method and source hash required")


@dataclass
class Receptor:
    id: str
    kind: str
    geometry: object
    crs: str
    provenance: dict
    time: str

    def __post_init__(self):
        if not self.id or self.kind not in {"building", "road", "bridge", "settlement", "infrastructure"}:
            raise ValueError("Invalid receptor identity/type")
        if self.geometry.is_empty or not self.geometry.is_valid or not self.time or not self.provenance.get("sha256"):
            raise ValueError("Valid geometry, observation time and source hash required")


def project(geometry, source_crs, target_crs):
    transformer = Transformer.from_crs(source_crs, target_crs, always_xy=True)
    return vector_transform(geometry, transformer.transform, interleaved=False)


def mask_geometry(mask, grid):
    geoms = [shape(g) for g, value in shapes(np.asarray(mask, np.uint8), mask=mask,
                                           transform=grid.transform, connectivity=4) if value == 1]
    return unary_union(geoms)


def touched_cells(geometry, grid, valid):
    burnt = rasterize([(mapping(geometry), 1)], out_shape=grid.shape, transform=grid.transform,
                     all_touched=True, dtype="uint8").astype(bool)
    result = set()
    for index in map(int, np.flatnonzero(burnt & valid)):
        x, y = grid.centre(index)
        cell = box(x-grid.transform.a/2, y+grid.transform.e/2,
                   x+grid.transform.a/2, y-grid.transform.e/2)
        hit = geometry.intersection(cell)
        positive = (hit.area > 0 if "Polygon" in geometry.geom_type else
                    hit.length > 0 if "Line" in geometry.geom_type else not hit.is_empty)
        if positive:
            result.add(index)
    return result


def geometry_coverage(geometry, support):
    """Exact planar area/length coverage; point uses covers(). No sampling-only negatives."""
    if geometry.is_empty:
        return None
    if geometry.geom_type in {"Point", "MultiPoint"}:
        points = [geometry] if geometry.geom_type == "Point" else list(geometry.geoms)
        return sum(support.covers(p) for p in points)/len(points)
    denominator = geometry.area if "Polygon" in geometry.geom_type else geometry.length
    overlap = geometry.intersection(support)
    numerator = overlap.area if "Polygon" in geometry.geom_type else overlap.length
    return None if denominator <= 0 else min(1.0, max(0.0, numerator / denominator))


def components(observation, crs):
    result = []
    for g, value in shapes(observation.candidate.astype("uint8"), mask=observation.candidate,
                            transform=observation.grid.transform, connectivity=4):
        if value != 1:
            continue
        native = shape(g)
        geometry = project(native, observation.grid.crs, crs)
        identity = canonical_hash({"layer": observation.layer, "source": observation.provenance["sha256"],
                                   "geometry": mapping(native)})[:20]
        result.append({"id": f"source:{observation.layer}:{identity}", "geometry": geometry,
                       "native_pixel_count": int(round(native.area / observation.grid.area))})
    return sorted(result, key=lambda item: item["id"])


def finite_stat(array, indices, reducer=np.min):
    values = array.ravel()[sorted(indices)] if indices else np.array([])
    values = values[np.isfinite(values)]
    return float(reducer(values)) if len(values) else None


def build_graph(hydro, observations, receptors, terrain_provenance, *, target_width_m=None):
    if len({o.layer for o in observations}) != len(observations) or not observations:
        raise ValueError("Unique observation layers required")
    if len({r.id for r in receptors}) != len(receptors):
        raise ValueError("Receptor IDs must be unique")
    if hydro.valid.sum() > 100_000 or len(receptors) > 10_000:
        raise ValueError("Graph size exceeds bounded research implementation")
    grid = hydro.grid
    dem_support = mask_geometry(hydro.valid, grid)
    scale = resolution_status(max(grid.transform.a, -grid.transform.e), target_width_m)
    nodes, edges, relationships, layer_counts = [], [], [], {}
    terrain_ref = {**terrain_provenance, "grid": grid.describe(), "method": hydro.summary["flow_method"]}
    if not terrain_ref.get("sha256"):
        raise ValueError("Terrain source hash required")

    def node(identity, node_type, geometry, provenance, times, support, quality, **attributes):
        nodes.append({"id": identity, "type": node_type, "geometry": mapping(geometry), "crs": grid.crs,
                      "provenance": provenance, "observation_times": times, "support": support,
                      "quality": quality, "attributes": attributes})

    def edge(origin, destination, kind, geometry=None, **attributes):
        value = {"source": origin, "target": destination, "type": kind, "attributes": attributes,
                 "provenance": terrain_ref if kind == "D8_DOWNSTREAM" else attributes.pop("provenance", {}),
                 "geometry": None if geometry is None else mapping(geometry), "crs": grid.crs}
        value["id"] = "edge:" + canonical_hash(value)[:24]
        edges.append(value)

    for i in map(int, np.flatnonzero(hydro.valid)):
        node(f"pathway:{i}", "pathway", Point(grid.centre(i)), terrain_ref,
             [terrain_ref.get("observation_time", "historical DSM; acquisition date unavailable")],
             {"dem_cell": i, "valid": True}, {"resolution": scale, "boundary_flags": int(hydro.boundary.ravel()[i])},
             elevation_m=float(hydro.original.ravel()[i]), filled_elevation_m=float(hydro.filled.ravel()[i]),
             contributing_area_m2=float(hydro.accumulation.ravel()[i]*grid.area),
             hand_m=finite_stat(hydro.hand, {i}), drainage_cell=int(hydro.drainage_id.ravel()[i]),
             catchment_outlet=int(hydro.catchment.ravel()[i]))
        d = int(hydro.downstream.ravel()[i])
        if d >= 0:
            edge(f"pathway:{i}", f"pathway:{d}", "D8_DOWNSTREAM", LineString([grid.centre(i), grid.centre(d)]),
                 method=hydro.summary["flow_method"], potential_only=True,
                 length_m=math.dist(grid.centre(i), grid.centre(d)))

    projected_receptors = []
    for receptor in sorted(receptors, key=lambda r: r.id):
        g = project(receptor.geometry, receptor.crs, grid.crs)
        cells = touched_cells(g, grid, hydro.valid)
        coverage = geometry_coverage(g, dem_support)
        projected_receptors.append((receptor, g, cells, coverage))
        node("receptor:" + receptor.id, "receptor", g, receptor.provenance, [receptor.time],
             {"dem_valid_fraction": coverage, "dem_cells": sorted(cells)},
             {"infrastructure_completeness": "UNKNOWN", "resolution": scale},
             kind=receptor.kind, hand_m=finite_stat(hydro.hand, cells),
             slope_deg=finite_stat(hydro.slope, cells, np.median))
        for cell in sorted(cells):
            edge(f"pathway:{cell}", "receptor:" + receptor.id, "RECEPTOR_OVERLAPS_CELL",
                 provenance=receptor.provenance, subcell_location_unresolved=True)

    for observation in observations:
        support = project(mask_geometry(observation.valid, observation.grid), observation.grid.crs, grid.crs)
        sources = components(observation, grid.crs)
        layer_counts[observation.layer] = {"candidate_pixels": int(observation.candidate.sum()),
            "valid_pixels": int(observation.valid.sum()), "unknown_pixels": int((~observation.valid).sum()),
            "candidate_area_m2": float(observation.candidate.sum()*observation.grid.area),
            "candidate_components": len(sources), "grid": observation.grid.describe(),
            "provenance": observation.provenance, "times": observation.times}
        for source in sources:
            g = source["geometry"]
            source_cells = touched_cells(g, grid, hydro.valid)
            dem_fraction = geometry_coverage(g, dem_support)
            node(source["id"], "source", g, observation.provenance, observation.times,
                 {"native_pixel_count": source["native_pixel_count"], "dem_valid_fraction": dem_fraction,
                  "mask_sha256": observation.provenance["sha256"], "dem_cells": sorted(source_cells)},
                 {"registration": observation.registration_status, "confidence": "UNCALIBRATED_OR_UNAVAILABLE"},
                 layer=observation.layer, inference_method=observation.method, area_m2=float(g.area))
            routes = {cell: path(hydro, cell) for cell in sorted(source_cells)}
            for cell in sorted(source_cells):
                edge(source["id"], f"pathway:{cell}", "SOURCE_OVERLAPS_CELL",
                     provenance=observation.provenance, subcell_location_unresolved=True)
            for receptor, rg, receptor_cells, receptor_dem_fraction in projected_receptors:
                observed_fraction = geometry_coverage(rg, support)
                intersection = g.intersection(rg)
                direct = not intersection.is_empty
                best_path = None
                best_length = None
                for start, route in routes.items():
                    for position, cell in enumerate(route):
                        if position > 0 and cell in receptor_cells:
                            subset = route[:position+1]
                            length = sum(math.dist(grid.centre(a), grid.centre(b)) for a, b in zip(subset, subset[1:]))
                            if best_length is None or length < best_length:
                                best_length, best_path = length, subset
                            break
                fully_observed = observed_fraction is not None and observed_fraction >= 1-1e-6
                complete_terrain = (dem_fraction is not None and dem_fraction >= 1-1e-6 and
                                    receptor_dem_fraction is not None and receptor_dem_fraction >= 1-1e-6)
                if direct:
                    status, tier = "DIRECT_GEOMETRIC_INTERSECTION", 3
                elif not complete_terrain or not fully_observed:
                    status, tier = "UNAVAILABLE_EVIDENCE", None
                elif best_path:
                    status, tier = "POTENTIAL_DOWNSTREAM_CONNECTION", 2
                elif source_cells & receptor_cells:
                    status, tier = "UNRESOLVED_WITHIN_DEM_CELL", None
                else:
                    status, tier = "NOT_CONNECTED_WITHIN_DOMAIN", 0
                along = best_length if status == "POTENTIAL_DOWNSTREAM_CONNECTION" else (0.0 if direct else None)
                source_height = finite_stat(hydro.original, source_cells, np.median)
                receptor_height = finite_stat(hydro.original, receptor_cells, np.median)
                relationship = {"source_id": source["id"], "source_layer": observation.layer,
                    "receptor_id": receptor.id, "receptor_type": receptor.kind, "status": status,
                    "direct_intersection": direct, "intersection_area_m2": float(intersection.area),
                    "intersection_length_m": float(intersection.length) if receptor.kind in {"road", "bridge"} else None,
                    "distance_m": float(g.distance(rg)), "along_network_distance_m": along,
                    "pathway_cells": best_path if status == "POTENTIAL_DOWNSTREAM_CONNECTION" else [],
                    "relative_elevation_receptor_minus_source_m": None if source_height is None or receptor_height is None else receptor_height-source_height,
                    "receptor_hand_m": finite_stat(hydro.hand, receptor_cells),
                    "receptor_slope_deg": finite_stat(hydro.slope, receptor_cells, np.median),
                    "receptor_observation_fraction": observed_fraction, "source_dem_fraction": dem_fraction,
                    "receptor_dem_fraction": receptor_dem_fraction, "registration_status": observation.registration_status,
                    "temporal_compatibility": "TIMESTAMPS_RECORDED_EVENT_COMPATIBILITY_NOT_CERTIFIED",
                    "source_times": observation.times, "receptor_time": receptor.time,
                    "ordinal_screening_tier": tier, "resolution_status": scale["status"],
                    "uncertainty": ["Not calibrated probability", "Historical infrastructure completeness unknown",
                                    "DEM path is potential topographic connectivity, not event propagation",
                                    "Same-cell overlap is not direct geometric intersection"]}
                relationships.append(relationship)
                if direct or status == "POTENTIAL_DOWNSTREAM_CONNECTION":
                    edge(source["id"], "receptor:" + receptor.id, status, intersection if direct else None,
                         provenance={"observation": observation.provenance, "terrain": terrain_ref, "receptor": receptor.provenance},
                         **{k: relationship[k] for k in ["along_network_distance_m", "distance_m", "pathway_cells", "registration_status"]})
    statuses = Counter(r["status"] for r in relationships)
    graph = {"schema_version": SCHEMA_VERSION, "crs": grid.crs, "grid": grid.describe(),
             "method": "Uncalibrated ordinal screening: direct intersection > potential D8 connection; unknown stays null",
             "hydrology": hydro.summary, "terrain_provenance": terrain_ref, "resolution": scale,
             "observations": layer_counts, "nodes": nodes, "edges": edges, "relationships": relationships,
             "summary": {"node_count": len(nodes), "edge_count": len(edges), "receptor_count": len(receptors),
                         "relationship_count": len(relationships), "relationship_statuses": dict(statuses)},
             "limitations": ["No rainfall, discharge, water depth, floodwave or debris-flow dynamics",
                             "Coarse DSM includes vegetation/buildings; pathways are scale dependent",
                             "Observation quality and physical registration require independent checking",
                             "No damaged, safe, blocked or inaccessible infrastructure is inferred"]}
    graph["content_sha256"] = canonical_hash(graph)
    return graph


def receptor_summary(graph):
    """Compact operator view; positive support may coexist with unavailable relationships."""
    grouped = {}
    for node in graph["nodes"]:
        if node["type"] == "receptor":
            grouped[node["id"].removeprefix("receptor:")] = {
                "id": node["id"].removeprefix("receptor:"), "kind": node["attributes"]["kind"],
                "hand_m": node["attributes"]["hand_m"], "slope_deg": node["attributes"]["slope_deg"],
                "layers": {}, "provenance": node["provenance"]}
    for row in graph["relationships"]:
        receptor = grouped[row["receptor_id"]]
        layer = receptor["layers"].setdefault(row["source_layer"], {
            "direct_intersection": False, "potential_connection": False, "unknown_relationships": 0,
            "same_cell_unresolved": 0, "distance_m": None, "along_network_distance_m": None,
            "observation_fraction": row["receptor_observation_fraction"], "ordinal_screening_tier": None})
        layer["direct_intersection"] |= row["direct_intersection"]
        layer["potential_connection"] |= row["status"] == "POTENTIAL_DOWNSTREAM_CONNECTION"
        layer["unknown_relationships"] += row["status"] == "UNAVAILABLE_EVIDENCE"
        layer["same_cell_unresolved"] += row["status"] == "UNRESOLVED_WITHIN_DEM_CELL"
        for key in ["distance_m", "along_network_distance_m"]:
            value = row[key]
            if value is not None and (layer[key] is None or value < layer[key]):
                layer[key] = value
    for receptor in grouped.values():
        for layer in receptor["layers"].values():
            layer["ordinal_screening_tier"] = (3 if layer["direct_intersection"] else
                2 if layer["potential_connection"] else None if layer["unknown_relationships"] or layer["same_cell_unresolved"] else 0)
    return {"schema_version": SCHEMA_VERSION, "method": graph["method"], "receptors": list(grouped.values()),
            "observations": graph["observations"], "resolution": graph["resolution"], "limitations": graph["limitations"]}


def export_graph(graph, hydro, output):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    fields = [k for k in graph["relationships"][0] if k not in {"pathway_cells", "uncertainty", "source_times"}] if graph["relationships"] else ["source_id", "receptor_id", "status"]
    with (output/"relationships.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(graph["relationships"])
    save_json(output/"receptors.json", receptor_summary(graph))
    stored = {k: v for k, v in graph.items() if k not in {"relationships", "content_sha256"}}
    stored["relationships_artifact"] = {"filename": "relationships.csv", "sha256": sha256(output/"relationships.csv"),
        "rows": len(graph["relationships"]), "note": "Timestamps and quality shared on source/receptor nodes; detailed path edges retained in graph"}
    stored["content_sha256"] = canonical_hash(stored)
    save_json(output/"graph.json", stored)
    features = []
    projector = Transformer.from_crs(graph["crs"], "EPSG:4326", always_xy=True)
    for node in graph["nodes"]:
        g = vector_transform(shape(node["geometry"]), projector.transform, interleaved=False)
        features.append({"type": "Feature", "id": node["id"], "geometry": mapping(g),
                         "properties": {"type": node["type"], **node["attributes"], "provenance": node["provenance"],
                                        "quality": node["quality"], "observation_times": node["observation_times"]}})
    save_json(output/"nodes.geojson", {"type": "FeatureCollection", "features": features})
    stream_features = []
    for edge in graph["edges"]:
        if edge["type"] == "D8_DOWNSTREAM" and edge["geometry"] is not None:
            g = vector_transform(shape(edge["geometry"]), projector.transform, interleaved=False)
            stream_features.append({"type": "Feature", "id": edge["id"], "geometry": mapping(g),
                                    "properties": {"source": edge["source"], "target": edge["target"], **edge["attributes"]}})
    save_json(output/"drainage.geojson", {"type": "FeatureCollection", "features": stream_features})
    for filename, array in {"conditioned_dem": hydro.filled, "fill_depth": hydro.filled-hydro.original,
            "flow_direction_d8": hydro.d8, "downstream_index": hydro.downstream,
            "contributing_area_m2": hydro.accumulation*hydro.grid.area, "streams": hydro.streams,
            "catchment_outlet": hydro.catchment, "hand_m": hydro.hand,
            "slope_deg": hydro.slope, "aspect_deg": hydro.aspect}.items():
        write_raster(output/(filename+".tif"), array, hydro.grid, hydro.valid)
    return stored
