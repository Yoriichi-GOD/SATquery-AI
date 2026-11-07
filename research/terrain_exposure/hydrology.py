"""Priority-Flood conditioning, deterministic D8, accumulation and flowpath HAND.

Barnes et al. (2014), doi:10.1016/j.cageo.2013.04.024, informs conditioning.
Nobre et al. (2011), doi:10.1016/j.jhydrol.2011.03.051, informs HAND.
No channel burning, hydraulic forcing or debris-flow runout is inferred.
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass
import heapq
import math

import numpy as np

from .io import Grid

# Clockwise from east. This public encoding is separate from flattened downstream IDs.
NEIGHBOURS = ((0, 1), (1, 1), (1, 0), (1, -1), (0, -1), (-1, -1), (-1, 0), (-1, 1))
D8_CODES = (1, 2, 4, 8, 16, 32, 64, 128)


def neighbours(index, shape):
    r, c = divmod(int(index), shape[1])
    for code, (dr, dc) in zip(D8_CODES, NEIGHBOURS):
        rr, cc = r + dr, c + dc
        if 0 <= rr < shape[0] and 0 <= cc < shape[1]:
            yield rr * shape[1] + cc, dr, dc, code


def condition(z, valid):
    """Fill to spill elevation. Outer edges and NoData-adjacent cells are open outlets.

    NoData is never filled. Treating its perimeter as open is an explicit unknown-boundary
    assumption; routes cannot be continued across it. Parent/order break flats without
    adding artificial epsilon elevation. Original elevations are retained separately.
    """
    shape = z.shape
    values, support = z.ravel(), valid.ravel()
    filled = values.copy()
    parent = np.full(values.size, -1, dtype=np.int64)
    order = np.full(values.size, -1, dtype=np.int64)
    seen = ~support.copy()
    boundary = np.zeros(values.size, dtype=np.uint8)  # 1 outer; 2 missing-data boundary
    heap = []
    for i in np.flatnonzero(support):
        r, c = divmod(int(i), shape[1])
        edge = r in (0, shape[0] - 1) or c in (0, shape[1] - 1)
        gap = any(not support[j] for j, *_ in neighbours(i, shape))
        if edge or gap:
            boundary[i] = (1 if edge else 0) | (2 if gap else 0)
            seen[i] = True
            heapq.heappush(heap, (float(values[i]), int(i)))
    sequence = 0
    while heap:
        height, i = heapq.heappop(heap)
        order[i] = sequence
        sequence += 1
        for j, *_ in neighbours(i, shape):
            if seen[j]:
                continue
            seen[j] = True
            filled[j] = max(values[j], height)
            parent[j] = i
            heapq.heappush(heap, (float(filled[j]), int(j)))
    if (support & (order < 0)).any():
        raise ValueError("Conditioning left an unvisited valid component")
    filled[~support] = np.nan
    return filled.reshape(shape), parent, order, boundary.reshape(shape)


def topological_order(downstream, valid):
    d, mask = downstream.ravel(), valid.ravel()
    incoming = np.zeros(d.size, dtype=np.int64)
    for i in np.flatnonzero(mask):
        if d[i] >= 0:
            if d[i] >= d.size or not mask[d[i]] or d[i] == i:
                raise ValueError("Invalid downstream index")
            incoming[d[i]] += 1
    queue = deque(int(i) for i in np.flatnonzero(mask & (incoming == 0)))
    ordered = []
    while queue:
        i = queue.popleft()
        ordered.append(i)
        if d[i] >= 0:
            incoming[d[i]] -= 1
            if incoming[d[i]] == 0:
                queue.append(int(d[i]))
    if len(ordered) != int(mask.sum()):
        raise ValueError("Downstream graph contains a cycle")
    return ordered


def slope_aspect(z, valid, grid):
    """Horn 3x3, original DSM. Aspect degrees clockwise from north; flat is unknown."""
    slope, aspect = np.full(z.shape, np.nan), np.full(z.shape, np.nan)
    if min(z.shape) < 3:
        return slope, aspect
    p = [z[i:z.shape[0]-2+i, j:z.shape[1]-2+j] for i in range(3) for j in range(3)]
    mask = np.ones((z.shape[0]-2, z.shape[1]-2), bool)
    for i in range(3):
        for j in range(3):
            mask &= valid[i:z.shape[0]-2+i, j:z.shape[1]-2+j]
    dx = ((p[2]+2*p[5]+p[8])-(p[0]+2*p[3]+p[6]))/(8*grid.transform.a)
    # Rows run south, so negate for a north-positive derivative.
    dy = -((p[6]+2*p[7]+p[8])-(p[0]+2*p[1]+p[2]))/(8*-grid.transform.e)
    gradient = np.hypot(dx, dy)
    slope[1:-1, 1:-1] = np.where(mask, np.degrees(np.arctan(gradient)), np.nan)
    aspect[1:-1, 1:-1] = np.where(mask & (gradient > 0), np.degrees(np.arctan2(-dx, -dy)) % 360, np.nan)
    return slope, aspect


@dataclass
class Hydrology:
    grid: Grid
    original: np.ndarray
    valid: np.ndarray
    filled: np.ndarray
    downstream: np.ndarray
    d8: np.ndarray
    accumulation: np.ndarray
    streams: np.ndarray
    hand: np.ndarray
    drainage_id: np.ndarray
    catchment: np.ndarray
    slope: np.ndarray
    aspect: np.ndarray
    boundary: np.ndarray
    summary: dict


def derive(z, valid, grid, stream_area_m2=100_000.0, conditioning="fill"):
    z = np.asarray(z, dtype=np.float64)
    valid = np.asarray(valid, bool) & np.isfinite(z)
    if z.shape != grid.shape or valid.shape != grid.shape or not valid.any():
        raise ValueError("DEM/grid mismatch or unavailable terrain")
    if conditioning not in ("fill", "none") or not math.isfinite(stream_area_m2) or stream_area_m2 <= 0:
        raise ValueError("Invalid conditioning or stream threshold")
    filled, parent, order, boundary = condition(z, valid)
    if conditioning == "none":
        filled = np.where(valid, z, np.nan)
    f, v = filled.ravel(), valid.ravel()
    downstream = np.full(z.size, -1, dtype=np.int64)
    codes = np.zeros(z.size, dtype=np.uint8)
    flat_routes = 0
    for i in np.flatnonzero(v):
        steepest = 0.0
        for j, dr, dc, code in neighbours(i, z.shape):
            if not v[j]:
                continue
            distance = math.hypot(dc * grid.transform.a, dr * -grid.transform.e)
            gradient = (f[i] - f[j])/distance
            if gradient > steepest:
                steepest, downstream[i], codes[i] = gradient, j, code
        if downstream[i] < 0 and conditioning == "fill" and parent[i] >= 0:
            p = parent[i]
            if f[p] <= f[i] and order[p] < order[i]:
                downstream[i] = p
                codes[i] = next(code for j, _, _, code in neighbours(i, z.shape) if j == p)
                flat_routes += 1
    topo = topological_order(downstream, valid)
    accumulation = v.astype(np.float64)
    for i in topo:
        if downstream[i] >= 0:
            accumulation[downstream[i]] += accumulation[i]
    streams = v & (accumulation * grid.area >= stream_area_m2)
    catchment = np.full(z.size, -1, dtype=np.int64)
    drainage = np.full(z.size, -1, dtype=np.int64)
    for i in reversed(topo):
        d = downstream[i]
        catchment[i] = i if d < 0 else catchment[d]
        drainage[i] = i if streams[i] else (-1 if d < 0 else drainage[d])
    hand = np.full(z.size, np.nan)
    ok = drainage >= 0
    # Use original DSM heights, not artificially filled elevations. Negative differences
    # caused by filling are explicitly unavailable, not clipped into zero-height positives.
    difference = z.ravel()[ok] - z.ravel()[drainage[ok]]
    hand[ok] = np.where(difference >= 0, difference, np.nan)
    slope, aspect = slope_aspect(z, valid, grid)
    outlets = v & (downstream < 0)
    if int(accumulation[outlets].sum()) != int(v.sum()):
        raise ValueError("Contributing-area conservation failed")
    summary = {"valid_cells": int(v.sum()), "total_cells": int(z.size),
               "valid_fraction": float(v.mean()), "outlets": int(outlets.sum()),
               "outlet_accumulation_sum_cells": int(accumulation[outlets].sum()),
               "filled_cells": int(((filled > z) & valid).sum()),
               "maximum_fill_m": float(np.max((filled-z)[valid])), "flat_parent_routes": flat_routes,
               "stream_cells": int(streams.sum()), "stream_threshold_m2": stream_area_m2,
               "hand_valid_cells": int(np.isfinite(hand).sum()),
               "conditioning": conditioning, "flow_method": "D8 steepest descent; Priority-Flood parent on filled flats",
               "boundary_condition": "Open outer edge and NoData perimeter; external contributing area unavailable",
               "interpretation": "Potential topographic drainage; not flood/debris propagation or flood depth"}
    return Hydrology(grid, z, valid, filled, downstream.reshape(z.shape), codes.reshape(z.shape),
                     accumulation.reshape(z.shape), streams.reshape(z.shape), hand.reshape(z.shape),
                     drainage.reshape(z.shape), catchment.reshape(z.shape), slope, aspect, boundary, summary)


def path(hydro, start):
    """Downstream in-domain cell IDs, including start, with defensive cycle detection."""
    if start < 0 or start >= hydro.valid.size or not hydro.valid.ravel()[start]:
        return []
    result, seen, i = [], set(), int(start)
    while i >= 0:
        if i in seen:
            raise ValueError("Cycle in drainage path")
        seen.add(i)
        result.append(i)
        i = int(hydro.downstream.ravel()[i])
    return result


def delineate_catchment(hydro, pour_index):
    if pour_index < 0 or pour_index >= hydro.valid.size or not hydro.valid.ravel()[pour_index]:
        raise ValueError("Pour point outside valid DEM")
    upstream = [[] for _ in range(hydro.valid.size)]
    for i in np.flatnonzero(hydro.valid):
        d = hydro.downstream.ravel()[i]
        if d >= 0:
            upstream[d].append(int(i))
    result = np.zeros(hydro.valid.size, bool)
    queue = [pour_index]
    while queue:
        i = queue.pop()
        result[i] = True
        queue.extend(upstream[i])
    return result.reshape(hydro.grid.shape)
