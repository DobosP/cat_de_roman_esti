import { readFileSync } from 'node:fs';
import assert from 'node:assert/strict';
import { validate,assertGateResult,validateUiAdoptionEvidence } from '../schemas/validate.mjs';
const schema=name=>JSON.parse(readFileSync(`web-kit/schemas/${name}.schema.json`));
const budgets=JSON.parse(readFileSync('budgets.json'));validate(schema('budgets'),budgets);
const budgetMissing=structuredClone(budgets);delete budgetMissing.js['cat-initial'].target_gz;assert.throws(()=>validate(schema('budgets'),budgetMissing));
const budgetNegative=structuredClone(budgets);budgetNegative.css.global.limit_gz=-1;assert.throws(()=>validate(schema('budgets'),budgetNegative));
const scope={schema:1,entries:[{paths:['frontend/src/legacy/**'],rules:['banned-imports'],reason:'Legacy migration remains',expires:'M2'}]};
validate(schema('lint-scope'),scope);const badScope=structuredClone(scope);badScope.entries[0].rules=['all'];assert.throws(()=>validate(schema('lint-scope'),badScope));delete badScope.entries[0].expires;assert.throws(()=>validate(schema('lint-scope'),badScope));
const hash='a'.repeat(64),kit={schema:1,core_tag:'core-v1.0',archives:{'ui.tgz':hash,'kit.tgz':hash,'go.tgz':hash}};
validate(schema('kit-lock'),kit);assert.throws(()=>validate(schema('kit-lock'),{...kit,archives:{...kit.archives,'extra.tgz':hash}}));
const result={schema:1,target:'unit',status:'pass',sha:'a'.repeat(40),dirty:false,tree_sha256:hash,toolchain_digest:`sha256:${hash}`,versions_lock_sha256:hash,parallel:4,started:'2026-10-06T00:00:00.000Z',finished:'2026-10-06T00:00:00.001Z',checks:[{name:'fixture',status:'pass',duration_ms:1}],csp:{stage:'report-only',violations:0,legacy_violations:0},budgets:{css:{limit:null,actual:25,status:'recorded'}},artifacts:[]};
validate(schema('result'),result);assertGateResult(result);
for(const patch of [{parallel:8},{checks:[]},{toolchain_digest:'declared-tag'},{csp:{stage:'enforced',violations:-1,legacy_violations:0}}])assert.throws(()=>validate(schema('result'),{...result,...patch}));
const pending={rule:'banned-imports',tool_or_import:'react',paths:['frontend/src/legacy/App.tsx'],expires:'M2',source:'lint/scope.json'};validate(schema('result'),{...result,legacy_pending:[pending]});assert.throws(()=>validate(schema('result'),{...result,legacy_pending:[{...pending,source:'inline-ignore'}]}));
const ui={mode:'staged-react',status:'pending',until:'S1-M2',source:'repo:kit-config',config_sha256:hash,legacy:{version:'0.3.0',archive_sha256:hash,source_sha:'a'.repeat(40),receipt:'testdata/original-ui/receipt.json',receipt_sha256:hash},selected_ui:{version:'1.0.1',archive_sha256:'b'.repeat(64)}};
validate(schema('ui-adoption'),ui);validateUiAdoptionEvidence(ui);
const stagedResult={...result,ui_adoption:ui,checks:[{name:'ui-adoption',status:'pass',reason:'ui-staged-pending',duration_ms:1}]};validate(schema('result'),stagedResult);assertGateResult(stagedResult);
for(const patch of [{mode:'active'},{until:'S1-M3'},{source:'lint/scope.json'},{config_sha256:'tag'},{extra:true},{legacy:{...ui.legacy,version:'0.3.1'}},{legacy:{...ui.legacy,receipt:'../receipt.json'}},{legacy:{...ui.legacy,receipt:'.gate/unit/result.json'}},{legacy:{...ui.legacy,receipt:'frontend/dist/receipt.json'}},{selected_ui:{...ui.selected_ui,alternate_tag:'core-v1.0'}}])assert.throws(()=>validate(schema('ui-adoption'),{...ui,...patch}));
assert.throws(()=>validateUiAdoptionEvidence({...ui,selected_ui:{...ui.selected_ui,version:'0.3.0'}}));
assert.throws(()=>assertGateResult({...result,ui_adoption:ui}));
assertGateResult({...stagedResult,legacy_pending:[pending],checks:[{name:'versions-check',status:'pass',reason:'legacy-pending;ui-staged-pending',duration_ms:1}]});
for(const key of ['constructor','toString','__proto__']){const bad=JSON.parse(JSON.stringify(result).slice(0,-1)+`,"${key}":{}}`);assert.throws(()=>validate(schema('result'),bad));}
for(const patch of [{started:'Z'},{started:'2026-02-31T00:00:00.000Z'},{finished:'2026-10-05T00:00:00.000Z'},{csp:{stage:'report-only',violations:1,legacy_violations:0}},{checks:[{name:'failed',status:'fail',duration_ms:0}]},{target:'full',checks:[{name:'pg-live',status:'skipped',reason:'no-dsn',duration_ms:0}]},{checks:[{name:'unknown',status:'skipped',reason:'not-needed',duration_ms:0}]},{budgets:{css:{limit:null,actual:25,status:'pass'}}},{budgets:{js:{limit:10,actual:25,status:'pass'}}},{budgets:{js:{limit:10,actual:25,status:'recorded'}}}])assert.throws(()=>assertGateResult({...result,...patch}));
console.log('schemas: actual committed budgets and positive/negative result, kit-lock and lint-scope instances validated');

const seedBytes=readFileSync('web-kit/budget/testdata/budgets.seed.json');assert.ok(seedBytes.equals(readFileSync('budgets.json')),'shared Go/Node schema seed must be exact committed budgets');
const matrix=JSON.parse(readFileSync('web-kit/budget/testdata/schema-cases.json'));
const rows=Array.isArray(matrix)?matrix:matrix.cases;assert.ok(rows.length>0);
for(const row of rows){const value=JSON.parse(seedBytes);let owner=value;for(const key of row.pointer.slice(0,-1))owner=owner[key];const key=row.pointer.at(-1);if(row.drop)delete owner[key];else owner[key]=row.value;let accepted=true;try{validate(schema('budgets'),value);}catch{accepted=false;}assert.equal(accepted,row.valid,`shared schema case ${row.name}`);}
console.log(`schemas: shared Go/Node budget matrix ${rows.length} actual cases validated`);
