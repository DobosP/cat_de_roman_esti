import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
const uiAdoptionSchema=JSON.parse(readFileSync(new URL('./ui-adoption.schema.json',import.meta.url)));
/** Validator for the explicit JSON Schema keywords used by the shipped kit schemas. */
export function validate(schema,value,root=schema,location='$') {
  if(typeof schema==='boolean'){assert.ok(schema,location);return;}
  if(schema.$ref){assert.ok(schema.$ref.startsWith('#/'),'external schema references require an explicit resolver');const target=schema.$ref.slice(2).split('/').reduce((node,key)=>node[key],root);return validate(target,value,root,location);}
  if('const' in schema)assert.deepEqual(value,schema.const,`${location}: const`);
  if(schema.enum)assert.ok(schema.enum.some(x=>JSON.stringify(x)===JSON.stringify(value)),`${location}: enum`);
  if(schema.type){const types=Array.isArray(schema.type)?schema.type:[schema.type];assert.ok(types.some(t=>t==='null'?value===null:t==='array'?Array.isArray(value):t==='object'?value!==null&&typeof value==='object'&&!Array.isArray(value):t==='integer'?Number.isInteger(value):t==='number'?typeof value==='number'&&Number.isFinite(value):typeof value===t),`${location}: type`);}
  if(typeof value==='number'){if(schema.minimum!==undefined)assert.ok(value>=schema.minimum,`${location}: minimum`);if(schema.maximum!==undefined)assert.ok(value<=schema.maximum,`${location}: maximum`);}
  if(typeof value==='string'){if(schema.minLength!==undefined)assert.ok(value.length>=schema.minLength,`${location}: minLength`);if(schema.pattern)assert.match(value,new RegExp(schema.pattern),`${location}: pattern`);}
  if(Array.isArray(value)){if(schema.minItems!==undefined)assert.ok(value.length>=schema.minItems,`${location}: minItems`);if(schema.maxItems!==undefined)assert.ok(value.length<=schema.maxItems,`${location}: maxItems`);if(schema.uniqueItems)assert.equal(new Set(value.map(x=>JSON.stringify(x))).size,value.length,`${location}: uniqueItems`);if(schema.items)value.forEach((x,i)=>validate(schema.items,x,root,`${location}[${i}]`));}
  if(value&&typeof value==='object'&&!Array.isArray(value)){
    if(schema.minProperties!==undefined)assert.ok(Object.keys(value).length>=schema.minProperties,`${location}: minProperties`);if(schema.maxProperties!==undefined)assert.ok(Object.keys(value).length<=schema.maxProperties,`${location}: maxProperties`);
    for(const key of schema.required??[])assert.ok(Object.hasOwn(value,key),`${location}: required ${key}`);
    for(const [key,child] of Object.entries(value)){if(schema.properties&&Object.hasOwn(schema.properties,key))validate(schema.properties[key],child,root,`${location}.${key}`);else if(schema.additionalProperties!==undefined)validate(schema.additionalProperties,child,root,`${location}.${key}`);}
  }
}
export function validateUiAdoptionEvidence(value) {
  validate(uiAdoptionSchema,value);
  assert.notEqual(value.selected_ui.version,value.legacy.version,'staged UI must identify the selected new SDK separately');
  return value;
}
/** Cross-field gate semantics accompany JSON Schema shape validation. */
export function assertGateResult(value) {
  const started=Date.parse(value.started),finished=Date.parse(value.finished);
  assert.ok(Number.isFinite(started)&&Number.isFinite(finished)&&finished>=started,'real ordered UTC timestamps required');
  for(const stamp of [value.started,value.finished])assert.equal(new Date(stamp).toISOString(),stamp.includes('.')?stamp:stamp.replace('Z','.000Z'),'canonical real UTC date required');
  assert.equal(new Set(value.checks.map(x=>x.name)).size,value.checks.length,'duplicate named checks');
  for(const entry of Object.values(value.budgets)){
    if(entry.limit===null)assert.equal(entry.status,'recorded','null budget must record measured actual');
    else assert.equal(entry.status,entry.actual<=entry.limit?'pass':'fail','budget status must reflect measured actual against committed limit');
  }
  if(value.status==='pass'){
    assert.equal(value.csp.violations,0,'CSP violations cannot pass');
    for(const check of value.checks){assert.notEqual(check.status,'fail','failed check cannot pass');if(check.status==='skipped')assert.ok(value.target==='unit'&&['no-dsn','no-device'].includes(check.reason),'only named permitted unit skips');}
    assert.ok(Object.values(value.budgets).every(entry=>entry.status!=='fail'),'failed budget cannot pass');
  }
  if(value.legacy_pending?.length){const checks=value.checks.filter(check=>['versions-check','v11-lint'].includes(check.name));assert.ok(checks.some(check=>['legacy-pending','legacy-pending;ui-staged-pending'].includes(check.reason)),'legacy findings must remain visible in named check reason');}
  if(value.ui_adoption){validateUiAdoptionEvidence(value.ui_adoption);assert.ok(value.checks.some(check=>['ui-adoption','kit:check','versions-check','toolchain-versions'].includes(check.name)&&['ui-staged-pending','legacy-pending;ui-staged-pending'].includes(check.reason)),'staged UI must remain visible in a named check reason');}
}
