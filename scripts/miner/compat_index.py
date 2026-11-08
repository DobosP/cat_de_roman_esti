#!/usr/bin/env python3
"""Static, citation-bearing exclusion/owner/signature index. Executes no source."""
import sys
sys.dont_write_bytecode = True
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import ast
import re
from common import *

MARKER = re.compile(r'(BLOCKED|COLLISION|DEFERRED|FUZZY.*DENY|UNRESOLVED|EXCLUD|REJECT|HOLD)', re.I)
SYMBOL = re.compile(r'^(?:[A-Z_0-9]+)$')


class Unknown(ValueError):
    pass


class Literals:
    """Only literals, containers, local constant references and literal concatenation.

    Imported constants are inspected via AST from scripts/*.py, never imported.
    Calls/comprehensions/attributes remain unknown except literal container wrappers.
    """
    def __init__(self, repo):
        self.repo, self.modules, self.active = repo, {}, set()

    def module(self, rel):
        if rel not in self.modules:
            tree = ast.parse(self.repo.text(rel), filename=rel)
            assigns, imports = {}, {}
            for n in tree.body:
                if isinstance(n, (ast.Assign, ast.AnnAssign)):
                    targets = n.targets if isinstance(n, ast.Assign) else [n.target]
                    for t in targets:
                        if isinstance(t, ast.Name) and n.value is not None:
                            assigns[t.id] = n
                elif isinstance(n, ast.ImportFrom) and n.module and n.level==0:
                    candidate = 'scripts/'+n.module.replace('.', '/')+'.py'
                    if (self.repo.root/candidate).is_file():
                        for alias in n.names:
                            imports[alias.asname or alias.name] = (candidate, alias.name)
            self.modules[rel] = (tree, assigns, imports)
        return self.modules[rel]

    def symbol(self, rel, name):
        key = (rel, name)
        if key in self.active:
            raise Unknown('cyclic constant reference')
        self.active.add(key)
        try:
            _, assignments, imports = self.module(rel)
            if name in assignments:
                n = assignments[name]
                return self.value(rel, n.value), [f'{rel}:{n.lineno}']
            if name in imports:
                dep, original = imports[name]
                value, refs = self.symbol(dep, original)
                return value, [f'{rel}:{next(n.lineno for n in self.module(rel)[0].body if isinstance(n, ast.ImportFrom) and any((a.asname or a.name)==name for a in n.names))}'] + refs
            raise Unknown('unbound constant '+name)
        finally:
            self.active.remove(key)

    def value(self, rel, n):
        if isinstance(n, ast.Constant):
            return n.value
        if isinstance(n, ast.Name):
            return self.symbol(rel, n.id)[0]
        if isinstance(n, (ast.Tuple, ast.List, ast.Set)):
            result = []
            for e in n.elts:
                if isinstance(e, ast.Starred):
                    v = self.value(rel, e.value)
                    if not isinstance(v, (list, tuple, set, frozenset)):
                        raise Unknown('starred non-container')
                    result.extend(v)
                else:
                    result.append(self.value(rel, e))
            if isinstance(n, ast.Tuple):
                return tuple(result)
            if isinstance(n, ast.Set):
                return set(result)
            return result
        if isinstance(n, ast.Dict):
            result = {}
            for k,v in zip(n.keys,n.values):
                if k is None:
                    result.update(self.value(rel,v))
                else:
                    result[self.value(rel,k)] = self.value(rel,v)
            return result
        if isinstance(n, ast.BinOp) and isinstance(n.op, ast.Add):
            return self.value(rel,n.left) + self.value(rel,n.right)
        if isinstance(n, ast.UnaryOp) and isinstance(n.op, (ast.UAdd, ast.USub)) and isinstance(n.operand, ast.Constant) and isinstance(n.operand.value,(float,int)):
            return n.operand.value if isinstance(n.op,ast.UAdd) else -n.operand.value
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id in ('tuple','list','set','frozenset') and len(n.args)==1 and not n.keywords:
            v = self.value(rel,n.args[0])
            if not isinstance(v,(tuple,list,set,frozenset)):
                raise Unknown('nonliteral container wrapper')
            return tuple(v)  # No arbitrary calls, even builtins, are executed.
        raise Unknown('dynamic '+type(n).__name__)


def historical_fields(value, path=()):
    if isinstance(value,dict):
        for key, child in value.items():
            current = path+(str(key),)
            if MARKER.search(str(key)) and not str(key).endswith(('_count','_checked','_collisions')):
                yield current, child
            else:
                yield from historical_fields(child,current)
    elif isinstance(value,list):
        for i,child in enumerate(value):
            yield from historical_fields(child,path+(str(i),))



def native_transform(surface,mapping):
    transformed=''.join(mapping.get(c,c) for c in surface)
    # graph/service.go pySpace, independent of the host's Unicode database.
    return re.sub(r'[\x09-\x0d\x1c-\x20\x85\xa0\u1680\u2000-\u200a\u2028\u2029\u202f\u205f\u3000]+',' ',transformed).strip(' ')


def attention_records(raw,rel,repo=None):
    records=raw.get('records',raw.get('packages',raw.get('items',[]))) if isinstance(raw,dict) else raw
    if isinstance(records,dict):records=list(records.values())
    if not isinstance(records,list):return [],False
    result=[]
    form_fields=('planned_forms','held_forms','verified_forms','proposed_forms','qualified_forms','aliases','forms','excluded_forms','research_excluded_forms','already_resolved_forms','observed_forms_not_proposed')
    text_fields=('lemma','label_ro','label','original_lemma')
    for i,r in enumerate(records):
        if not isinstance(r,dict):continue
        id_=str(r.get('id',r.get('item_id',i)))
        ref=repo.cite(rel,json.dumps(id_,ensure_ascii=False)) if repo is not None else f'{rel}:1'
        attention={k:r[k] for k in ('id','state','status','kind','node_id','owner_id','lemma','label_ro','label','decision','next_action','reason','review_verdicts','reviewed_module_sha256') if k in r}
        attention.update(ref=ref,record_pointer='/records/'+str(i),recorded_state=r.get('state',r.get('status','UNKNOWN')))
        attention['forms']={k:r[k] for k in form_fields if k in r}
        attention['surfaces']=sorted(set(x for k in text_fields for x in strings(r.get(k,[]))) | set(x for k in form_fields for x in strings(r.get(k,[]))))
        attention['qualification']='Recorded pool/stock attention only; state does not prove installation, acceptance validity or a universal alias denial.'
        result.append(attention)
    return result,True


def main():
    p=argparse.ArgumentParser(description=__doc__)
    add_scratch_argument(p)
    p.add_argument('--root',required=True)
    p.add_argument('--out',required=True)
    p.add_argument('--stock',action='append',default=[],help='explicit retained current-stock JSON file/directory; static attention only, never imports modules')
    a=p.parse_args()
    set_scratch_root(a.scratch_root)
    repo=Repo(a.root)
    parser=Literals(repo)
    exclusions=[]
    collision_pairs=[]
    unresolved=[]
    examined=[]
    def add(kind, terms, rel, line, symbol=None):
        for term in sorted(set(strings(terms))):
            if term.strip():
                exclusions.append({'kind':kind,'surface':term,'key':norm(term),'ref':f'{rel}:{line}','symbol':symbol})
    source_paths=sorted((repo.root/'scripts').glob('*.py'))
    source_paths += [repo.root/'cat_de_roman_esti/wordgames/service.py']
    source_paths += sorted((repo.root/'tests').rglob('*.py'))
    for path in source_paths:
        rel=path.relative_to(repo.root).as_posix()
        text=repo.text(rel)
        if not MARKER.search(text):
            continue
        try:
            tree, assignments, imports=parser.module(rel)
        except SyntaxError as e:
            unresolved.append({'ref':f'{rel}:{e.lineno or 1}','reason':'AST parse failure','scope':'whole file','fail_closed':True})
            continue
        examined.append(rel)
        for name,n in sorted(assignments.items()):
            if not SYMBOL.fullmatch(name) or not MARKER.search(name):
                continue
            try:
                value,refs=parser.symbol(rel,name)
                # A structured test case can contain accepted controls beside rejects.
                # Keep it as manual context instead of turning every dict value into a deny.
                if rel.startswith('tests/') and isinstance(value,dict):
                    unresolved.append({'ref':f'{rel}:{n.lineno}','symbol':name,'reason':'structured exclusion test constant; distinguish rejected cases from accepted controls manually','fail_closed':True,'literal_surfaces':sorted(set(strings(value)))})
                    continue
                # Literal tuple/list contents are inspected; imported origins also bound.
                add(name,value,rel,n.lineno,name)
                if 'COLLISION' in name and isinstance(value,(tuple,list)):
                    for pair in value:
                        if isinstance(pair,(tuple,list)) and len(pair)==2 and all(isinstance(x,str) for x in pair):
                            collision_pairs.append({'left':pair[0],'right':pair[1],'left_key':norm(pair[0]),'right_key':norm(pair[1]),'ref':f'{rel}:{n.lineno}','symbol':name})
                for dep in refs:
                    if dep != f'{rel}:{n.lineno}':
                        exclusions.append({'kind':'constant_origin','surface':name,'key':None,'ref':dep,'symbol':name})
            except (Unknown,TypeError,ValueError) as e:
                unresolved.append({'ref':f'{rel}:{n.lineno}','symbol':name,'reason':str(e),'fail_closed':True,
                                   'literal_surfaces':sorted({x.value for x in ast.walk(n.value) if isinstance(x,ast.Constant) and isinstance(x.value,str)})})
        if rel.startswith('tests/'):
            # Assertion-local explicit resolve(None)/empty results are useful exclusions.
            for n in ast.walk(tree):
                if not isinstance(n,ast.Assert):
                    continue
                denied=[]
                for expression in ast.walk(n.test):
                    if isinstance(expression,ast.Compare):
                        operands=[expression.left]+expression.comparators
                        for left,op,right in zip(operands,expression.ops,operands[1:]):
                            if not isinstance(op,(ast.Is,ast.Eq)):continue
                            for candidate,empty in ((left,right),(right,left)):
                                if isinstance(candidate,ast.Call) and isinstance(empty,ast.Constant) and empty.value in (None,''):
                                    denied.append(candidate)
                    elif isinstance(expression,ast.UnaryOp) and isinstance(expression.op,ast.Not) and isinstance(expression.operand,ast.Call):
                        denied.append(expression.operand)
                for c in denied:
                    if not isinstance(c.func,ast.Attribute) or c.func.attr not in ('resolve','resolve_fuzzy','suggest'):continue
                    if c.args and isinstance(c.args[0],ast.Constant) and isinstance(c.args[0].value,str):
                        add('test_asserted_unresolved_'+c.func.attr,[c.args[0].value],rel,n.lineno,'assert')
                    elif c.args:
                        unresolved.append({'ref':f'{rel}:{n.lineno}','reason':'dynamic resolver exclusion assertion; inspect surrounding test/function and referenced constants','scope':'test assertion','fail_closed':True})
    history_paths=sorted({* (repo.root/'docs/reviews').rglob('graph-candidates.json'), * (repo.root/'docs/reviews').rglob('*graph-candidates.json')})
    history=[]
    for path in history_paths:
        rel=path.relative_to(repo.root).as_posix()
        raw=repo.data(rel)
        fields=[]
        for pointer,value in historical_fields(raw):
            key=pointer[-1]
            line=int(repo.cite(rel,json.dumps(key)).rsplit(':',1)[1])
            add('historical_'+key,value,rel,line,'/'+ '/'.join(pointer))
            fields.append('/'+'/'.join(pointer))
        history.append({'path':rel,'exclusion_fields':fields,'no_exclusion_field':not fields,
                        'note':'All fields inspected; natural-language limits are retained below for manual screen.'})
        if isinstance(raw,dict):
            for key in ('limits','notes','summary','candidate_summary'):
                if key in raw:
                    history[-1].setdefault('manual_context',{})[key]=raw[key]
    # Native finite denials: record their actual function bodies and string literals.
    native='go-backend/internal/graph/service.go'
    native_text=repo.text(native)
    for function in ('ReviewedUnresolved','ResolveFuzzy'):
        match=re.search(r'func \(g \*Service\) '+function+r'\([^\n]*\).*?\n}\n',native_text,re.S)
        if match is None:
            unresolved.append({'ref':f'{native}:1','reason':'native denial function not found: '+function,'fail_closed':True})
            continue
        body=match.group()
        start=native_text[:match.start()].count('\n')+1
        relevant=[line for line in body.splitlines() if ('key ==' in line or 'return key ==' in line)]
        terms=[]
        for line in relevant:
            for quoted in re.findall(r'"(?:[^"\\]|\\.)*"',line):
                try: terms.append(json.loads(quoted))
                except json.JSONDecodeError: pass
        add('native_'+function,terms,native,start,function)
    rows,held,quick_held=inventory(repo)
    kg=repo.data(FIX+'kg_sample.json')
    owners=collections.defaultdict(list)
    for n in kg['kg_nodes']:
        rel=FIX+'kg_sample.json'
        ref=repo.cite(rel,json.dumps(n['id']))
        for surface in sorted(set([n['label_ro']]+n.get('aliases',[]))):
            owners[norm(surface)].append({'surface':surface,'owner':n['id'],'label':n['label_ro'],'ref':ref})
    signatures=[]
    for r in rows:
        game=r['game']; rel=r['origin']; payload=r.get('payload',r)
        item={'game':game,'id':r['id'],'signature':signature(game,r),'ref':repo.cite(rel,json.dumps(r['id'])),'held_refs':r['held']}
        if game=='conexiuni':item['groups']=partitions(payload['groups'].values())
        if game=='perechi':item['tile_set']=sorted(x for pair in payload['pairs'] for x in pair['members'])
        if game=='contexto':item['target']=payload['target']
        if game=='lant':item.update(start=payload['start'],target=payload['target'])
        signatures.append(item)
    tombstones=[]
    for game,name in [('conexiuni','conexiuni_rejection_tombstones.json'),('lant','lant_rejection_tombstones.json')]:
        rel=FIX+name
        for id_,row in sorted(repo.data(rel)['items'].items()):
            tombstones.append({'game':game,'id':id_,'signature':signature(game,row),'payload':row,'ref':repo.cite(rel,json.dumps(id_))})
    # Exact current native lookup authorities, preserving raw accent surfaces and keys.
    bundle_rel='go-backend/internal/content/bundled.json'
    bundle=repo.data(bundle_rel)
    required_fields=('normalization_map','accent_normalization_map','normalized_index','labels','discovery_world','contexto_data')
    missing=[k for k in required_fields if not isinstance(bundle.get(k),dict)]
    mapping=bundle.get('normalization_map',{})
    accent_mapping=bundle.get('accent_normalization_map',{})
    native_index=bundle.get('normalized_index',{})
    native_attention=[]
    def native_surface(surface,owner,origin,ref):
        if not isinstance(surface,str):return
        key=native_transform(surface,mapping)
        accented=native_transform(surface,accent_mapping).replace('\u0327','\u0326')
        native_attention.append({'surface':surface,'native_key':key,'accent_preserved_key':accented,'native_exact_owner':native_index.get(key),'proposed_owner':owner,'origin':origin,'ref':ref})
    for n in kg['kg_nodes']:
        ref=repo.cite(FIX+'kg_sample.json',json.dumps(n['id']))
        for surface in [n['label_ro']]+n.get('aliases',[]):native_surface(surface,n['id'],'KG node label/alias',ref)
    for id_,label in sorted(bundle.get('labels',{}).items()):native_surface(label,id_,'bundled labels',repo.cite(bundle_rel,json.dumps(id_)))
    world_concepts=bundle.get('discovery_world',{}).get('concepts',[])
    projection_terms=bundle.get('contexto_data',{}).get('projection_terms',[])
    if not isinstance(world_concepts,list) or not isinstance(projection_terms,list):missing.append('world concepts / Cald projection_terms list')
    for concept in world_concepts:
        id_=concept.get('id');ref=repo.cite(bundle_rel,json.dumps(id_))
        for source in [concept,concept.get('snapshot',{})]:
            for field in ('label','label_ro','aliases'):
                for surface in strings(source.get(field,[])):native_surface(surface,id_,'discovery_world concept/snapshot',ref)
    for term in projection_terms:
        ref=repo.cite(bundle_rel,json.dumps(term.get('public_id','projection_terms')))
        for field in ('label','surface','key'):
            for surface in strings(term.get(field,[])):native_surface(surface,term.get('public_id'),'Cald projection term',ref)
    for entry in exclusions:
        if entry.get('key') is not None:
            entry['native_key']=native_transform(entry['surface'],mapping)
            entry['accent_preserved_key']=native_transform(entry['surface'],accent_mapping).replace('\u0327','\u0326')
    pool_records=[];pool_files=[];pool_holds=[]
    for path in sorted((repo.root/'docs/content-pool').glob('*/pool.json')):
        rel=path.relative_to(repo.root).as_posix();raw=repo.data(rel)
        records,ok=attention_records(raw,rel,repo)
        pool_files.append({'path':rel,'records':len(records),'record_states':dict(sorted(collections.Counter(r['recorded_state'] for r in records).items())),'parsed':ok})
        if not ok:missing.append('unrecognized final pool shape '+rel)
        for r in records:
            for surface in r['surfaces']:
                native_surface(surface,r.get('node_id',r.get('owner_id')), 'final pool state '+str(r['recorded_state']),r['ref'])
        pool_records.extend(records)
        for pointer,value in historical_fields(raw):
            if not pointer or pointer[0]=='records':continue
            pool_holds.append({'pointer':'/'+'/'.join(pointer),'value':value,'ref':repo.cite(rel,json.dumps(pointer[-1])),'classification':'pool hold/exclusion context; inspect fields before treating any surface as denied'})
    if not pool_files:missing.append('no final docs/content-pool/*/pool.json found')
    stock_records=[];external_bindings=[];stock_files=[]
    for requested in a.stock:
        path=repo_or_scratch(requested,repo)
        paths=sorted(path.rglob('*.json')) if path.is_dir() else [path]
        if len(paths)>256:fail('stock input exceeds 256 JSON files; select a current stock manifest')
        for stock in paths:
            if stock.suffix!='.json':fail('--stock accepts static JSON only, never Python source modules')
            stock=repo_or_scratch(stock,repo)
            data=read_regular(stock);raw=strict_json(data);rel=str(stock)
            records,ok=attention_records(raw,rel)
            stock_files.append({'path':rel,'records':len(records),'parsed':ok,'qualification':'Explicit protected/pending stock, not content installed on main.'})
            if not ok or not records:missing.append('unrecognized or empty explicit stock '+rel)
            stock_text=data.decode('utf-8')
            for r in records:
                marker=json.dumps(str(r.get('id','')),ensure_ascii=False)
                offset=stock_text.find(marker)
                line=stock_text[:offset].count('\n')+1 if offset>=0 else 1
                r['ref']=rel+':'+str(line);r['stock_binding']=rel
                for surface in r['surfaces']:native_surface(surface,r.get('node_id',r.get('owner_id')),'explicit pending stock '+str(r['recorded_state']),r['ref'])
            stock_records.extend(records)
            external_bindings.append({'path':rel,'sha256':sha256(data),'bytes':len(data)})
    authority={'ref':repo.cite(bundle_rel),'normalization_map':mapping,'accent_normalization_map':accent_mapping,
               'normalized_index':native_index,'labels':bundle.get('labels',{}),'discovery_world_concepts':world_concepts,'contexto_projection_terms':projection_terms,
               'qualification':'Actual bundled JSON authorities bound by source SHA. No authority-pin/freshness/runtime qualification is inferred.'}
    for problem in missing:unresolved.append({'ref':bundle_rel+':1','reason':problem,'fail_closed':True,'scope':'missing screening authority'})
    coverage={'required_main_fields_present':not missing,'final_pool_files':len(pool_files),'protected_pending_stock_supplied':bool(a.stock),
              'protected_stock_limit':'Main contains no unlanded stock payloads. Pass explicit --stock JSON inventories for each protected pending source relevant to the landing; absent input cannot be screened.',
              'native_fuzzy_probe_required':True,'semantic_and_dynamic_manual_screen_required':True}
    adr='docs/adr/0210-curation-waves-and-staged-stock-landing.md'
    rules=[{'owner_label':'Ie','excluded_keys':['ii','iei'],'ref':repo.cite(adr,'Ie never')},
           {'excluded_surface':'sucitoare','key':norm('sucitoare'),'ref':repo.cite(adr,'Bare `sucitoare`')},
           *({'owner_label':label,'key':norm(label),'hold':'explicit_owner_approval_required',
              'ref':repo.cite('docs/CONTENT_LOOP.md','Mănăstire')} for label in ('Mănăstire','Sucitor'))]
    out={'schema':'cat-v2-compat-index-1','complete_static_screen':False,
         'screen_policy':'Literal hits are holds. Unknown/dynamic expressions NEVER pass; resolve each relevant annotation with file:line evidence before M2 passes. This index is discovery, not a verdict.',
         'normalization':'Python NFKD, accent removal, casefold, whitespace collapse for lookup only; native Unicode15 resolver/fuzzy probes mandatory.',
         'exclusions':sorted(exclusions,key=lambda r:(r['ref'],r['kind'],r['surface'])),
         'unresolved':sorted(unresolved,key=lambda r:(r['ref'],r.get('symbol',''))),
         'native_authorities':authority,'native_surface_attention':native_attention,'coverage':coverage,
         'pool_files':pool_files,'pool_record_attention':pool_records,'pool_hold_context':pool_holds,
         'stock_files':stock_files,'stock_record_attention':stock_records,'external_bindings':external_bindings,
         'collision_pairs':sorted(collision_pairs,key=lambda r:(r['ref'],r['left'],r['right'])),
         'current_owners':dict(sorted(owners.items())),
         'owner_key_collisions':{k:v for k,v in sorted(owners.items()) if len({r['owner'] for r in v})>1},
         'owner_rulings':rules,'signatures':sorted(signatures,key=lambda r:(r['game'],r['id'])),
         'tombstones':tombstones,'holds':[{'id':k,'refs':v} for k,v in sorted(held.items())]+[{'id':k,'refs':[v]} for k,v in sorted(quick_held.items())],
         'historical_candidates':history,'examined_exclusion_sources':examined,**repo.provenance()}
    write_json(a.out,out)
    print(json.dumps({'out':str(scratch(a.out)),'exclusions':len(exclusions),'unknowns':len(unresolved),'owners':len(owners),'signatures':len(signatures),'tombstones':len(tombstones),'historical_files':len(history),'native_exact_keys':len(native_index),'world_concepts':len(world_concepts),'cald_projection_terms':len(projection_terms),'final_pool_records':len(pool_records),'stock_records':len(stock_records)},sort_keys=True))

if __name__=='__main__':run(main)
