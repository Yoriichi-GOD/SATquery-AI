/* Software-only API/display boundary checks. No satellite accuracy claim. */
'use strict';
const assert = require('node:assert/strict');
const D = require('../paired_lab/web/noir-data.js');
const checks = [];
const check = (name, fn) => { fn(); checks.push(name); };
const run = {id:'software-fixture', population:'SYNTHETIC_SOFTWARE_TEST', provenance:{inputs:[]},
  artifacts:[{name:'prediction.tif',sha256:'a'.repeat(64),url:'/api/software/prediction.tif'},
             {name:'debris-candidates.tif',sha256:'b'.repeat(64),url:'/api/software/debris.tif'}],
  summary:{new_water_m2:200,exposed_buildings:1,exposed_road_m:7,valid_pixels:20,new_water_pixels:2,water_in_both_pixels:1},limitations:['Software fixture']};
const debris = {debris_available:true,summary:{debris_candidate_m2:300,debris_candidate_pixels:3,debris_valid_pixels:10,debris_intersected_buildings:2,debris_intersected_road_m:9},
  grid:{crs:'EPSG:32645'},coverage:{valid_pixels:10,total_pixels:25},provenance:{pre_date:'2026-08-22',post_date:'2026-08-27',limitations:'Actual API uses a string for method limitations.'},source_hashes:{'debris-candidates.tif':'b'.repeat(64)}};
check('Missing debris does not create a debris layer or zero measurement',()=>{
  const r=D.flood(run,null,{debris_available:false});assert(!r.layers.some(l=>l.key==='debris'));assert(!r.measures.some(m=>m[0].startsWith('Debris')));
});
check('Debris source limitations match the renderer array contract',()=>{
  const layer=D.flood(run,null,debris).layers.find(l=>l.key==='debris');assert(Array.isArray(layer.limitations));assert.equal(layer.limitations[0],debris.provenance.limitations);
});
check('Water and debris denominators remain separate',()=>{
  const r=D.flood(run,null,debris);assert.deepEqual(r.distributions.map(d=>d.denominator),[20,10]);
});
check('The debris layer retains its own source hash, grid and optical dates',()=>{
  const l=D.flood(run,null,debris).layers.find(l=>l.key==='debris');assert.equal(l.sha256,'b'.repeat(64));assert.equal(l.grid,debris.grid);assert(l.date.includes('2026-08-22')&&l.date.includes('2026-08-27'));
});
check('Unknown numerical fields never become zero',()=>{
  const r=D.flood({...run,summary:{}},null,null);assert.deepEqual(r.measures,[]);assert.deepEqual(r.classes,[]);
});
console.log(JSON.stringify({scope:'Software display-contract checks only',passed:checks.length,checks},null,2));
