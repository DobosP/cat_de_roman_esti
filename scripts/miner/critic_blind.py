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



# Native quick intake is deliberately separate from the historical six-game
# inspector. The trusted operator pins the executable AND reviewed build-input
# receipt, outside the author-controlled bundle. No hash here grants approval.
QUICK_QUALIFICATION='Unapproved private pending projection only; no semantic, source-policy, content, installation or serving approval.'
QUICK_MEMBER_LIMIT=32<<20
QUICK_EXTERNAL_LIMIT=64<<20
QUICK_TOOL_LIMIT=256<<20
QUICK_GAMES=('intrusul','perechi')


def quick_require(condition,message):
    if not condition:fail('native quick: '+message)


def quick_digest(value):
    return sha256(compact(value))


def quick_path(path):
    p=Path(path)
    quick_require(p.is_absolute() and str(p)==str(path) and '..' not in p.parts,'absolute canonical path required')
    quick_require(all(not part.is_symlink() for part in (p,*p.parents)),'symlink input refused')
    return p


def quick_read(path,limit=QUICK_MEMBER_LIMIT):
    p=quick_path(path)
    quick_require(p.stat().st_size<=limit,'input byte cap')
    data=read_regular(p)
    quick_require(len(data)<=limit,'input byte cap')
    return data


def quick_tool_hash(path):
    # Producer cap is separate; common's 64 MiB document cap remains unchanged.
    p=quick_path(path)
    flags=os.O_RDONLY|getattr(os,'O_NOFOLLOW',0)|getattr(os,'O_NONBLOCK',0)
    fd=os.open(p,flags)
    with os.fdopen(fd,'rb') as source:
        before=os.fstat(source.fileno())
        quick_require(stat.S_ISREG(before.st_mode) and 0<before.st_size<=QUICK_TOOL_LIMIT,'producer type/byte cap')
        h=hashlib.sha256();count=0
        while True:
            block=source.read(1<<20)
            if not block:break
            count+=len(block);quick_require(count<=QUICK_TOOL_LIMIT,'producer byte cap');h.update(block)
        after=os.fstat(source.fileno())
    quick_require(count==before.st_size and (before.st_mtime_ns,before.st_ctime_ns)==(after.st_mtime_ns,after.st_ctime_ns),'producer changed during read')
    return h.hexdigest(),count


def quick_pin(data,pin,name):
    quick_require(isinstance(pin,str) and re.fullmatch('[0-9a-f]{64}',pin) is not None and sha256(data)==pin,name+' hash differs')


def quick_bound_file(row,root=None,limit=QUICK_MEMBER_LIMIT):
    quick_require(exact_keys(row,'path','bytes','sha256') and isinstance(row['path'],str) and type(row['bytes']) is int,'file binding shape')
    if root is None:path=quick_path(row['path'])
    else:
        rel=Path(row['path'])
        quick_require(not rel.is_absolute() and '..' not in rel.parts and rel.as_posix()==row['path'],'relative file binding path')
        path=quick_path(str(root/rel))
    data=quick_read(path,limit)
    quick_require(row['bytes']==len(data),'file binding byte count')
    quick_pin(data,row['sha256'],'input '+row['path'])
    return data


def quick_build_proof(a,root,tool,inventory):
    data=quick_read(scratch(a.native_build_proof));quick_pin(data,a.native_build_proof_sha256,'build proof')
    proof=json_object(data)
    quick_require(exact_keys(proof,'schema','tool','go_version','compiled_rubric_sha256','compiled_authority_sha256','source_inputs','sdk_image','build_flags','target','inventory_sha256','module_files','packages','external_modules','external_inputs','module_verification','source_frame_sha256'),'build proof shape')
    quick_require(proof['schema']=='cat-quick-native-build-proof-1' and proof['go_version']=='go1.27.3','build proof identity/toolchain')
    quick_require(proof['tool']==tool,'build proof producer differs')
    quick_require(isinstance(proof['sdk_image'],str) and re.fullmatch('sha256:[0-9a-f]{64}',proof['sdk_image']) is not None,'owning SDK image digest required')
    quick_require(proof['build_flags']==['-trimpath','-mod=readonly','-buildvcs=false','-p=4'] and exact_keys(proof['target'],'goos','goarch','cgo_enabled') and proof['target']['goos']=='linux' and proof['target']['goarch']=='amd64' and proof['target']['cgo_enabled'] is False,'build flags/target differ')
    quick_require(proof['inventory_sha256']==quick_digest(inventory),'build receipt/current full inventory differs')
    for name,rel in [('compiled_rubric_sha256','docs/CRITIQUE_RUBRIC.md'),('compiled_authority_sha256','go-backend/internal/contentrails/sources/installed-authorities.json')]:
        raw=quick_read(root/rel)
        if name=='compiled_rubric_sha256':raw=raw.replace(b'\r\n',b'\n').replace(b'\r',b'\n')
        quick_pin(raw,proof[name],name)
    sources=proof['source_inputs']
    quick_require(isinstance(sources,list) and 1<=len(sources)<=20000,'build source inventory cap')
    paths=[v.get('path') for v in sources if isinstance(v,dict)]
    quick_require(len(paths)==len(sources) and all(isinstance(v,str) for v in paths) and paths==sorted(set(paths)),'build source inventory identity')
    # Root obtains this actual file membership from owning-toolchain go list
    # with the same target/flags. Its separately pinned receipt is the trust
    # anchor; the author bundle cannot attest its own compiled source closure.
    module_files=proof['module_files'];packages=proof['packages']
    quick_require(isinstance(module_files,list) and module_files==sorted(set(module_files)) and {'go-backend/go.mod','go-backend/go.sum'}<=set(module_files) and all(isinstance(v,str) and Path(v).name in ('go.mod','go.sum') for v in module_files),'compiled module membership')
    required=set(module_files)
    quick_require(isinstance(packages,list) and 1<=len(packages)<=2000,'compiled package cap')
    directories=[]
    for package in packages:
        quick_require(exact_keys(package,'directory','files') and isinstance(package['directory'],str),'compiled package shape')
        directory=Path(package['directory']);quick_require(not directory.is_absolute() and '..' not in directory.parts and directory.as_posix()==package['directory'],'compiled package path')
        quick_require(str(directory).startswith(('go-backend/','shared-go/')),'compiled package escaped local modules')
        directories.append(str(directory));fields=package['files']
        quick_require(exact_keys(fields,*GO_LIST_FILE_FIELDS),'compiled Go file fields')
        for names in fields.values():
            quick_require(isinstance(names,list) and all(isinstance(v,str) for v in names) and names==sorted(set(names)),'compiled file membership')
            for name in names:
                member=Path(name);quick_require(not member.is_absolute() and '..' not in member.parts and member.as_posix()==name,'compiled file path')
                required.add((directory/member).as_posix())
    quick_require(directories==sorted(set(directories)) and 'go-backend/cmd/cat-content-rail' in directories,'compiled command/package membership')
    quick_require(required==set(paths),'compiled source/embed/module membership differs')
    for binding in sources:quick_bound_file(binding,root)
    quick_external_proof(proof,root)
    return {'path':str(scratch(a.native_build_proof)),'sha256':sha256(data)}



def quick_external_proof(proof,root):
    quick_require(proof['module_verification']=={'before':'all modules verified','after':'all modules verified'},'offline dependency verification incomplete')
    quick_require(isinstance(proof['source_frame_sha256'],str) and re.fullmatch('[0-9a-f]{64}',proof['source_frame_sha256']) is not None,'source frame digest absent')
    modules=proof['external_modules'];inputs=proof['external_inputs']
    quick_require(isinstance(modules,list) and len(modules)<=512 and isinstance(inputs,list) and len(inputs)<=50000,'external compiled input cap')
    sums=set(quick_read(root/'go-backend/go.sum').decode().splitlines());identities={}
    for module in modules:
        quick_require(exact_keys(module,'path','version','sum','go_mod_sum') and all(isinstance(v,str) for v in module.values()),'external module identity shape')
        name=module['path'];version=module['version']
        quick_require(re.fullmatch('[A-Za-z0-9._~!+/-]+',name) is not None and '..' not in Path(name).parts and not name.startswith('/') and re.fullmatch('v[0-9][A-Za-z0-9.+-]*',version) is not None and name not in identities,'external module identity/version')
        quick_require(all(re.fullmatch(r'h1:[A-Za-z0-9+/]{43}=',module[k]) is not None for k in ('sum','go_mod_sum')),'external module checksum shape')
        quick_require(name+' '+version+' '+module['sum'] in sums and name+' '+version+'/go.mod '+module['go_mod_sum'] in sums,'external module not in current go.sum')
        identities[name]=module
    seen=set();coverage=set();mods=set()
    for row in inputs:
        quick_require(exact_keys(row,'module','path','bytes','sha256') and isinstance(row['module'],str) and row['module'] in identities and isinstance(row['path'],str) and type(row['bytes']) is int and 0<=row['bytes']<=QUICK_MEMBER_LIMIT and isinstance(row['sha256'],str) and re.fullmatch('[0-9a-f]{64}',row['sha256']) is not None,'external compiled member shape/identity')
        path=Path(row['path']);identity=(row['module'],row['path'])
        quick_require(not path.is_absolute() and '..' not in path.parts and path.as_posix()==row['path'] and identity not in seen,'external compiled member path/duplicate')
        seen.add(identity);coverage.add(row['module'])
        if row['path']=='go.mod':mods.add(row['module'])
    quick_require(set(identities)==coverage==mods,'external module source/go.mod coverage')
    quick_require([(r['module'],r['path']) for r in inputs]==sorted(seen),'external compiled input order')
    # Actual external body hashes and before/after go mod verify are Root's
    # pinned build evidence, never inferred from the SDK image or bundle.

def quick_run(tool,args,directory):
    # Only the independently pinned local operator executable is invoked.
    # CLI options are fixed; no source/fixture/install override is expressible.
    import tempfile
    with tempfile.TemporaryFile() as output,tempfile.TemporaryFile() as errors:
        try:
            result=subprocess.run([str(tool),'quick',*args],cwd=directory,stdin=subprocess.DEVNULL,stdout=output,stderr=errors,timeout=300,check=False)
        except subprocess.TimeoutExpired:fail('native quick: replay timed out')
        errors.seek(0);diagnostic=errors.read(1000).decode('utf-8',errors='replace')
        quick_require(result.returncode==0,'native replay refused: '+diagnostic.strip())
        quick_require(output.tell()<=QUICK_MEMBER_LIMIT,'native replay output cap')
        output.seek(0);return output.read()


def quick_role(bundle,item_id):
    quick_require(exact_keys(bundle,'schema','qualified','qualification','index','members') and bundle['schema']=='quick-pending-bundle-v1' and bundle['qualified'] is False and bundle['qualification']==QUICK_QUALIFICATION,'bundle identity/shape')
    index=bundle['index'];quick_require(exact_keys(index,'schema','qualified','approval','pending_sha256','descriptors') and index['schema']=='quick-pending-index-v1' and index['qualified'] is False and index['approval'] is None,'index shape')
    descriptors=index['descriptors'];quick_require(isinstance(descriptors,list) and 1<=len(descriptors)<=256,'descriptor cap')
    members={};raw_members=bundle['members'];quick_require(isinstance(raw_members,list) and len(raw_members)==1+3*len(descriptors),'member coverage')
    for row in raw_members:
        quick_require(exact_keys(row,'path','bytes','sha256','data') and isinstance(row['path'],str) and isinstance(row['data'],str) and type(row['bytes']) is int and row['path'] not in members,'member shape/duplicate')
        raw=row['data'].encode();quick_require(len(raw)==row['bytes'] and len(raw)<=QUICK_MEMBER_LIMIT,'member byte cap/count');quick_pin(raw,row['sha256'],'member')
        members[row['path']]=raw
    quick_require('pending.json' in members,'pending member absent');quick_pin(members['pending.json'],index['pending_sha256'],'pending')
    pending=json_object(members['pending.json'])
    quick_require(exact_keys(pending,'schema','status','provenance_mode','qualified','approval','qualification','baseline_source_sha256','baseline_source_version','bindings','inventory','tool','input_bindings','boards','rated','screen','preserved_old_rows'),'pending shape')
    quick_require(pending['schema']=='quick-pending-v1' and pending['status']=='pending' and pending['provenance_mode']=='source_backed' and pending['qualified'] is False and pending['approval'] is None and pending['qualification']==QUICK_QUALIFICATION,'pending status/provenance')
    quick_require(isinstance(pending['boards'],list) and len(pending['boards'])==len(descriptors),'board coverage')
    found=None;seen=set();used={'pending.json'}
    for descriptor in descriptors:
        quick_require(exact_keys(descriptor,'dossier_path','dossier_sha256','public_path','private_path','id','game','review_binding','record_sha256','kg_sha256','rubric_sha256','status','provenance_mode','source_id','runtime_id','pending_sha256'),'descriptor shape')
        id_=descriptor['id'];game=descriptor['game']
        quick_require(isinstance(id_,str) and game in QUICK_GAMES and re.fullmatch(('iq92_' if game=='intrusul' else 'pq92_')+'[A-Za-z0-9_-]{1,180}',id_) is not None and id_ not in seen,'game/namespace/duplicate')
        quick_require(isinstance(descriptor['source_id'],str) and re.fullmatch('aq92_[A-Za-z0-9_-]{1,180}',descriptor['source_id']) is not None and isinstance(descriptor['runtime_id'],str) and re.fullmatch(('vi_' if game=='intrusul' else 'vp_')+'[0-9a-f]{20}',descriptor['runtime_id']) is not None,'private identity namespace')
        seen.add(id_);challenge=quick_digest([index['pending_sha256'],id_,'quick-pending-regular-category-v1'])[:24]
        paths={'dossier_path':'dossiers/'+id_+'.json','public_path':'public/'+challenge+'.json','private_path':'private/'+challenge+'.json'}
        for name,path in paths.items():
            quick_require(descriptor[name]==path and path in members and path not in used,'role path/coverage');used.add(path)
        dossier_raw=members[paths['dossier_path']];quick_pin(dossier_raw,descriptor['dossier_sha256'],'dossier');dossier=json_object(dossier_raw)
        quick_require(exact_keys(dossier,'schema','id','game','status','provenance_mode','source_id','runtime_id','record_sha256','kg_sha256','rubric_sha256','pending_sha256','baseline_source_sha256','bindings','semantic_payload','nodes','category','difficulty','public_projection_sha256','private_projection_sha256','screen','approval','qualified','qualification','review_binding'),'dossier shape')
        quick_require(dossier['schema']=='quick-pending-dossier-v1' and dossier['approval'] is None and dossier['qualified'] is False and dossier['qualification']==QUICK_QUALIFICATION,'dossier identity')
        for name in ('id','game','status','provenance_mode','source_id','runtime_id','record_sha256','kg_sha256','rubric_sha256','pending_sha256','review_binding'):quick_require(dossier[name]==descriptor[name],'descriptor/dossier mixed')
        quick_require(dossier['status']=='pending' and dossier['provenance_mode']=='source_backed' and dossier['pending_sha256']==index['pending_sha256'] and dossier['baseline_source_sha256']==pending['baseline_source_sha256'] and dossier['bindings']==pending['bindings'] and dossier['screen']==pending['screen'],'mixed pending bindings')
        bound={k:v for k,v in dossier.items() if k not in ('review_binding','rubric_sha256')}
        quick_require(dossier['review_binding']=='sha256:'+quick_digest({'schema':'quick-pending-review-binding-v1','rubric_sha256':dossier['rubric_sha256'],'dossier':bound}),'review binding')
        pub_raw=members[paths['public_path']];priv_raw=members[paths['private_path']]
        quick_pin(pub_raw,dossier['public_projection_sha256'],'public');quick_pin(priv_raw,dossier['private_projection_sha256'],'private')
        public=json_object(pub_raw);private=json_object(priv_raw)
        quick_public(public,private,dossier,pending,challenge)
        if id_==item_id:found=(pending,dossier,public,private,pub_raw)
    quick_require(used==set(members) and found is not None,'exact selected item/member inventory required')
    return found


def quick_public(public,private,dossier,pending,challenge):
    game=dossier['game'];count=4 if game=='intrusul' else 8
    quick_require(exact_keys(public,'schema','challenge_id','game','mode','context','tiles','task','response_schema') and public['schema']=='quick-pending-public-v1' and public['challenge_id']==challenge and public['game']==game and public['mode']=='regular_category','public game/mode/schema')
    quick_require(exact_keys(private,'schema','challenge_id','id','runtime_id','game','mode','seed','token_map','expected_answer','native_initial_state','initial_get_equal','isolated_overlay_only','approval') and private['schema']=='quick-pending-private-v1' and private['challenge_id']==challenge and private['id']==dossier['id'] and private['runtime_id']==dossier['runtime_id'] and private['game']==game and private['mode']=='regular_category' and type(private['seed']) is int and 0<=private['seed']<5000 and private['initial_get_equal'] is True and private['isolated_overlay_only'] is True and private['approval'] is None,'private game/mode/native proof')
    tiles=public['tiles'];quick_require(isinstance(tiles,list) and len(tiles)==count,'public tile count')
    tokens=['t'+str(i+1).zfill(4) for i in range(count)]
    quick_require(all(exact_keys(t,'tile','text') and t['tile']==tokens[i] and isinstance(t['text'],str) and t['text'].strip() for i,t in enumerate(tiles)),'public tile token/text shape')
    context=public['context'];quick_require(isinstance(context,dict) and set(context)<=set(('difficulty','board_category','category_label')) and all(isinstance(v,str) and v.strip() for v in context.values()),'public context allowlist')
    tm=private['token_map'];quick_require(isinstance(tm,dict) and len(tm)==count and all(isinstance(k,str) for k in tm) and set(tm.values())==set(tokens),'private token permutation')
    state=private['native_initial_state'];quick_require(isinstance(state,dict) and isinstance(state.get('tiles'),list) and len(state['tiles'])==count,'native state tiles')
    quick_require({k:state[k] for k in ('difficulty','board_category','category_label') if k in state}==context,'native public context drift')
    for i,tile in enumerate(state['tiles']):
        quick_require(exact_keys(tile,*(('id','label') if game=='intrusul' else ('id','label','solved'))) and (game=='intrusul' or tile['solved'] is False) and tm.get(tile['id'])==tokens[i] and tile['label']==tiles[i]['text'],'native tile rendering/permutation drift')
    quick_require(state.get('solution') is None and state.get('score') is None,'unearned answer/score')
    rows=[r for r in pending['boards'] if isinstance(r,dict) and r.get('id')==dossier['id']]
    quick_require(len(rows)==1,'exact authored row absent');row=rows[0]
    quick_require(exact_keys(row,'id','game','source_id','category','difficulty','payload','sources','rationale') and row['game']==game and row['source_id']==dossier['source_id'] and row['category']==dossier['category'] and row['difficulty']==dossier['difficulty'] and row['payload']==dossier['semantic_payload'] and quick_digest(row)==dossier['record_sha256'],'frozen raw authored row differs')
    quick_require(isinstance(row['sources'],list) and 1<=len(row['sources'])<=16 and all(isinstance(u,str) and re.fullmatch(r'https?://[^\s]+',u) for u in row['sources']) and isinstance(row['rationale'],str) and row['rationale'].strip(),'source-backed author shape/cap')
    p=row['payload'];answer=private['expected_answer']
    if game=='intrusul':
        quick_require(exact_keys(p,'members','intruder','group_label') and isinstance(p['members'],list) and len(p['members'])==3 and isinstance(p['intruder'],str),'intrusul payload')
        visible=p['members']+[p['intruder']]
        quick_require(exact_keys(answer,'odd','predicate') and answer['odd']==tm.get(p['intruder']) and answer['predicate']==p['group_label'],'private odd key differs')
        task='Pick the single odd tile and explain the natural predicate shared by the other three; report any alternate odd tile or predicate.'
        schema={'odd':'tile','predicate':'nonblank text','tile_explanations':'one per tile','alternate_predicates':[],'ambiguous':False}
        predicates=[p['group_label']]
    else:
        quick_require(exact_keys(p,'pairs') and isinstance(p['pairs'],list) and len(p['pairs'])==4 and all(exact_keys(pair,'members','group_label') and isinstance(pair['members'],list) and len(pair['members'])==2 for pair in p['pairs']),'perechi payload')
        visible=[x for pair in p['pairs'] for x in pair['members']]
        expected=[{'members':sorted(tm.get(x,'') for x in pair['members']),'predicate':pair['group_label']} for pair in p['pairs']]
        quick_require(exact_keys(answer,'pairs') and answer['pairs']==expected,'private pair key differs')
        task='Match all eight tiles into four natural pairs; explain each pair and report any competing matching or ambiguous tile.'
        schema={'pairs':'four disjoint tile pairs','explanations':'four nonblank texts','alternate_matching':None,'ambiguous':False}
        predicates=[pair['group_label'] for pair in p['pairs']]
    quick_require(all(isinstance(x,str) for x in visible) and len(set(visible))==count and set(visible)==set(tm),'payload/private tile coverage')
    quick_require(public['task']==task and public['response_schema']==schema and public['response_schema']['ambiguous'] is False,'public instruction/hint schema changed')
    quick_require(isinstance(dossier['nodes'],dict) and set(dossier['nodes'])==set(visible),'dossier node scope')
    # Public values must come from the native visible fields or the exact fixed
    # instructions. Semantic text embedded in a legitimate label still requires
    # the independent critic; private metadata cannot introduce another field.
    public_text=compact(public).decode()
    forbidden=[row['id'],row['source_id'],dossier['runtime_id'],row['rationale'],*row['sources'],*predicates]
    quick_require(all(isinstance(v,str) and v.strip() and v not in public_text for v in forbidden),'private identity/rationale/source/predicate leakage')


def quick_cache_context(a,root,external,evidence,seal,bound,selected,captures):
    path=getattr(a,'author_cache_binding',None)
    expected=getattr(a,'author_cache_binding_sha256',None)
    v2=evidence.get('schema')=='quick-author-evidence-v2'
    if not v2:
        quick_require(not path and not expected and 'author_cache_binding_sha256' not in bound,'known cache exposure context cannot select v1')
        return None,set()
    quick_require(isinstance(path,str) and isinstance(expected,str) and re.fullmatch('[0-9a-f]{64}',expected) is not None,'independent Root cache path and SHA required')
    quick_require(path not in selected.values() and path not in captures and path in external,'Root cache binding role/path missing or aliased')
    quick_require(str(quick_path(path))==path,'Root cache binding canonical path')
    quick_pin(external[path],expected,'independent Root cache binding')
    binding=json_object(external[path])
    quick_require(exact_keys(binding,'schema','operator','root','baseline_source_sha256','inventory_sha256','packet_sha256','run_id','cache_root','client','author','author_context','created_at','source_controls','first_receipt_journal','owner_refusals','attempts','deliveries','inspection_ack','exposure_urls') and binding['schema']=='quick-author-cache-binding-v1' and binding['operator']=='agent:codex' and binding['root']==str(root),'Root cache binding shape/operator/current root')
    quick_require(bound.get('author_cache_binding_sha256')==expected and binding['packet_sha256']==bound['author_packet_sha256'] and binding['inventory_sha256']==bound['inventory_sha256'],'Root cache current packet/inventory binding')
    quick_require(evidence.get('packet_sha256')==bound['author_packet_sha256'] and seal.get('packet_sha256')==bound['author_packet_sha256'] and seal.get('evidence_sha256')==bound['author_evidence_sha256'] and seal.get('cache_binding_sha256')==expected and seal.get('schema')=='quick-author-seal-v2','v2 seal/evidence/independent Root pin binding')
    quick_require(exact_keys(evidence,'schema','packet_sha256','items','receipts','cache_binding') and exact_keys(seal,'schema','author','packet_sha256','evidence_sha256','cache_binding_sha256','sealed_at','urls'),'v2 exact evidence/seal schema')
    urls=binding['exposure_urls']
    quick_require(isinstance(urls,list) and 1<=len(urls)<=4096 and all(isinstance(u,str) for u in urls) and urls==sorted(set(urls)) and seal['urls']==urls,'complete sorted author exposure')
    quick_require(isinstance(binding['attempts'],list) and 1<=len(binding['attempts'])<=64 and isinstance(binding['deliveries'],list) and len(binding['deliveries'])==len(urls),'fixed cache attempt/delivery caps')
    used={path};roles={path:'binding'}
    def descriptor(value,role,existing=False):
        quick_require(exact_keys(value,'path','bytes','sha256') and isinstance(value['path'],str) and type(value['bytes']) is int and 1<=value['bytes']<=4<<20 and isinstance(value['sha256'],str),'cache closure descriptor shape/cap')
        name=value['path'];quick_require(name in external and (existing or name not in roles) and name not in selected.values() and name not in captures,'cache closure unknown/multiple artifact roles')
        quick_require(str(quick_path(name))==name and root not in Path(name).parents,'cache closure canonical/external path')
        quick_require(len(external[name])==value['bytes'],'cache closure byte count');quick_pin(external[name],value['sha256'],'cache closure '+role)
        used.add(name);roles[name]=role
        return external[name]
    quick_require(evidence['cache_binding']=={'path':path,'bytes':len(external[path]),'sha256':expected},'evidence Root binding descriptor differs')
    for key in ('client','first_receipt_journal','owner_refusals','inspection_ack'):descriptor(binding[key],key)
    quick_require(binding['client']['sha256']=='29f6979a54bba0bb5858c9449e226f759d863ef11667db8ceee30de0ee9f33c3','approved manual client only')
    controls=json_object(descriptor(binding['source_controls'],'source_controls'))
    quick_require(exact_keys(controls,'schema','run_id','client_sha256','checked_at','terms_checked_by','terms_evidence','hosts') and controls['schema']=='quick-cache-current-controls-v1' and isinstance(controls['hosts'],list) and 1<=len(controls['hosts'])<=3 and isinstance(controls['terms_evidence'],list) and 1<=len(controls['terms_evidence'])<=32,'fixed source-control closure shape/caps')
    for i,value in enumerate(controls['terms_evidence']):descriptor(value,'terms/'+str(i))
    for i,value in enumerate(controls['hosts']):
        quick_require(exact_keys(value,'host','state','robots_receipt','robots_body'),'source-control host shape')
        for key in ('state','robots_receipt','robots_body'):descriptor(value[key],'host/'+str(i)+'/'+key)
    for i,value in enumerate(binding['attempts']):descriptor(value,'attempt/'+str(i))
    for i,value in enumerate(binding['deliveries']):
        quick_require(exact_keys(value,'url','first_receipt','attempt_sha256','result_row','requested_role','delivery_kind','requested_at','client_requested_at','observed_by','observation_kind'),'Root delivery exact shape')
        descriptor(value['first_receipt'],'first_receipt/'+str(i))
    return {'binding':{'path':path,'sha256':expected},'exposure_urls':urls},used


def quick_current(a):
    import tempfile
    root=quick_path(str(Path(a.root).absolute()));repo=Repo(root)
    bundle_path=scratch(a.pending_bundle);blob=quick_read(bundle_path);quick_pin(blob,a.pending_sha256,'whole bundle')
    pending,dossier,public,private,pub_raw=quick_role(json_object(blob),a.item_id)
    tool_path=quick_path(a.native_tool);tool_hash,tool_size=quick_tool_hash(tool_path)
    quick_require(tool_hash==a.native_tool_sha256,'pinned native producer hash differs')
    tool={'path':str(tool_path),'sha256':tool_hash,'bytes':tool_size,'go_version':'go1.27.3'}
    quick_require(pending['tool']==tool,'bundle native producer differs')
    consumer=[]
    for name in ('common.py','critic_blind.py'):
        executing=quick_read(Path(__file__).resolve().with_name(name))
        current=quick_read(root/'scripts/miner'/name)
        quick_require(executing==current,'executing consumer differs from current root '+name)
        consumer.append({'path':'scripts/miner/'+name,'sha256':sha256(current),'bytes':len(current)})
    proof=quick_build_proof(a,root,tool,pending['inventory'])
    inventory=pending['inventory'];quick_require(exact_keys(inventory,'schema','baseline_source_sha256','baseline_source_version','members') and inventory['schema']=='quick-pending-inventory-v1' and inventory['baseline_source_sha256']==pending['baseline_source_sha256'] and type(inventory['baseline_source_version']) is int and inventory['baseline_source_version']==pending['baseline_source_version'],'inventory identity')
    members=inventory['members'];quick_require(isinstance(members,list) and 1<=len(members)<=20000,'inventory cap')
    paths=[r.get('path') for r in members if isinstance(r,dict)];quick_require(len(paths)==len(members) and all(isinstance(p,str) for p in paths) and paths==sorted(set(paths)),'inventory path identity')
    for row in members:quick_bound_file(row,root)
    bound=pending['bindings'];binding_keys=['kg_sha256','rubric_sha256','inventory_sha256','stock_sha256','holds_sha256','registry_sha256','author_packet_sha256','author_seal_sha256','author_evidence_sha256','tool_sha256']
    if 'author_cache_binding_sha256' in bound:binding_keys.append('author_cache_binding_sha256')
    quick_require(exact_keys(bound,*binding_keys),'binding shape')
    quick_require(all(isinstance(v,str) and re.fullmatch('[0-9a-f]{64}',v) is not None for v in bound.values()),'binding digest shape')
    quick_require(bound['inventory_sha256']==quick_digest(inventory) and bound['tool_sha256']==tool_hash,'inventory/tool binding differs')
    for field,rel in [('kg_sha256',FIX+'kg_sample.json'),('rubric_sha256','docs/CRITIQUE_RUBRIC.md')]:
        data=quick_read(root/rel).replace(b'\r\n',b'\n').replace(b'\r',b'\n');quick_pin(data,bound[field],field);quick_require(dossier[field]==bound[field],'dossier '+field)
    kg=json_object(quick_read(root/(FIX+'kg_sample.json')))
    quick_require(isinstance(kg.get('kg_nodes'),list),'current KG nodes absent')
    labels={row['id']:row['label_ro'] for row in kg['kg_nodes'] if isinstance(row,dict) and isinstance(row.get('id'),str) and isinstance(row.get('label_ro'),str)}
    quick_require(len(labels)==len(kg['kg_nodes']),'current KG node identity duplicate/invalid')
    # Raw NodeSnapshot labels remain raw; displayed casing belongs exclusively
    # to the native parser/rules and is proved by the fresh native replay.
    for tile in public['tiles']:
        ids=[id_ for id_,token in private['token_map'].items() if token==tile['tile']]
        quick_require(len(ids)==1 and ids[0] in labels and dossier['nodes'][ids[0]].get('label_ro')==labels[ids[0]],'current KG/dossier raw label differs')
    for field,rel in [('holds_sha256','docs/content-registry/exclusions.json'),('registry_sha256','docs/content-registry/registry.jsonl')]:quick_pin(quick_read(root/rel),bound[field],field)
    inputs=pending['input_bindings'];quick_require(isinstance(inputs,list) and 4<=len(inputs)<=4100,'external readset cap')
    external={};total=0
    for row in inputs:
        quick_require(isinstance(row,dict) and isinstance(row.get('path'),str) and row['path'] not in external,'external readset duplicate')
        path=quick_path(row['path']);quick_require(root not in path.parents and path!=tool_path,'external input/source override')
        data=quick_bound_file(row);total+=len(data);quick_require(total<=QUICK_EXTERNAL_LIMIT,'external evidence aggregate exceeds 64 MiB');external[row['path']]=data
    selected={}
    for name,field,schema in [('packet','author_packet_sha256','quick-author-packet-v1'),('seal','author_seal_sha256','quick-author-seal-v1'),('evidence','author_evidence_sha256','quick-author-evidence-v1')]:
        matches=[p for p,b in external.items() if sha256(b)==bound[field]];quick_require(len(matches)==1,'author input binding ambiguous/missing')
        selected[name]=matches[0];actual_schema=json_object(external[matches[0]]).get('schema');quick_require(actual_schema==schema or name in ('seal','evidence') and actual_schema==schema[:-1]+'2','author input schema')
    packet=json_object(external[selected['packet']]);quick_require(exact_keys(packet,'schema','baseline_source_sha256','boards') and packet['baseline_source_sha256']==pending['baseline_source_sha256'] and packet['boards']==pending['boards'],'exact raw author packet differs')
    # Captures may be HTML/binary: identify inventory only among JSON candidates.
    inv_matches=[]
    for path,data in external.items():
        if sha256(data)==bound['author_packet_sha256'] or path in selected.values():continue
        try:value=json_object(data)
        except (ValueError,UnicodeError):continue
        if value==inventory:inv_matches.append(path)
    quick_require(len(inv_matches)==1,'exact native inventory input absent')
    selected['inventory']=inv_matches[0]
    quick_require(all(len(data)<=4<<20 for path,data in external.items() if path!=selected['inventory']),'external author/source document exceeds 4 MiB')
    evidence=json_object(external[selected['evidence']]);quick_require(isinstance(evidence.get('receipts'),list),'receipt inventory absent')
    captures={r.get('capture_path') for r in evidence['receipts'] if isinstance(r,dict)}
    seal=json_object(external[selected['seal']])
    cache_context,cache_paths=quick_cache_context(a,root,external,evidence,seal,bound,selected,captures)
    if cache_context:quick_require(json_object(external[cache_context['binding']['path']])['baseline_source_sha256']==pending['baseline_source_sha256'],'cache binding stale baseline')
    quick_require(set(external)==set(selected.values())|captures|cache_paths,'external readset exact fixed capture/cache closure coverage')
    replay_cache=[] if cache_context is None else ['--author-cache-binding',cache_context['binding']['path'],'--author-cache-binding-sha256',cache_context['binding']['sha256']]
    # Native replay checks compiled rubric/authority, full current path membership,
    # source chain, stock/history/holds, raw inputs and actual service projections.
    # View extraction is intentionally never used as a freshness attestation.
    with tempfile.TemporaryDirectory(prefix='quick-replay-',dir=scratch(a.scratch_root)) as temp:
        current=json_object(quick_run(tool_path,['--root',str(root),'--pending-inventory'],temp))
        quick_require(current==inventory,'current native inventory differs')
        out=Path(temp)/'replayed.json'
        quick_run(tool_path,['--root',str(root),'--prepare-pending',selected['packet'],'--inventory-manifest',selected['inventory'],'--author-seal',selected['seal'],'--receipt-manifest',selected['evidence'],'--pending-out',str(out),*replay_cache],temp)
        quick_require(quick_read(out)==blob,'fresh native preparation bytes differ')
    # Reread the frozen readsets after the subprocess before publishing either key.
    quick_require(quick_read(bundle_path)==blob,'bundle changed during replay')
    for row in members:quick_bound_file(row,root)
    for row in inputs:quick_bound_file(row)
    quick_require(quick_tool_hash(tool_path)==(tool_hash,tool_size),'producer changed during replay')
    # Compiled embeds (.sql, embedfs and testdata included) can be absent from
    # the native runtime inventory. Recheck the entire independently pinned
    # proof and its declared local source bodies after the expensive replay.
    quick_require(quick_build_proof(a,root,tool,pending['inventory'])==proof,'build proof changed during replay')
    binding={'stock_screen':pending['screen'],'consumer_tools':consumer,'root':str(root),'baseline_source_sha256':pending['baseline_source_sha256'],'baseline_source_version':pending['baseline_source_version'],'bundle':{'path':str(bundle_path),'sha256':sha256(blob)},'native_tool':tool,'native_build_proof':proof,'pending_sha256':json_object(blob)['index']['pending_sha256'],'record_sha256':dossier['record_sha256'],'review_binding':dossier['review_binding'],'bindings':bound,'inventory_sha256':quick_digest(inventory),'game':public['game'],'mode':public['mode']}
    if cache_context is not None:binding['author_cache_context']=cache_context
    return public,private,pub_raw,binding


def build_quick(a):
    public_path=output_path(a.public_out);key_path=output_path(a.key_out)
    quick_require(public_path!=key_path,'public/private path collision')
    public,private,pub_raw,binding=quick_current(a)
    key={'schema':'cat-quick-blind-key-1','challenge_id':public['challenge_id'],'game':public['game'],'mode':public['mode'],'item_id':a.item_id,'native_binding':binding,'public_binding':{'path':str(public_path),'sha256':sha256(pub_raw)},'private_projection':private,'approval':None}
    write_bytes(public_path,pub_raw)
    try:write_json(key_path,key)
    except (OSError,ValueError):public_path.unlink(missing_ok=True);raise
    print(json.dumps({'public_out':str(public_path),'key_out':str(key_path),'challenge_id':public['challenge_id'],'public_sha256':sha256(pub_raw),'response_binding':{'challenge_id':public['challenge_id'],'public_sha256':sha256(pub_raw),'game':public['game'],'mode':public['mode']},'approval':None},sort_keys=True))


def compare_quick(a):
    key_path=scratch(a.key);response_path=scratch(a.response)
    quick_require(key_path!=response_path,'response/key collision')
    key_data=quick_read(key_path);key=json_object(key_data);response_data=quick_read(response_path);response=json_object(response_data)
    quick_require(exact_keys(key,'schema','challenge_id','game','mode','item_id','native_binding','public_binding','private_projection','approval') and key['schema']=='cat-quick-blind-key-1' and key['item_id']==a.item_id and key['approval'] is None,'key shape/item')
    public,private,pub_raw,binding=quick_current(a)
    quick_require(key['native_binding']==binding and key['private_projection']==private and key['game']==public['game'] and key['mode']==public['mode'] and key['challenge_id']==public['challenge_id'],'private key/current producer binding differs')
    pb=key['public_binding'];quick_require(exact_keys(pb,'path','sha256') and quick_read(scratch(pb['path']))==pub_raw and pb['sha256']==sha256(pub_raw),'public task missing or hash changed')
    quick_require(response.get('challenge_id')==public['challenge_id'] and response.get('public_sha256')==sha256(pub_raw) and response.get('game')==public['game'] and response.get('mode')==public['mode'],'response challenge/public/game/mode binding differs')
    tokens={row['tile'] for row in public['tiles']};expected=private['expected_answer'];game=public['game'];issues=[];details={};match=False
    common={'challenge_id','public_sha256','game','mode','ambiguous'}
    if game=='intrusul':
        quick_require(set(response)==common|{'odd','predicate','tile_explanations','alternate_predicates'},'response exact Intrusul schema')
        odd=response['odd'];quick_require(isinstance(odd,str) and odd in tokens,'unknown/malformed odd token')
        match=odd==expected['odd']
        explanations=response['tile_explanations'];quick_require(isinstance(explanations,dict) and set(explanations)==tokens,'each-tile explanation coverage')
        if not isinstance(response['predicate'],str) or not response['predicate'].strip():issues.append('nonblank truthful predicate required')
        if not all(isinstance(v,str) and v.strip() for v in explanations.values()):issues.append('nonblank semantic explanation for every tile required')
        quick_require(isinstance(response['alternate_predicates'],list),'explicit alternate_predicates list required')
        if response['alternate_predicates']:issues.append('critic reported alternate odd predicate')
        details={'odd_exact_match':match,'semantic_predicate_truth_verified':False}
    else:
        quick_require(set(response)==common|{'pairs','explanations','alternate_matching'},'response exact Perechi schema')
        pairs=response['pairs'];quick_require(isinstance(pairs,list) and len(pairs)==4 and all(isinstance(p,list) and len(p)==2 and all(isinstance(v,str) for v in p) for p in pairs),'four pairs required')
        flat=[v for pair in pairs for v in pair];quick_require(len(set(flat))==8 and set(flat)==tokens,'unknown/duplicated/missing pair token')
        match=partitions(pairs)==partitions(p['members'] for p in expected['pairs'])
        explanations=response['explanations'];quick_require(isinstance(explanations,list) and len(explanations)==4,'one explanation aligned to each submitted pair required')
        if not all(isinstance(v,str) and v.strip() for v in explanations):issues.append('four nonblank semantic pair explanations required')
        quick_require(response['alternate_matching'] is None or isinstance(response['alternate_matching'],list),'explicit alternate_matching required')
        if response['alternate_matching'] is not None:issues.append('critic reported alternate matching')
        details={'matching_exact_match':match,'semantic_pair_truth_verified':False}
    if response['ambiguous'] is not False:issues.append('critic ambiguity flag missing or true')
    result={'schema':'cat-quick-blind-comparison-1','challenge_id':public['challenge_id'],'game':game,'mode':public['mode'],'public_binding':pb,'native_binding':binding,'key_binding':{'path':str(key_path),'sha256':sha256(key_data)},'response_binding':{'path':str(response_path),'sha256':sha256(response_data)},'mechanical_match':match,'details':details,'issues':issues,'status':'needs_human_semantic_checks' if match and not issues else 'critic_filter_failure','approval':None,'human_checks_required':['Truthful natural exact-sense predicates','No equally valid semantic alternate','Recognition and source-backed A/I/J review','Independent critic and factual/quality roles','Unresolved history relevance closure remains mandatory'],'limitation':'Operator-pinned tool/build receipt plus fresh native replay bind bytes only; no semantic, source-policy, independence, installation or serving approval.'}
    quick_require(quick_read(key_path)==key_data,'retained private key changed during comparison')
    quick_require(quick_read(response_path)==response_data,'retained critic response changed during comparison')
    write_json(a.out,result);print(json.dumps({'out':str(scratch(a.out)),'mechanical_match':match,'issues':len(issues),'status':result['status'],'approval':None},sort_keys=True))


def add_quick_arguments(parser):
    parser.add_argument('--root',required=True);parser.add_argument('--pending-bundle',required=True);parser.add_argument('--pending-sha256',required=True)
    parser.add_argument('--item-id',required=True);parser.add_argument('--native-tool',required=True);parser.add_argument('--native-tool-sha256',required=True)
    parser.add_argument('--native-build-proof',required=True);parser.add_argument('--native-build-proof-sha256',required=True)
    parser.add_argument('--author-cache-binding');parser.add_argument('--author-cache-binding-sha256')
    add_scratch_argument(parser)


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
    qb=sub.add_parser('build-quick',help='native-bound pending I/J critic task; no approval')
    add_quick_arguments(qb);qb.add_argument('--public-out',required=True);qb.add_argument('--key-out',required=True)
    qc=sub.add_parser('compare-quick',help='revalidate native pending I/J bindings and compare retained response')
    add_quick_arguments(qc);qc.add_argument('--key',required=True);qc.add_argument('--response',required=True);qc.add_argument('--out',required=True)
    a=p.parse_args()
    set_scratch_root(a.scratch_root)
    if a.command=='build':
        if not 16<=a.max_graph_nodes<=4096:fail('max-graph-nodes must be 16..4096')
        build(a)
    elif a.command=='compare':compare(a)
    elif a.command=='build-quick':build_quick(a)
    else:compare_quick(a)

if __name__=='__main__':run(main)
