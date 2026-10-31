/* Display adapters only. Measurements and source bytes remain backend-owned. */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else root.SQEvidence = factory();
})(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  'use strict';
  const asList=v=>Array.isArray(v)?v:typeof v==='string'?[v]:[];
  const finite = v => typeof v === 'number' && Number.isFinite(v);
  const number = (v, digits = 2) => finite(v) ? v.toLocaleString('en-GB', {maximumFractionDigits: digits}) : '—';
  const date = v => v && !Number.isNaN(Date.parse(v)) ? new Date(v).toISOString().slice(0, 10) : '—';
  const bounds = b => Array.isArray(b) && b.length === 4 && b.every(finite) ? b.map(v => v.toFixed(4)).join(', ') : 'No AOI selected';
  function flood(run, grid, debris = null) {
    const inputs = run.provenance?.inputs || [], artifacts = run.artifacts || [];
    const layer = (key, label, name, input, legend) => {
      const artifact = artifacts.find(a => a.name === name);
      return artifact ? {key, label, url: artifact.url, kind: key === 'water' ? 'Derived candidate mask' : 'Observed radar display',
        source: input?.source || 'Saved water threshold workflow', date: date(input?.datetime), units: input?.units || 'Categorical classes',
        sha256: artifact.sha256, sourceRecord: input || run.provenance, grid,
        legend, limitations: run.limitations || []} : null;
    };
    const layers = [layer('pre', 'Before SAR', 'pre.png', inputs[0], 'Recorded display stretch · not calibrated colours'),
      layer('post', 'After SAR', 'post.png', inputs[1], 'Recorded display stretch · not calibrated colours')].filter(Boolean);
    const prediction = artifacts.find(a => a.name === 'prediction.tif');
    if (prediction) layers.push({key: 'water', label: 'Water candidates', url: '/api/flood/runs/' + encodeURIComponent(run.id) + '/candidate.png',
      kind: 'Derived candidate mask', source: 'Fixed SAR threshold workflow', date: inputs.map(i => date(i.datetime)).join(' → '), units: 'Categorical classes',
      sha256: prediction.sha256, download: prediction.url, grid, sourceRecord: run.provenance,
      legend: 'Blue: water in both · Gold: new-water candidates · Gray: invalid', limitations: run.limitations || []});
    const s = run.summary || {};
    const measures = [['New-water candidates', finite(s.new_water_m2) ? s.new_water_m2 / 10000 : null, 'ha'],
      ['Building intersections', s.exposed_buildings, 'features'], ['Road intersections', s.exposed_road_m, 'm']].filter(r => finite(r[1]));
    const classes = finite(s.valid_pixels) && finite(s.new_water_pixels) && finite(s.water_in_both_pixels) && s.valid_pixels > 0 &&
      s.valid_pixels >= s.new_water_pixels + s.water_in_both_pixels ? [
        ['New-water candidate', s.new_water_pixels], ['Water in both', s.water_in_both_pixels],
        ['Other valid', s.valid_pixels - s.new_water_pixels - s.water_in_both_pixels]] : [];
    const distributions=classes.length?[{label:'Water candidate population',classes,denominator:s.valid_pixels}]:[];
    if(debris?.debris_available===true){
      const p=debris.provenance||{},ds=debris.summary||{},artifact=artifacts.find(a=>a.name==='debris-candidates.tif');
      layers.push({key:'debris',label:'Possible debris / surface change',url:'/api/flood/runs/'+encodeURIComponent(run.id)+'/debris-candidate.png',kind:'Unvalidated derived proxy',source:'Vegetation-to-bare + NDVI loss + SAR change',date:[p.pre_date,p.post_date].map(date).join(' to '),units:'Categorical classes',sha256:artifact?.sha256,download:artifact?.url,grid:debris.grid,sourceRecord:{provenance:p,coverage:debris.coverage,source_hashes:debris.source_hashes},legend:'Copper: possible debris / surface change; Gray: unknown; Dark: observed noncandidate',limitations:asList(p.limitations||run.limitations)});
      for(const row of [['Debris proxy candidates',finite(ds.debris_candidate_m2)?ds.debris_candidate_m2/10000:null,'ha'],['Debris building intersections',ds.debris_intersected_buildings,'features'],['Debris road intersections',ds.debris_intersected_road_m,'m']])if(finite(row[1]))measures.push(row);
      if(finite(ds.debris_valid_pixels)&&finite(ds.debris_candidate_pixels)&&ds.debris_valid_pixels>=ds.debris_candidate_pixels&&ds.debris_valid_pixels>0)distributions.push({label:'Debris proxy population / independent coverage',classes:[['Candidate',ds.debris_candidate_pixels],['Other valid',ds.debris_valid_pixels-ds.debris_candidate_pixels]],denominator:ds.debris_valid_pixels});
    }
    return {id: run.id, label: run.event_name, population: run.population, layers, measures, classes, distributions,
      classDenominator: s.valid_pixels, limitations: run.limitations || [], record: run,
      footer: {sources: [...new Set(inputs.map(i => i.source).filter(Boolean))].join(' · ') || 'Source not recorded',
        aoi: bounds(grid?.bbox_wgs84), dates: inputs.map(i => date(i.datetime)).join(' → ') || '—',
        resolution: grid?.pixel_size?.every(finite) ? grid.pixel_size.map(v => number(v)).join(' × ') + ' ' + (grid.crs?.startsWith('EPSG:326') || grid.crs?.startsWith('EPSG:327') ? 'm' : '(CRS units)') : '—',
        id: run.id}};
  }
  function terrain(scene) {
    const p = scene.provenance || {}, s = scene.statistics || {};
    return {id: scene.id, label: p.dataset, population: scene.population, record: scene,
      layers: [{key: 'dem', label: 'DSM elevation', kind: 'Measured surface model', source: p.dataset, date: p.release || '—', units: p.units,
        sha256: scene.hashes?.['analysis.tif'], download: '/api/terrain/scenes/' + encodeURIComponent(scene.id) + '/raster',
        sourceRecord: p, mesh: scene.mesh, grid: {crs: p.analysis_crs, pixel_size: p.analysis_pixel_size_m},
        legend: number(s.elevation_min_m) + ' → ' + number(s.elevation_max_m) + ' m · dark: low · white: high · transparent: NoData', limitations: scene.limitations || []}],
      measures: [['Minimum DSM', s.elevation_min_m, 'm'], ['Maximum DSM', s.elevation_max_m, 'm'], ['Median slope', s.slope_median_deg, '°']].filter(r => finite(r[1])),
      classes: [], limitations: scene.limitations || [], footer: {id: scene.id, sources: p.dataset || 'Copernicus DSM', aoi: bounds(p.bbox_requested_wgs84),
        dates: p.release || '—', resolution: finite(p.nominal_source_resolution_m) ? number(p.nominal_source_resolution_m) + ' m nominal' : '—'}};
  }
  function workspace(result, views) {
    return {id: result.id, label: result.task, population: 'CURRENT_WORKSPACE_RESULT', record: result,
      layers: views.map(([label, url], i) => ({key: 'output-' + i, label, url, kind: 'Run output / source preview', source: result.task,
        date: result.dates?.map(date).join(' → ') || '—', units: 'See recorded result', sourceRecord: result.input_checks || {},
        legend: label + ' · display preview; original data and parameters in Run JSON', limitations: result.limitations || []})),
      measures: [], classes: [], limitations: result.limitations || [], footer: {id: result.id, sources: result.task,
        aoi: 'AOI: see input metadata', dates: result.dates?.map(date).join(' → ') || '—', resolution: 'See input metadata'}};
  }
  return {finite, number, date, bounds, flood, terrain, workspace};
});
