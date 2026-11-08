#!/usr/bin/env python3
"""Build allowlisted blind tasks and compare only after a response is retained."""
import sys
sys.dont_write_bytecode=True
from pathlib import Path
import secrets
import subprocess
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *

EXCLUDED_SERVING_EMBED='go-backend/internal/content/bundled.json'
GO_LIST_FILE_FIELDS=('GoFiles','CgoFiles','CFiles','CXXFiles','MFiles','HFiles','FFiles','SFiles','SysoFiles','EmbedFiles')


def candidate_rows(value,hint=None):
    if isinstance(value,dict):
        if value.get('game') in GAMES and isinstance(value.get('payload'),dict):
            yield value;return
        if hint in GAMES and 'id' in value and 'difficulty' in value:
            yield {**value,'game':hint,'payload':value.get('payload',value)};return
        for k,v in value.items():
            yield from candidate_rows(v,k if k in GAMES else hint)
    elif isinstance(value,list):
        for v in value:yield from candidate_rows(v,hint)


def read_input(path,repo):
    p=repo_or_scratch(path,repo)
    data=read_regular(p)
    return p,strict_json(data),data


def compact(value):
    return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode()


def exact_keys(value,*keys):
    return isinstance(value,dict) and set(value)==set(keys)


def binding_matches(binding,path,data):
    return (exact_keys(binding,'path','sha256','bytes') and binding['path']==path and
            type(binding['bytes']) is int and binding['bytes']==len(data) and
            isinstance(binding['sha256'],str) and re.fullmatch(r'[0-9a-f]{64}',binding['sha256']) is not None and
            binding['sha256']==hashlib.sha256(data).hexdigest())


def producer_input(binding,repo,name):
    if not isinstance(binding,dict) or not isinstance(binding.get('path'),str):
        fail('invalid native caption producer path: '+name)
    path=repo_or_scratch(binding['path'],repo)
    data=read_regular(path)
    if not binding_matches(binding,str(path),data):
        fail('stale or mismatched native caption input: '+name)
    return data


def json_stream(data):
    decoder=json.JSONDecoder();offset=0
    while True:
        while offset<len(data) and data[offset].isspace():offset+=1
        if offset==len(data):return
        try:value,offset=decoder.raw_decode(data,offset)
        except json.JSONDecodeError as exc:fail('cannot decode Go producer closure: '+str(exc))
        yield value


def native_source_paths(repo,go_tool,scratch_root):
    if not go_tool or not Path(go_tool).is_absolute():
        fail('native caption verification requires --go-tool with the absolute pinned Go path')
    go=Path(go_tool).resolve(strict=True)
    if not go.is_file():
        fail('--go-tool must identify the pinned Go executable')
    module=repo.root/'go-backend'
    env={k:v for k,v in os.environ.items() if k not in {'GONOSUMDB','GOPRIVATE','GOEXPERIMENT'}}
    cache=scratch(scratch_root/'go-list-cache')
    if in_git_checkout(cache):
        fail('Go listing cache must be outside Git checkouts')
    env.update(GOENV='off',GOFLAGS='',GOPROXY='off',GOSUMDB='off',GOTOOLCHAIN='local',GOWORK='off',
               GOCACHE=str(cache))
    try:
        version=subprocess.run([str(go),'version'],stdin=subprocess.DEVNULL,capture_output=True,check=True,env=env,timeout=60)
        if not version.stdout.startswith(b'go version go1.27.3 '):
            fail('native caption Go version differs')
        result=subprocess.run([str(go),'list','-deps','-json','-mod=readonly','-buildvcs=false','./cmd/cat-content'],
                              cwd=module,stdin=subprocess.DEVNULL,capture_output=True,check=True,env=env,timeout=60)
    except subprocess.SubprocessError as exc:
        fail(f'cannot enumerate native caption producer closure: {exc}')
    paths={repo.root/'go-backend/go.mod',repo.root/'go-backend/go.sum'}
    for package in json_stream(result.stdout.decode()):
        module_info=package.get('Module') or {}
        if module_info.get('Main') is not True:continue
        directory=Path(package['Dir']).resolve()
        try:directory.relative_to(module)
        except ValueError:fail('local producer package escaped main module: '+str(directory))
        for field in GO_LIST_FILE_FIELDS:
            for name in package.get(field) or []:
                path=directory/name
                rel=path.relative_to(repo.root).as_posix()
                if rel!=EXCLUDED_SERVING_EMBED:paths.add(path)
    return sorted(p.relative_to(repo.root).as_posix() for p in paths)


def native_caption_artifact(path,pinned_sha,repo,board,go_tool,scratch_root):
    if not isinstance(pinned_sha,str) or re.fullmatch(r'[0-9a-f]{64}',pinned_sha) is None:
        fail('Lanț requires an exact lowercase --lant-caption-sha256 pin')
    artifact_path=scratch(path)
    artifact_data=read_regular(artifact_path)
    if sha256(artifact_data)!=pinned_sha:
        fail('native caption artifact hash changed')
    artifact=json_object(artifact_data)
    if not exact_keys(artifact,'schema','purpose','game','qualification','inputs','counts','captions'):
        fail('native caption artifact schema keys differ')
    expected_qualification='Native derivation and validation only; no content, source, ranking, rail, installation or serving approval.'
    if artifact['schema']!='cat-prospective-lant-captions-1' or artifact['purpose']!='unapproved_native_preview_only' or artifact['game']!='lant' or artifact['qualification']!=expected_qualification:
        fail('wrong native caption artifact identity or game')
    inputs=artifact['inputs']
    if not exact_keys(inputs,'kg','pack','rubric','rules_unicode15','rules_provenance','native_sources','go_version'):
        fail('native caption input schema differs')
    graph=Graph(repo,json_object(producer_input(inputs['kg'],repo,'kg')))
    pack=json_object(producer_input(inputs['pack'],repo,'pack'))
    matches=[row for row in pack['lant'] if row['id']==board['id']]
    if len(matches)!=1 or any(matches[0].get(k)!=board['payload'].get(k) for k in ('start','target','optimal')):
        fail('native caption pack does not bind this Lanț board')
    expected={
        'rubric':('docs/CRITIQUE_RUBRIC.md',repo.read('docs/CRITIQUE_RUBRIC.md')),
        'rules_unicode15':('go-backend/internal/contentbuild/rules_unicode15.json',repo.read('go-backend/internal/contentbuild/rules_unicode15.json')),
        'rules_provenance':('go-backend/internal/contentbuild/rules_provenance.json',repo.read('go-backend/internal/contentbuild/rules_provenance.json')),
    }
    for name,(bound_path,data) in expected.items():
        if not binding_matches(inputs[name],bound_path,data):fail('stale or mismatched native caption input: '+name)
    if inputs['go_version']!='go1.27.3':fail('native caption Go version differs')
    native_paths=native_source_paths(repo,go_tool,scratch_root)
    native=inputs['native_sources']
    if not isinstance(native,list) or len(native)!=len(native_paths):fail('native caption source inventory differs')
    for item,rel in zip(native,native_paths):
        data=repo.read(rel)
        if not binding_matches(item,rel,data):fail('stale or mismatched native caption source: '+rel)
    captions=artifact['captions']
    expected_edges={left+'\0'+right for left in graph.adj for right in graph.adj[left]}
    if not isinstance(captions,dict) or set(captions)!=expected_edges:
        fail('native caption coverage differs from exact prospective KG')
    if any(not isinstance(value,str) or not value.strip() or len(value)>200 for value in captions.values()):
        fail('native caption value missing or invalid')
    counts=artifact['counts']
    if not exact_keys(counts,'directed_edges') or type(counts['directed_edges']) is not int or counts['directed_edges']!=len(captions):
        fail('native caption count binding differs')
    return graph,captions,{'path':str(artifact_path),'sha256':pinned_sha,'schema':artifact['schema'],'game':'lant','inputs':inputs}


def audit_recipes(path,pinned_sha,dossier,tool,tool_sha,board,repo):
    audit_path=scratch(path)
    audit_data=read_regular(audit_path)
    if sha256(audit_data)!=pinned_sha:
        fail('native Alchimie audit hash changed')
    audit=json_object(audit_data)
    if (audit.get('schema'),audit.get('game'),audit.get('mode'),audit.get('status'))!=(
        'alchimie-live-projection-audit-v1','alchimie','gate','pending'
    ):
        fail('Alchimie requires the pending native projection audit')
    ids=audit['input_ids']
    if (not isinstance(ids,list) or not ids or
        any(not isinstance(value,str) or not re.fullmatch(r'[a-z0-9_-]+',value) for value in ids) or
        ids!=sorted(set(ids)) or board['id'] not in ids
    ):
        fail('native Alchimie audit requires an exact sorted item inventory')
    tool=Path(tool).expanduser()
    dossier=scratch(dossier)
    if not tool.is_absolute() or not tool.is_file() or not dossier.is_dir():
        fail('Alchimie requires an absolute pinned cat-content-ops executable and a scratch dossier directory')
    tool=tool.resolve(strict=True)
    if digest_file(tool)!=tool_sha:
        fail('pinned cat-content-ops executable hash changed')
    for item_id in ids:
        read_regular(beneath(dossier/(item_id+'.json'),dossier))
    # The native read-only replay checks the full item schema and bounds, current
    # runtime sources and extensions, raw record bytes, and fresh dossier bindings.
    try:
        replay=subprocess.run(
            [str(tool),'audit-projections','--root',str(repo.root),'--check','--ids',','.join(ids),'--dossier',str(dossier)],
            cwd=dossier,stdin=subprocess.DEVNULL,capture_output=True,check=True,timeout=180,
        )
    except subprocess.CalledProcessError as exc:
        fail('native Alchimie audit replay failed: '+exc.stderr[:1000].decode('utf-8',errors='replace').strip())
    except subprocess.TimeoutExpired:
        fail('native Alchimie audit replay timed out')
    if compact(json_object(replay.stdout))!=compact(audit):
        fail('native Alchimie audit differs from replay')
    for field,rel in [('kg_sha256',FIX+'kg_sample.json'),('pack_sha256',FIX+'games_pack.json'),('rubric_sha256','docs/CRITIQUE_RUBRIC.md')]:
        data=repo.read(rel)
        if field!='pack_sha256':
            data=data.replace(b'\r\n',b'\n').replace(b'\r',b'\n')
        if audit[field]!=sha256(data):
            fail('stale Alchimie audit '+field)
    matches=[row for row in audit['items'] if row['id']==board['id']]
    if len(matches)!=1 or compact(matches[0]['source_record'])!=compact(board['payload']):
        fail('native Alchimie audit does not bind the selected source record')
    item=matches[0]
    merged=collections.defaultdict(set)
    for route in item['routes']:
        for step in route:merged[tuple(sorted(step['pair']))].update(step['results'])
    recipes=[{'pair':list(pair),'results':sorted(values)} for pair,values in sorted(merged.items())]
    structural={'par':item['projection_par'],'recipes':recipes,'routes':item['routes']}
    if hashlib.sha256(compact(structural)).hexdigest()!=item['projection_sha256']:fail('cannot reconstruct the audit recipe projection exactly; obtain explicit native projection before critic')
    return recipes,item['projection_par'],{'path':str(audit_path),'sha256':sha256(audit_data),'projection_sha256':item['projection_sha256'],'native_tool_sha256':tool_sha}


def build(a):
    repo=Repo(a.root)
    path,raw,input_data=read_input(a.input,repo)
    rows=list(candidate_rows(raw,a.game))
    if a.item_id:rows=[r for r in rows if r['id']==a.item_id]
    if len(rows)!=1:fail('select exactly one candidate using --item-id and, for a raw pack row, --game')
    board=rows[0];game=board['game'];payload=board['payload']
    caption_options=(a.lant_caption_artifact,a.lant_caption_sha256,a.go_tool)
    if any(caption_options) and (game!='lant' or not all(caption_options)):
        fail('native caption options are required together and only for Lanț')
    audit_options=(a.audit,a.audit_sha256,a.audit_dossier_dir,a.audit_tool,a.audit_tool_sha256)
    if game=='alchimie' and not all(audit_options):
        fail('Alchimie requires --audit, --audit-sha256, --audit-dossier-dir, --audit-tool and --audit-tool-sha256')
    if game!='alchimie' and any(audit_options):
        fail('native projection audit options are only for Alchimie')
    public_path=output_path(a.public_out);key_path=output_path(a.key_out)
    if public_path==key_path:fail('public and private outputs must differ')
    source_hash=sha256(input_data)
    challenge_id=hashlib.sha256(compact([source_hash,board['id'],a.seed if a.seed is not None else secrets.token_hex(32)])).hexdigest()[:24]
    graph=None if a.lant_caption_artifact else Graph(repo)
    ids=set();private={};extra={};human=[]
    if game=='conexiuni':
        groups=list(payload['groups'].values())
        if len(groups)!=4 or any(len(x)!=4 for x in groups) or len(set(x for group in groups for x in group))!=16:fail('Conexiuni needs 16 distinct tiles in four quads')
        ids={x for group in groups for x in group}
        task='Partition the 16 shuffled tiles into four groups of four. Give one natural predicate and an each-tile explanation per group; report any alternative valid partition and recognizable_groups 0..4.'
        human=['Predicate truth and naturalness','Each-tile explanation for every group','No second valid partition','At least three recognizable groups']
    elif game=='intrusul':
        if len(payload['members'])!=3 or len(set(payload['members']+[payload['intruder']]))!=4:fail('Intrusul needs four distinct tiles')
        ids=set(payload['members']+[payload['intruder']])
        task='Pick the single odd tile and name the natural predicate shared by the other three. Report alternate_predicates if any other tile could naturally be odd.'
        human=['Predicate is true of all three members and false of odd tile','No natural alternate odd tile; synonym predicates require judgment']
    elif game=='perechi':
        pairs=[pair['members'] for pair in payload['pairs']]
        if len(pairs)!=4 or any(len(x)!=2 for x in pairs) or len(set(x for pair in pairs for x in pair))!=8:fail('Perechi needs eight distinct tiles in four pairs')
        ids={x for pair in pairs for x in pair}
        task='Match the eight shuffled tiles into four pairs. Explain the relation of each pair, and report any alternate natural matching or ambiguous tile.'
        human=['Natural pair explanations','No competing semantic matching or ambiguous tile']
    elif game=='lant':
        par=payload.get('optimal')
        if type(par) is not int or not 1<=par<=12:fail('Lanț requires integer optimal 1..12')
        if a.lant_caption_artifact:
            graph,captions,caption_binding=native_caption_artifact(
                a.lant_caption_artifact,a.lant_caption_sha256,repo,board,a.go_tool,scratch(a.scratch_root))
        else:
            # Existing-board replay uses the installed caption authority for this exact graph.
            bundle=repo.data('go-backend/internal/content/bundled.json')
            pack=repo.data(FIX+'games_pack.json')
            if bundle['sources']['kg_sample.json']!=sha256(repo.read(FIX+'kg_sample.json')) or not any(
                row['id']==board['id'] and all(row.get(k)==payload.get(k) for k in ('start','target','optimal'))
                for row in pack['lant']
            ) or bundle['sources']['games_pack.json']!=sha256(repo.read(FIX+'games_pack.json')):
                fail('a prospective Lanț board requires a pinned native caption artifact')
            captions=bundle['lant_captions']
            caption_binding={'schema':'installed_bundle_replay'}
        distances=graph.bfs(payload['start'],depth=par+2)
        if len(distances)>a.max_graph_nodes:fail('Lanț public choice graph exceeds --max-graph-nodes; do not silently truncate')
        ids=set(distances)|{payload['target']}
        links=[]
        for left in sorted(ids):
            for right in sorted(graph.adj[left]):
                if right not in ids:continue
                caption=captions.get(left+'\0'+right)
                if not caption:fail('missing bundled caption on public Lanț edge')
                links.append((left,right,caption))
        private={'allowed_edges':[[x,y] for x,y,c in links],'par':par,'native_caption_artifact_binding':caption_binding}
        task='Play from start to target using only the listed choices and their captions. Return the complete path including endpoints and one explanation per move. Reach target within par+2 moves; report any unclear caption.'
        human=['Every step is explainable from its caption','Caption visibility/semantics reflect the HTTP game; offline choice graph is not an HTTP playthrough']
    elif game=='contexto':
        if not a.raw_cald_diagnostic:fail('Cald gameplay requires the ADR-0213 cap-eight protocol; use --raw-cald-diagnostic only for a local opener probe')
        task='Choose exactly five ordinary Romanian opening guesses before seeing the hidden target or any distances. Return openers as five text strings; the target and graph feedback remain sealed.'
        distances=graph.bfs(payload['target'],reverse=True)
        bundle=repo.data('go-backend/internal/content/bundled.json')
        lookup=bundle.get('normalized_index',{})
        private={'target':payload['target'],'raw_reverse_distances':distances,'normalized_index':lookup,'normalization_map':bundle['normalization_map'],'accent_normalization_map':bundle['accent_normalization_map']}
        human=['One dominant target sense','Native Cald distances/responsive feedback required; raw graph opener probe is only a proxy']
    elif game=='alchimie':
        recipes,par,audit_binding=audit_recipes(*audit_options,board,repo)
        ids=set(payload['seeds'])|{payload['target']}
        for recipe in recipes:ids.update(recipe['pair']);ids.update(recipe['results'])
        private={'recipes':recipes,'par':par,'audit_binding':audit_binding}
        task='Craft the target from the seeds using the audited available pair results. Return action pairs in order and explain each step. Report free pairs or an uninferable target; do not use the hidden witness route.'
        human=['Target inferable from seeds/openings','Each pair result fair, no free pair','Native audit authority and exact source/dossier bindings verified in frozen bundle']
    else:fail('unsupported game')
    if any(x not in graph.nodes for x in ids):fail('unknown node in challenge')
    ordered=sorted(ids,key=lambda x:hashlib.sha256((challenge_id+'\0'+x).encode()).hexdigest())
    token={id_:'t'+str(i+1).zfill(4) for i,id_ in enumerate(ordered)}
    expected={}
    public={'schema':'cat-v2-blind-task-1','challenge_id':challenge_id,'game':game,'task':task}
    if ids:public['tiles']=[{'tile':token[id_],'text':graph.nodes[id_]['label_ro']} for id_ in ordered]
    if game=='conexiuni':
        expected={'groups':partitions([token[x] for x in group] for group in groups),'predicates':payload.get('group_labels',{})}
        public['response_schema']={'groups':[['tile x4']]*4,'predicates':['text x4'],'tile_explanations':{'tile':'each tile ...'},'recognizable_groups':'0..4','alternative_partition':None,'ambiguous':False}
    elif game=='intrusul':
        expected={'odd':token[payload['intruder']],'predicate':payload.get('group_label')}
        public['response_schema']={'odd':'tile','predicate':'text','alternate_predicates':[],'ambiguous':False}
    elif game=='perechi':
        expected={'pairs':partitions([token[x] for x in pair] for pair in pairs),'predicates':[pair.get('group_label') for pair in payload['pairs']]}
        public['response_schema']={'pairs':[['tile','tile']]*4,'explanations':['text x4'],'alternate_matching':None,'ambiguous':False}
    elif game=='lant':
        public.update(start=token[payload['start']],target=token[payload['target']],par=par)
        public['choices']=sorted(({'from':token[x],'to':token[y],'caption':c} for x,y,c in links),
                                 key=lambda row:(row['from'],row['to']))
        private['allowed_edges']=[[token[x],token[y]] for x,y in private['allowed_edges']]
        expected={'start':token[payload['start']],'target':token[payload['target']],'max_moves':par+2}
        public['response_schema']={'path':['start tile','...','target tile'],'explanations':['one per move'],'ambiguous':False}
    elif game=='contexto':
        expected={'openers_count':5,'raw_within_two_hops_required':1}
        public['response_schema']={'openers':['Romanian word x5'],'ambiguous':False}
    elif game=='alchimie':
        public.update(seeds=[token[x] for x in payload['seeds']],target=token[payload['target']],par=par)
        # Complete recipe rules, in a hash order, expose no author solution route or labels.
        rules=[{'pair':sorted(token[x] for x in recipe['pair']),'results':sorted(token[x] for x in recipe['results'])} for recipe in recipes]
        public['available_pair_results']=sorted(rules,key=lambda r:hashlib.sha256(compact(r)).hexdigest())
        private['recipes']=rules
        expected={'seeds':public['seeds'],'target':public['target'],'max_actions':par}
        public['response_schema']={'actions':[['tile','tile']],'explanations':['one per action'],'free_pairs':[],'target_inferable':True,'ambiguous':False}
    public_sha=hashlib.sha256(json_bytes(public)).hexdigest()
    key={'schema':'cat-v2-blind-key-1','challenge_id':challenge_id,'game':game,'input_binding':{'path':str(path),'sha256':source_hash,'id':board['id']},
         'public_binding':{'path':str(public_path),'sha256':public_sha},'expected_answer':expected,'private_context':private,
         'tile_map':{v:k for k,v in token.items()},'human_checks':human,**repo.provenance()}
    key_data=json_bytes(key)
    write_json(public_path,public)
    try:
        write_bytes(key_path,key_data)
    except (OSError, ValueError):
        public_path.unlink(missing_ok=True)
        raise
    print(json.dumps({'public_out':str(public_path),'key_out':str(key_path),'challenge_id':challenge_id,'public_sha256':public_sha,'instruction':'Give the critic ONLY public_out. Seal the key until its response is retained.'},sort_keys=True))


def compare(a):
    key_path=scratch(a.key);response_path=scratch(a.response)
    if key_path==response_path:fail('response cannot be the private key')
    key_data=read_regular(key_path);response_data=read_regular(response_path)
    key=json_object(key_data);r=json_object(response_data)
    if key.get('schema')!='cat-v2-blind-key-1':fail('wrong private key schema')
    pb=key['public_binding']
    if digest_file(scratch(pb['path']))!=pb['sha256']:fail('public task missing or hash changed')
    if r.get('challenge_id')!=key['challenge_id']:fail('response must bind the challenge_id')
    e=key['expected_answer'];game=key['game'];private=key['private_context'];details={};issues=[]
    match=False
    try:
        if game=='conexiuni':
            answer=r.get('groups',[])
            shape=len(answer)==4 and all(isinstance(x,list) and len(x)==4 for x in answer) and len(set(x for group in answer for x in group))==16
            match=shape and partitions(answer)==e['groups']
            details={'partition_exact_match':match,'recognizable_groups':r.get('recognizable_groups'),'predicate_count':len(r.get('predicates',[]))}
            if not isinstance(r.get('recognizable_groups'),int) or not 3<=r['recognizable_groups']<=4:issues.append('fewer than three recognizable groups or missing rating')
            if r.get('alternative_partition'):issues.append('critic reported an alternative partition')
            if len(r.get('predicates',[]))!=4:issues.append('four predicate explanations required')
            explanations=r.get('tile_explanations',{})
            if not isinstance(explanations,dict) or set(explanations)!=set(x for group in e['groups'] for x in group) or not all(isinstance(v,str) and v.strip() for v in explanations.values()):issues.append('one each-tile explanation per tile required')
        elif game=='intrusul':
            match=r.get('odd')==e['odd']
            predicate=r.get('predicate')
            details={'odd_exact_match':match,'predicate_present':isinstance(predicate,str) and bool(predicate.strip()),'predicate_exact_key_match':norm(predicate)==norm(e['predicate']) if isinstance(predicate,str) and isinstance(e.get('predicate'),str) else None}
            if not details['predicate_present']:issues.append('predicate missing')
            if r.get('alternate_predicates'):issues.append('critic reported alternate odd predicates')
        elif game=='perechi':
            answer=r.get('pairs',[])
            shape=len(answer)==4 and all(isinstance(x,list) and len(x)==2 for x in answer) and len(set(x for pair in answer for x in pair))==8
            match=shape and partitions(answer)==e['pairs']
            details={'matching_exact_match':match,'explanation_count':len(r.get('explanations',[]))}
            if r.get('alternate_matching'):issues.append('critic reported alternate matching')
            if len(r.get('explanations',[]))!=4:issues.append('four pair explanations required')
        elif game=='lant':
            path=r.get('path',[]);allowed={tuple(pair) for pair in private['allowed_edges']}
            legal=isinstance(path,list) and len(path)>=2 and all((x,y) in allowed for x,y in zip(path,path[1:]))
            match=legal and path[0]==e['start'] and path[-1]==e['target'] and len(path)-1<=e['max_moves']
            details={'legal_edges':legal,'moves':len(path)-1,'within_par_plus_two':len(path)-1<=e['max_moves'],'explanation_count':len(r.get('explanations',[]))}
            if len(r.get('explanations',[]))!=len(path)-1:issues.append('one explanation per move required')
        elif game=='contexto':
            openers=r.get('openers',[])
            if not isinstance(openers,list) or len(openers)!=5 or not all(isinstance(x,str) for x in openers):fail('Cald response requires exactly five string openers')
            probes=[]
            for text in openers:
                # Preserve reviewed accented unresolved forms before accent-fold lookup.
                spelling=native_transform(text,private['accent_normalization_map']).replace('\u0327','\u0326')
                id_=None if spelling in ('pas\u0326te','pas\u0326tele') else private['normalized_index'].get(native_transform(text,private['normalization_map']))
                d=private['raw_reverse_distances'].get(id_)
                probes.append({'text':text,'exact_node':id_,'raw_hops':d})
            proxy=len({native_transform(x,private['normalization_map']) for x in openers})==5 and any(p['raw_hops'] is not None and p['raw_hops']<=2 for p in probes)
            match=None
            details={'raw_graph_opener_probe_pass':proxy,'probes':probes,'native_cald_feedback_verified':False}
            if not proxy:issues.append('raw graph proxy found no distinct five-opener set with one within two hops')
        elif game=='alchimie':
            actions=r.get('actions',[]);owned=set(e['seeds']);recipes={tuple(sorted(x['pair'])):set(x['results']) for x in private['recipes']};legal=True
            for pair in actions:
                if not isinstance(pair,list) or len(pair)!=2 or pair[0]==pair[1] or not set(pair)<=owned:legal=False;break
                outputs=recipes.get(tuple(sorted(pair)),set())
                if not outputs-owned:legal=False;break
                owned.update(outputs)
            match=legal and e['target'] in owned and len(actions)<=e['max_actions']
            details={'legal_productive_actions':legal,'target_reached':e['target'] in owned,'actions':len(actions),'within_exact_par':len(actions)<=e['max_actions']}
            if len(r.get('explanations',[]))!=len(actions):issues.append('one explanation per action required')
            if r.get('free_pairs') or r.get('target_inferable') is not True:issues.append('free pair or uninferable target reported')
        if r.get('ambiguous') is not False:issues.append('critic ambiguity flag missing or true')
    except (TypeError,IndexError) as exc:
        match=False;issues.append('malformed answer structure: '+str(exc))
    result={'schema':'cat-v2-blind-comparison-1','challenge_id':key['challenge_id'],'game':game,'mechanical_match':match,
            'details':details,'issues':issues,'human_checks_required':key['human_checks'],'approval':None,
            'status':'needs_human_semantic_checks' if match is not False and not issues else 'critic_filter_failure',
            'key_sha256':sha256(key_data),'response_binding':{'path':str(response_path),'sha256':sha256(response_data)},
            'public_binding':pb,'expected_answer_revealed_after_response':e,
            'limitation':'Mechanical answer comparison never certifies semantic fairness, evidence quality, critic independence, native runtime parity, signing or M6/M7 review.'}
    if game=='contexto':result['status']='raw_cald_diagnostic_only'
    write_json(a.out,result)
    print(json.dumps({'out':str(scratch(a.out)),'mechanical_match':match,'issues':len(issues),'status':result['status']},sort_keys=True))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    sub=p.add_subparsers(dest='command',required=True)
    b=sub.add_parser('build');b.add_argument('--root',required=True);b.add_argument('--input',required=True)
    add_scratch_argument(b)
    b.add_argument('--item-id');b.add_argument('--game',choices=GAMES);b.add_argument('--seed',help='explicit replay seed for tool tests')
    b.add_argument('--max-graph-nodes',type=int,default=4096)
    b.add_argument('--audit');b.add_argument('--audit-sha256')
    b.add_argument('--audit-dossier-dir');b.add_argument('--audit-tool',help='absolute pinned cat-content-ops executable')
    b.add_argument('--audit-tool-sha256')
    b.add_argument('--lant-caption-artifact');b.add_argument('--lant-caption-sha256');b.add_argument('--go-tool')
    b.add_argument('--raw-cald-diagnostic',action='store_true',help='allow the legacy raw opener diagnostic only')
    b.add_argument('--public-out',required=True);b.add_argument('--key-out',required=True)
    c=sub.add_parser('compare');c.add_argument('--key',required=True);c.add_argument('--response',required=True);c.add_argument('--out',required=True)
    add_scratch_argument(c)
    a=p.parse_args()
    set_scratch_root(a.scratch_root)
    if a.command=='build':
        if not 16<=a.max_graph_nodes<=4096:fail('max-graph-nodes must be 16..4096')
        build(a)
    else:compare(a)

if __name__=='__main__':run(main)
