"""Synthetic schema/unit tests only: mocked native replay is never qualification.

No production fixture, authority or source is modified. The tiny synthetic root
cannot pass the real Go producer. All native invocations are replaced explicitly
inside these tests; Root must separately run the owning pinned producer tests.
"""
import copy
import contextlib
import io
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch


HERE=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('quick_blind_under_test',HERE/'scripts/miner/critic_blind.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


def raw(value):
    return m.json_bytes(value)


def save(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_bytes(value if isinstance(value,bytes) else raw(value))
    return path


def bound(path,relative=None):
    data=path.read_bytes()
    return {'path':relative if relative is not None else str(path),'bytes':len(data),'sha256':m.sha256(data)}


class SyntheticNativeFixture:
    """Actual native schema, explicitly synthetic bytes and mocked producer."""
    def __init__(self,base,game):
        self.base=base;self.root=base/'synthetic-root';self.scratch=base/'scratch'
        self.scratch.mkdir();self.game=game;self.count=4 if game=='intrusul' else 8
        self.id=('iq92_' if game=='intrusul' else 'pq92_')+'synthetic_unit'
        self.runtime=('vi_' if game=='intrusul' else 'vp_')+'1'*20
        self.nodes=[{'id':'unit_node_'+str(i),'label_ro':'Cuvânt '+str(i)} for i in range(self.count)]
        save(self.root/m.FIX/'kg_sample.json',{'kg_nodes':self.nodes,'kg_edges':[]})
        save(self.root/'docs/CRITIQUE_RUBRIC.md',b'## I.\nSynthetic test only\n## J.\n')
        save(self.root/'docs/content-registry/registry.jsonl',b'unit unresolved history\n')
        save(self.root/'docs/content-registry/exclusions.json',{'schema':'synthetic-exclusions'})
        save(self.root/'go-backend/internal/contentrails/sources/installed-authorities.json',{'schema':'synthetic-unit-authority'})
        save(self.root/'go-backend/cmd/cat-content-rail/main.go',b'package main\nfunc main() {}\n')
        save(self.root/'go-backend/go.mod',b'module synthetic.unit\ngo 1.27.3\n')
        save(self.root/'go-backend/go.sum',b'')
        for name in ('common.py','critic_blind.py'):save(self.root/'scripts/miner'/name,(HERE/'scripts/miner'/name).read_bytes())
        self.tool=save(self.scratch/'synthetic-producer-placeholder',b'NOT AN EXECUTABLE: SYNTHETIC UNIT PROOF ONLY\n')
        self.tool_binding={**bound(self.tool),'go_version':'go1.27.3'}
        ids=[n['id'] for n in self.nodes]
        payload={'members':ids[:3],'intruder':ids[3],'group_label':'PRIVATE_PREDICATE_SENTINEL'} if game=='intrusul' else {'pairs':[{'members':ids[i:i+2],'group_label':'PRIVATE_PAIR_SENTINEL_'+str(i)} for i in range(0,8,2)]}
        self.row={'id':self.id,'game':game,'source_id':'aq92_synthetic_unit','category':'viata_de_roman','difficulty':'normal','payload':payload,'sources':['https://example.test/AUTHOR_SOURCE_SENTINEL'],'rationale':'AUTHOR_RATIONALE_SENTINEL'}
        self.packet_path=self.scratch/'packet.json';self.seal_path=self.scratch/'seal.json';self.evidence_path=self.scratch/'evidence.json';self.inventory_path=self.scratch/'inventory.json';self.capture_path=save(self.scratch/'capture.html',b'<p>SYNTHETIC CAPTURE ONLY</p>')
        self.bundle_path=self.scratch/'bundle.json';self.proof_path=self.scratch/'proof.json'
        self.native_labels={}
        self.public_mutator=None;self.private_mutator=None;self.dossier_mutator=None;self.pending_mutator=None
        self.rebuild()

    def rebuild(self):
        root=self.root
        members=[bound(path,path.relative_to(root).as_posix()) for path in sorted(root.rglob('*')) if path.is_file()]
        self.inventory={'schema':'quick-pending-inventory-v1','baseline_source_sha256':'a'*64,'baseline_source_version':25,'members':members}
        save(self.inventory_path,self.inventory)
        self.packet={'schema':'quick-author-packet-v1','baseline_source_sha256':'a'*64,'boards':[self.row]};save(self.packet_path,self.packet)
        save(self.seal_path,{'schema':'quick-author-seal-v1','author':'AUTHOR_NAME_SENTINEL','packet_sha256':m.sha256(self.packet_path.read_bytes()),'sealed_at':'2026-11-10T12:00:00Z','urls':self.row['sources']})
        self.evidence={'schema':'quick-author-evidence-v1','packet_sha256':m.sha256(self.packet_path.read_bytes()),'items':{self.id:'source_backed'},'receipts':[{'url':self.row['sources'][0] if self.row['sources'] else 'https://example.test/unit','capture_path':str(self.capture_path),'capture_sha256':m.sha256(self.capture_path.read_bytes()),'bytes':len(self.capture_path.read_bytes()),'fetched_by_role':'author','fetched_at':'2026-11-10T11:00:00Z'}]}
        save(self.evidence_path,self.evidence)
        bindings={'kg_sha256':m.sha256((root/m.FIX/'kg_sample.json').read_bytes()),'rubric_sha256':m.sha256((root/'docs/CRITIQUE_RUBRIC.md').read_bytes()),'inventory_sha256':m.quick_digest(self.inventory),'stock_sha256':'b'*64,'holds_sha256':m.sha256((root/'docs/content-registry/exclusions.json').read_bytes()),'registry_sha256':m.sha256((root/'docs/content-registry/registry.jsonl').read_bytes()),'author_packet_sha256':m.sha256(self.packet_path.read_bytes()),'author_seal_sha256':m.sha256(self.seal_path.read_bytes()),'author_evidence_sha256':m.sha256(self.evidence_path.read_bytes()),'tool_sha256':self.tool_binding['sha256']}
        self.pending={'schema':'quick-pending-v1','status':'pending','provenance_mode':'source_backed','qualified':False,'approval':None,'qualification':m.QUICK_QUALIFICATION,'baseline_source_sha256':'a'*64,'baseline_source_version':25,'bindings':bindings,'inventory':self.inventory,'tool':self.tool_binding,'input_bindings':[bound(p) for p in sorted([self.packet_path,self.seal_path,self.evidence_path,self.inventory_path,self.capture_path])],'boards':[self.row],'rated':[{'id':self.runtime}],'screen':{'schema':'quick-pending-stock-screen-v1','complete':False,'unresolved_quick_history':['unit_research_'+str(i) for i in range(13)],'unresolved_history_requires_independent_relevance_closure':True,'approval':None},'preserved_old_rows':[]}
        if self.pending_mutator:self.pending_mutator(self.pending)
        self.pending_raw=raw(self.pending);pending_sha=m.sha256(self.pending_raw);challenge=m.quick_digest([pending_sha,self.id,'quick-pending-regular-category-v1'])[:24]
        order=[2,0,3,1] if self.game=='intrusul' else [3,0,7,2,4,6,1,5]
        self.token_map={self.nodes[n]['id']:'t'+str(i+1).zfill(4) for i,n in enumerate(order)}
        tiles=[{'tile':self.token_map[self.nodes[n]['id']],'text':self.native_labels.get(self.nodes[n]['id'],self.nodes[n]['label_ro'])} for n in order]
        state_tiles=[{'id':self.nodes[n]['id'],'label':self.native_labels.get(self.nodes[n]['id'],self.nodes[n]['label_ro']),**({'solved':False} if self.game=='perechi' else {})} for n in order]
        context={'board_category':'viata_de_roman',**({'difficulty':'normal'} if self.game=='intrusul' else {})}
        if self.game=='intrusul':
            answer={'odd':self.token_map[self.row['payload']['intruder']],'predicate':self.row['payload']['group_label']}
            task='Pick the single odd tile and explain the natural predicate shared by the other three; report any alternate odd tile or predicate.'
            response_schema={'odd':'tile','predicate':'nonblank text','tile_explanations':'one per tile','alternate_predicates':[],'ambiguous':False}
        else:
            answer={'pairs':[{'members':sorted(self.token_map[x] for x in p['members']),'predicate':p['group_label']} for p in self.row['payload']['pairs']]}
            task='Match all eight tiles into four natural pairs; explain each pair and report any competing matching or ambiguous tile.'
            response_schema={'pairs':'four disjoint tile pairs','explanations':'four nonblank texts','alternate_matching':None,'ambiguous':False}
        self.public={'schema':'quick-pending-public-v1','challenge_id':challenge,'game':self.game,'mode':'regular_category','context':context,'tiles':tiles,'task':task,'response_schema':response_schema}
        self.private={'schema':'quick-pending-private-v1','challenge_id':challenge,'id':self.id,'runtime_id':self.runtime,'game':self.game,'mode':'regular_category','seed':7,'token_map':self.token_map,'expected_answer':answer,'native_initial_state':{'tiles':state_tiles,**context},'initial_get_equal':True,'isolated_overlay_only':True,'approval':None}
        if self.public_mutator:self.public_mutator(self.public)
        if self.private_mutator:self.private_mutator(self.private)
        public_raw=raw(self.public);private_raw=raw(self.private)
        self.dossier={'schema':'quick-pending-dossier-v1','id':self.id,'game':self.game,'status':'pending','provenance_mode':'source_backed','source_id':self.row['source_id'],'runtime_id':self.runtime,'record_sha256':m.quick_digest(self.row),'kg_sha256':bindings['kg_sha256'],'rubric_sha256':bindings['rubric_sha256'],'pending_sha256':pending_sha,'baseline_source_sha256':'a'*64,'bindings':bindings,'semantic_payload':self.row['payload'],'nodes':{n['id']:n for n in self.nodes},'category':self.row['category'],'difficulty':self.row['difficulty'],'public_projection_sha256':m.sha256(public_raw),'private_projection_sha256':m.sha256(private_raw),'screen':self.pending['screen'],'approval':None,'qualified':False,'qualification':m.QUICK_QUALIFICATION}
        if self.dossier_mutator:self.dossier_mutator(self.dossier)
        db={k:v for k,v in self.dossier.items() if k!='rubric_sha256'}
        self.dossier['review_binding']='sha256:'+m.quick_digest({'schema':'quick-pending-review-binding-v1','rubric_sha256':self.dossier['rubric_sha256'],'dossier':db})
        dossier_raw=raw(self.dossier)
        descriptor={'dossier_path':'dossiers/'+self.id+'.json','dossier_sha256':m.sha256(dossier_raw),'public_path':'public/'+challenge+'.json','private_path':'private/'+challenge+'.json',**{k:self.dossier[k] for k in ('id','game','review_binding','record_sha256','kg_sha256','rubric_sha256','status','provenance_mode','source_id','runtime_id','pending_sha256')}}
        rendered=[('pending.json',self.pending_raw),(descriptor['public_path'],public_raw),(descriptor['private_path'],private_raw),(descriptor['dossier_path'],dossier_raw)]
        self.bundle={'schema':'quick-pending-bundle-v1','qualified':False,'qualification':m.QUICK_QUALIFICATION,'index':{'schema':'quick-pending-index-v1','qualified':False,'approval':None,'pending_sha256':pending_sha,'descriptors':[descriptor]},'members':[{'path':p,'bytes':len(b),'sha256':m.sha256(b),'data':b.decode()} for p,b in rendered]}
        save(self.bundle_path,self.bundle)
        packages=[]
        for directory,fields in [('go-backend/cmd/cat-content-rail',{'GoFiles':['main.go']}),('go-backend/internal/contentrails',{'EmbedFiles':['sources/installed-authorities.json']})]:
            packages.append({'directory':directory,'files':{name:fields.get(name,[]) for name in m.GO_LIST_FILE_FIELDS}})
        paths=['go-backend/cmd/cat-content-rail/main.go','go-backend/go.mod','go-backend/go.sum','go-backend/internal/contentrails/sources/installed-authorities.json']
        self.proof={'schema':'cat-quick-native-build-proof-1','tool':self.tool_binding,'go_version':'go1.27.3','sdk_image':'sha256:'+'0'*64,'build_flags':['-trimpath','-mod=readonly','-buildvcs=false','-p=4'],'target':{'goos':'linux','goarch':'amd64','cgo_enabled':False},'inventory_sha256':m.quick_digest(self.inventory),'compiled_rubric_sha256':bindings['rubric_sha256'],'compiled_authority_sha256':m.sha256((root/'go-backend/internal/contentrails/sources/installed-authorities.json').read_bytes()),'module_files':['go-backend/go.mod','go-backend/go.sum'],'packages':packages,'source_inputs':[bound(root/p,p) for p in paths],'external_modules':[],'external_inputs':[],'module_verification':{'before':'all modules verified','after':'all modules verified'},'source_frame_sha256':'f'*64}
        save(self.proof_path,self.proof)
        self.args=SimpleNamespace(root=str(root),scratch_root=str(self.scratch),pending_bundle=str(self.bundle_path),pending_sha256=m.sha256(self.bundle_path.read_bytes()),native_tool=str(self.tool),native_tool_sha256=self.tool_binding['sha256'],native_build_proof=str(self.proof_path),native_build_proof_sha256=m.sha256(self.proof_path.read_bytes()),item_id=self.id,public_out=str(self.scratch/'public.json'),key_out=str(self.scratch/'key.json'),key=str(self.scratch/'key.json'),response=str(self.scratch/'response.json'),out=str(self.scratch/'comparison.json'))
        m.set_scratch_root(self.scratch)

    def mocked_native_replay(self,tool,args,directory):
        assert tool==self.tool
        assert args[:2]==['--root',str(self.root)]
        if '--pending-inventory' in args:return raw(self.inventory)
        assert '--prepare-pending' in args and '--source' not in args and '--write' not in args
        save(Path(args[args.index('--pending-out')+1]),self.bundle)
        return b'{"ok":true,"approval":null}\n'

    def response(self):
        r={'challenge_id':self.public['challenge_id'],'public_sha256':m.sha256(raw(self.public)),'game':self.game,'mode':'regular_category','ambiguous':False}
        if self.game=='intrusul':r.update(odd=self.private['expected_answer']['odd'],predicate='SYNTHETIC explanation, requires independent semantic review',tile_explanations={t['tile']:'SYNTHETIC explanation' for t in self.public['tiles']},alternate_predicates=[])
        else:r.update(pairs=[p['members'] for p in self.private['expected_answer']['pairs']],explanations=['SYNTHETIC explanation']*4,alternate_matching=None)
        return r


class QuickBlindBindingTests(unittest.TestCase):
    def fixture(self,game):
        temp=tempfile.TemporaryDirectory(prefix='quick-blind-unit-');self.addCleanup(temp.cleanup)
        return SyntheticNativeFixture(Path(temp.name),game)

    def build(self,f):
        with contextlib.redirect_stdout(io.StringIO()),patch.object(m,'quick_run',side_effect=f.mocked_native_replay):m.build_quick(f.args)

    def compare(self,f,response):
        save(Path(f.args.response),response)
        with contextlib.redirect_stdout(io.StringIO()),patch.object(m,'quick_run',side_effect=f.mocked_native_replay):m.compare_quick(f.args)
        return json.loads(Path(f.args.out).read_bytes())

    def test_synthetic_both_games_build_compare_deterministic_private_key_only(self):
        for game in m.QUICK_GAMES:
            with self.subTest(game=game):
                f=self.fixture(game);self.build(f)
                public=Path(f.args.public_out).read_bytes();key=json.loads(Path(f.args.key).read_bytes())
                self.assertEqual(public,raw(f.public));self.assertEqual(key['private_projection']['token_map'],f.token_map)
                for sentinel in ('AUTHOR','PRIVATE','aq92_','iq92_','pq92_','vi_','vp_','unit_node_','capture.html','packet.json'):
                    self.assertNotIn(sentinel,public.decode())
                result=self.compare(f,f.response())
                self.assertTrue(result['mechanical_match']);self.assertEqual(result['status'],'needs_human_semantic_checks');self.assertIsNone(result['approval'])
                self.assertFalse(result['details']['semantic_predicate_truth_verified' if game=='intrusul' else 'semantic_pair_truth_verified'])
                self.assertEqual(result['schema'],'cat-quick-blind-comparison-1')
                self.assertEqual(result['native_binding']['bundle']['sha256'],f.args.pending_sha256)
                self.assertEqual(result['native_binding']['native_build_proof']['sha256'],f.args.native_build_proof_sha256)
                self.assertEqual(result['key_binding']['sha256'],m.sha256(Path(f.args.key).read_bytes()))
                self.assertFalse(result['native_binding']['stock_screen']['complete'])
                self.assertEqual(len(result['native_binding']['stock_screen']['unresolved_quick_history']),13)
                before=copy.deepcopy(f.public);f.rebuild();self.assertEqual(f.public,before)
                self.assertFalse(f.pending['screen']['complete']);self.assertEqual(len(f.pending['screen']['unresolved_quick_history']),13)

    def test_correct_key_with_blank_nonstring_reasoning_filters_both_games(self):
        for game in m.QUICK_GAMES:
            for blank in (' ',None,False,[]):
                with self.subTest(game=game,blank=blank):
                    f=self.fixture(game);self.build(f);response=f.response()
                    if game=='intrusul':response['tile_explanations'][f.public['tiles'][0]['tile']]=blank
                    else:response['explanations'][0]=blank
                    result=self.compare(f,response);self.assertTrue(result['mechanical_match']);self.assertEqual(result['status'],'critic_filter_failure');self.assertIsNone(result['approval'])

    def test_native_display_casing_is_not_guessed_from_raw_kg_labels(self):
        for game in m.QUICK_GAMES:
            f=self.fixture(game)
            for node in f.nodes:
                node['label_ro']=node['label_ro'].lower()
                f.native_labels[node['id']]=node['label_ro'][0].upper()+node['label_ro'][1:]
            save(f.root/m.FIX/'kg_sample.json',{'kg_nodes':f.nodes,'kg_edges':[]});f.rebuild();self.build(f)
            self.assertNotEqual(f.public['tiles'][0]['text'],f.nodes[0]['label_ro'])
            result=self.compare(f,f.response());self.assertTrue(result['mechanical_match']);self.assertIsNone(result['approval'])

    def test_correct_odd_with_blank_predicate_never_passes_filter(self):
        f=self.fixture('intrusul');self.build(f);response=f.response();response['predicate']=' '
        result=self.compare(f,response);self.assertTrue(result['mechanical_match']);self.assertEqual(result['status'],'critic_filter_failure');self.assertIsNone(result['approval'])

    def test_duplicate_response_keys_and_edited_private_key_refuse(self):
        for game in m.QUICK_GAMES:
            f=self.fixture(game);self.build(f)
            save(Path(f.args.response),b'{"ambiguous":false,"ambiguous":false}')
            with self.assertRaisesRegex(ValueError,'duplicate JSON key'):m.compare_quick(f.args)
            save(Path(f.args.response),f.response())
            key=json.loads(Path(f.args.key).read_bytes());key['native_binding']['native_tool']['sha256']='0'*64;save(Path(f.args.key),key)
            with patch.object(m,'quick_run',side_effect=f.mocked_native_replay):
                with self.assertRaisesRegex(ValueError,'private key/current producer'):m.compare_quick(f.args)
            self.assertFalse(Path(f.args.out).exists())

    def test_explicit_plausible_alternates_and_ambiguity_filter_both_games(self):
        for game in m.QUICK_GAMES:
            for ambiguous in (False,True,0,None):
                with self.subTest(game=game,ambiguous=ambiguous):
                    f=self.fixture(game);self.build(f);response=f.response();response['ambiguous']=ambiguous
                    if game=='intrusul':response['alternate_predicates']=[{'odd':f.public['tiles'][0]['tile'],'predicate':'An equally natural alternate exact-sense grouping'}]
                    else:response['alternate_matching']=[list(reversed(p)) for p in response['pairs']]
                    result=self.compare(f,response);self.assertEqual(result['status'],'critic_filter_failure');self.assertIsNone(result['approval'])

    def test_wrong_but_well_formed_answer_never_approves(self):
        for game in m.QUICK_GAMES:
            f=self.fixture(game);self.build(f);response=f.response()
            if game=='intrusul':response['odd']=next(t['tile'] for t in f.public['tiles'] if t['tile']!=response['odd'])
            else:response['pairs'][0][0],response['pairs'][1][0]=response['pairs'][1][0],response['pairs'][0][0]
            result=self.compare(f,response);self.assertFalse(result['mechanical_match']);self.assertIsNone(result['approval'])

    def test_bad_response_challenge_public_game_mode_refuse_before_output(self):
        for game in m.QUICK_GAMES:
            for name,bad in [('challenge_id','wrong'),('public_sha256','0'*64),('game','contexto'),('mode','daily')]:
                with self.subTest(game=game,name=name):
                    f=self.fixture(game);self.build(f);response=f.response();response[name]=bad
                    with self.assertRaisesRegex(ValueError,'response challenge'):self.compare(f,response)
                    self.assertFalse(Path(f.args.out).exists())

    def test_wrong_missing_duplicate_unknown_tokens_and_reasoning_coverage_refuse(self):
        for game in m.QUICK_GAMES:
            for mutation in range(5):
                with self.subTest(game=game,mutation=mutation):
                    f=self.fixture(game);self.build(f);response=f.response()
                    if game=='intrusul':
                        if mutation==0:response['odd']='unknown'
                        elif mutation==1:del response['tile_explanations'][f.public['tiles'][0]['tile']]
                        elif mutation==2:response['tile_explanations']['unknown']='text'
                        elif mutation==3:del response['alternate_predicates']
                        else:response['odd']=['t0001']
                    else:
                        if mutation==0:response['pairs'][0][0]='unknown'
                        elif mutation==1:response['pairs'][0][0]=response['pairs'][1][0]
                        elif mutation==2:response['pairs'].pop()
                        elif mutation==3:response['explanations'].pop()
                        else:del response['alternate_matching']
                    with self.assertRaises(ValueError):self.compare(f,response)
                    self.assertFalse(Path(f.args.out).exists())

    def test_changed_public_bytes_refuse(self):
        for game in m.QUICK_GAMES:
            f=self.fixture(game);self.build(f);path=Path(f.args.public_out);path.write_bytes(path.read_bytes()+b' ')
            with self.assertRaisesRegex(ValueError,'public task'):self.compare(f,f.response())

    def test_whole_bundle_and_operator_build_receipt_pins_are_independent(self):
        for field in ('pending_sha256','native_tool_sha256','native_build_proof_sha256'):
            f=self.fixture('intrusul');setattr(f.args,field,'0'*64)
            with self.assertRaises(ValueError):self.build(f)
            self.assertFalse(Path(f.args.public_out).exists());self.assertFalse(Path(f.args.key_out).exists())

    def test_current_raw_kg_rubric_fullsource_inventory_holds_and_tool_drift_refuse(self):
        for game in m.QUICK_GAMES:
            for target in ('kg','rubric','source','registry','holds','raw','seal','evidence','capture','inventory','tool','consumer'):
                with self.subTest(game=game,target=target):
                    f=self.fixture(game)
                    path={'kg':f.root/m.FIX/'kg_sample.json','rubric':f.root/'docs/CRITIQUE_RUBRIC.md','source':f.root/'go-backend/cmd/cat-content-rail/main.go','registry':f.root/'docs/content-registry/registry.jsonl','holds':f.root/'docs/content-registry/exclusions.json','raw':f.packet_path,'seal':f.seal_path,'evidence':f.evidence_path,'capture':f.capture_path,'inventory':f.inventory_path,'tool':f.tool,'consumer':f.root/'scripts/miner/critic_blind.py'}[target]
                    path.write_bytes(path.read_bytes()+b' ')
                    with self.assertRaises(ValueError):self.build(f)
                    self.assertFalse(Path(f.args.public_out).exists())

    def test_full_rehashed_bundle_cannot_imply_current_native_preparation(self):
        for game in m.QUICK_GAMES:
            f=self.fixture(game)
            # Every supplied hash can be recomputed by an author. The trusted
            # producer still refuses the current compiled-rubric/source state.
            with patch.object(m,'quick_run',side_effect=ValueError('native quick: native replay refused: current compiled I/J rubric binding')):
                with self.assertRaisesRegex(ValueError,'compiled I/J'):m.build_quick(f.args)
            self.assertFalse(Path(f.args.public_out).exists());self.assertFalse(Path(f.args.key_out).exists())

    def test_native_replay_inventory_and_bundle_bytes_must_both_be_exact(self):
        for stage in ('inventory','bundle'):
            f=self.fixture('intrusul')
            def wrong(tool,args,directory):
                if '--pending-inventory' in args:
                    return raw({**f.inventory,'baseline_source_version':24}) if stage=='inventory' else raw(f.inventory)
                save(Path(args[-1]),raw(f.bundle)+b' ');return b'{}'
            with patch.object(m,'quick_run',side_effect=wrong):
                with self.assertRaises(ValueError):m.build_quick(f.args)
            self.assertFalse(Path(f.args.public_out).exists())

    def test_public_hint_answer_source_catalog_reviewer_sentinels_reject(self):
        for game in m.QUICK_GAMES:
            for name in ('hint','solution','source_id','runtime_id','reviewer','rationale'):
                with self.subTest(game=game,name=name):
                    f=self.fixture(game);f.public_mutator=lambda p:p.update({name:'REVIEWER_PRIVATE_SENTINEL'});f.rebuild()
                    with self.assertRaises(ValueError):self.build(f)
                    self.assertFalse(Path(f.args.public_out).exists())

    def test_hidden_predicate_or_author_trail_in_native_rendered_text_rejects(self):
        for game in m.QUICK_GAMES:
            for text in ('AUTHOR_RATIONALE_SENTINEL','https://example.test/AUTHOR_SOURCE_SENTINEL','aq92_synthetic_unit','PRIVATE_PREDICATE_SENTINEL' if game=='intrusul' else 'PRIVATE_PAIR_SENTINEL_0'):
                with self.subTest(game=game,text=text):
                    f=self.fixture(game);f.nodes[0]['label_ro']=text
                    save(f.root/m.FIX/'kg_sample.json',{'kg_nodes':f.nodes,'kg_edges':[]});f.rebuild()
                    with self.assertRaisesRegex(ValueError,'leakage'):self.build(f)

    def test_bad_game_namespace_mode_and_private_key_permutation_reject(self):
        for game in m.QUICK_GAMES:
            for change in ('public_game','public_mode','private_mode','private_key','private_tokens','native_tiles'):
                with self.subTest(game=game,change=change):
                    f=self.fixture(game)
                    if change=='public_game':f.public_mutator=lambda p:p.update(game='conexiuni')
                    elif change=='public_mode':f.public_mutator=lambda p:p.update(mode='daily')
                    elif change=='private_mode':f.private_mutator=lambda p:p.update(mode='daily')
                    elif change=='private_key':f.private_mutator=lambda p:p['expected_answer'].update({'odd':'t9999'} if game=='intrusul' else {'pairs':[]})
                    elif change=='private_tokens':f.private_mutator=lambda p:p['token_map'].update({next(iter(p['token_map'])):'t9999'})
                    else:f.private_mutator=lambda p:p['native_initial_state']['tiles'][0].update(label='SENTINEL')
                    f.rebuild()
                    with self.assertRaises(ValueError):self.build(f)
        f=self.fixture('intrusul');f.id='pq92_wrong_game';f.row['id']=f.id;f.rebuild()
        with self.assertRaisesRegex(ValueError,'namespace'):self.build(f)

    def test_stale_rendered_member_hash_and_private_projection_hash_reject(self):
        for game in m.QUICK_GAMES:
            for kind in ('member','private_hash','public_hash','raw_record','mixed_kg','mixed_tool'):
                with self.subTest(game=game,kind=kind):
                    f=self.fixture(game)
                    if kind=='member':f.bundle['members'][1]['sha256']='0'*64;save(f.bundle_path,f.bundle);f.args.pending_sha256=m.sha256(f.bundle_path.read_bytes())
                    else:
                        def mutate(d):
                            field={'private_hash':'private_projection_sha256','public_hash':'public_projection_sha256','raw_record':'record_sha256','mixed_kg':'kg_sha256'}.get(kind)
                            if field:d[field]='0'*64
                            else:d['bindings']={**d['bindings'],'tool_sha256':'0'*64}
                        f.dossier_mutator=mutate;f.rebuild()
                    with self.assertRaises(ValueError):self.build(f)

    def test_unknown_keys_duplicate_json_and_author_raw_envelope_refuse(self):
        f=self.fixture('intrusul')
        for data in (b'{"schema":"x","schema":"y"}',b'{"x":1e400}',b'{} {}',raw(f.packet)):
            save(f.bundle_path,data);f.args.pending_sha256=m.sha256(data)
            with self.assertRaises(ValueError):self.build(f)
        f=self.fixture('intrusul');f.row['approval']=True;f.rebuild()
        with self.assertRaises(ValueError):self.build(f)

    def test_sourcebacked_reference_cap_and_kgonly_mode_cannot_be_relaxed(self):
        for game in m.QUICK_GAMES:
            for count in (0,17):
                f=self.fixture(game);f.row['sources']=['https://example.test/unit/'+str(i) for i in range(count)];f.rebuild()
                with self.assertRaisesRegex(ValueError,'source-backed'):self.build(f)
            f=self.fixture(game);f.pending_mutator=lambda p:p.update(provenance_mode='kg_only');f.rebuild()
            with self.assertRaises(ValueError):self.build(f)

    def test_compiled_receipt_sdk_flags_closure_membership_and_external_proof_refuse(self):
        for kind in ('sdk','flags','source_frame','module_verify','closure_missing','closure_extra','external_unknown','external_duplicate','external_missing_mod','sum_drift'):
            with self.subTest(kind=kind):
                f=self.fixture('intrusul');proof=copy.deepcopy(f.proof)
                if kind=='sdk':proof['sdk_image']='latest'
                elif kind=='flags':proof['build_flags'].append('-tags=unreviewed')
                elif kind=='source_frame':proof['source_frame_sha256']=''
                elif kind=='module_verify':proof['module_verification']['after']='skipped'
                elif kind=='closure_missing':proof['source_inputs'].pop()
                elif kind=='closure_extra':proof['packages'][0]['files']['EmbedFiles']=['new-secret.json']
                elif kind=='external_unknown':proof['external_inputs']=[{'module':'unknown','path':'go.mod','bytes':1,'sha256':'0'*64}]
                else:
                    mod={'path':'example.test/dep','version':'v1.2.3','sum':'h1:'+'A'*43+'=','go_mod_sum':'h1:'+'B'*43+'='}
                    sums=(mod['path']+' '+mod['version']+' '+mod['sum']+'\n'+mod['path']+' '+mod['version']+'/go.mod '+mod['go_mod_sum']+'\n').encode()
                    # Direct dependency-proof test isolates structure/go.sum;
                    # rebuilding whole inventory is separately tested above.
                    save(f.root/'go-backend/go.sum',sums);proof['external_modules']=[mod]
                    row={'module':mod['path'],'path':'go.mod','bytes':42,'sha256':'0'*64}
                    proof['external_inputs']=[row,row] if kind=='external_duplicate' else [{**row,'path':'dep.go'}] if kind=='external_missing_mod' else [row]
                    if kind=='sum_drift':proof['external_modules'][0]['sum']='h1:'+'C'*43+'='
                    with self.assertRaises(ValueError):m.quick_external_proof(proof,f.root)
                    continue
                save(f.proof_path,proof);f.args.native_build_proof_sha256=m.sha256(f.proof_path.read_bytes())
                with self.assertRaises(ValueError):self.build(f)

    def test_document_fixture_tool_caps_and_no_source_override_cli(self):
        self.assertEqual(m.QUICK_EXTERNAL_LIMIT,64<<20);self.assertEqual(m.MAX_BYTES,64<<20)
        f=self.fixture('intrusul');oversized=f.scratch/'oversized.json'
        with oversized.open('wb') as file:file.truncate((64<<20)+1)
        with self.assertRaisesRegex(ValueError,'cap'):m.quick_read(oversized)
        with oversized.open('wb') as file:file.truncate((256<<20)+1)
        with self.assertRaisesRegex(ValueError,'cap'):m.quick_tool_hash(oversized)
        oversized.unlink()
        import subprocess,sys
        arguments=['--root',f.args.root,'--pending-bundle',f.args.pending_bundle,'--pending-sha256',f.args.pending_sha256,'--item-id',f.args.item_id,'--native-tool',f.args.native_tool,'--native-tool-sha256',f.args.native_tool_sha256,'--native-build-proof',f.args.native_build_proof,'--native-build-proof-sha256',f.args.native_build_proof_sha256,'--public-out',f.args.public_out,'--key-out',f.args.key_out,'--scratch-root',f.args.scratch_root]
        result=subprocess.run([sys.executable,'-I','-B',str(HERE/'scripts/miner/critic_blind.py'),'build-quick',*arguments,'--source','bad'],capture_output=True,text=True)
        self.assertIn('unrecognized arguments: --source',result.stderr)
        self.assertNotEqual(result.returncode,0);self.assertFalse(Path(f.args.public_out).exists())

    def test_external_aggregate_64mib_bound_without_large_artifact_retention(self):
        # Exercise the exact aggregate limit with synthetic len-only read bytes;
        # no fake bytes can reach a native call or be claimed producer evidence.
        f=self.fixture('intrusul');original=m.quick_bound_file
        class DeclaredBytes(bytes):
            def __len__(self):return 32<<20
        def large(binding,root=None,limit=m.QUICK_MEMBER_LIMIT):
            if root is None:return DeclaredBytes(b'unit')
            return original(binding,root,limit)
        with patch.object(m,'quick_bound_file',side_effect=large),patch.object(m,'quick_run',side_effect=AssertionError('must refuse before native call')):
            with self.assertRaisesRegex(ValueError,'aggregate exceeds 64 MiB'):m.build_quick(f.args)

    def test_native_refusal_propagates_source_and_fixture_caps_without_output(self):
        for reason in ('full quick authored source exceeds 4 MiB','quick pending catalog projection exceeds 2 MiB','full quick authored board cap'):
            f=self.fixture('perechi')
            with patch.object(m,'quick_run',side_effect=ValueError('native quick: native replay refused: '+reason)):
                with self.assertRaisesRegex(ValueError,'native replay refused'):m.build_quick(f.args)
            self.assertFalse(Path(f.args.public_out).exists());self.assertFalse(Path(f.args.key_out).exists())

    def test_declared_compiled_embeds_outside_inventory_stay_fresh_for_build_and_compare(self):
        compiled=[('go-backend/internal/accounts','schema.sql'),('go-backend/internal/httpapi','embedfs/index.html'),('go-backend/internal/catalog','testdata/catalog.json')]
        for game in m.QUICK_GAMES:
            for operation in ('build','compare'):
                for directory,name in compiled:
                    with self.subTest(game=game,operation=operation,compiled_member=name):
                        f=self.fixture(game);relative=directory+'/'+name
                        path=save(f.root/relative,b'original compiled embed body\n')
                        self.assertNotIn(relative,{row['path'] for row in f.inventory['members']})
                        f.proof['packages'].append({'directory':directory,'files':{field:[name] if field=='EmbedFiles' else [] for field in m.GO_LIST_FILE_FIELDS}})
                        f.proof['packages'].sort(key=lambda row:row['directory'])
                        f.proof['source_inputs'].append(bound(path,relative));f.proof['source_inputs'].sort(key=lambda row:row['path'])
                        save(f.proof_path,f.proof);f.args.native_build_proof_sha256=m.sha256(f.proof_path.read_bytes())
                        if operation=='compare':self.build(f);save(Path(f.args.response),f.response())
                        before=m.sha256(path.read_bytes());mutated=False
                        def replay(tool,args,directory):
                            nonlocal mutated
                            result=f.mocked_native_replay(tool,args,directory)
                            if '--prepare-pending' in args:path.write_bytes(b'modified compiled embed body\n');mutated=True
                            return result
                        with contextlib.redirect_stdout(io.StringIO()),patch.object(m,'quick_run',side_effect=replay):
                            with self.assertRaisesRegex(ValueError,'input '+relative):
                                (m.build_quick if operation=='build' else m.compare_quick)(f.args)
                        self.assertTrue(mutated);self.assertNotEqual(before,m.sha256(path.read_bytes()))
                        if operation=='build':
                            self.assertFalse(Path(f.args.public_out).exists());self.assertFalse(Path(f.args.key_out).exists())
                        else:self.assertFalse(Path(f.args.out).exists())

    def test_retained_comparison_evidence_cannot_change_during_prepare(self):
        for game in m.QUICK_GAMES:
            for kind in ('key','response'):
                with self.subTest(game=game,retained_input=kind):
                    f=self.fixture(game);self.build(f);save(Path(f.args.response),f.response())
                    path=Path(f.args.key if kind=='key' else f.args.response)
                    before=path.read_bytes();changed=json.loads(before)
                    if kind=='key':changed['approval']='edited while native replay runs'
                    else:changed['ambiguous']=True
                    after=raw(changed);mutated=False
                    def replay(tool,args,directory):
                        nonlocal mutated
                        result=f.mocked_native_replay(tool,args,directory)
                        if '--prepare-pending' in args:path.write_bytes(after);mutated=True
                        return result
                    with contextlib.redirect_stdout(io.StringIO()),patch.object(m,'quick_run',side_effect=replay):
                        with self.assertRaisesRegex(ValueError,'retained .* changed during comparison'):m.compare_quick(f.args)
                    self.assertTrue(mutated);self.assertEqual(path.read_bytes(),after);self.assertNotEqual(before,after)
                    self.assertFalse(Path(f.args.out).exists())


if __name__=='__main__':unittest.main()
