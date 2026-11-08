#!/usr/bin/env python3
"""Bounded graph prospects for all six games; never an importer or approval tool."""
import sys
sys.dont_write_bytecode=True
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import itertools
from common import *

TYPED_HUBS={'is_a','part_of','located_in','associated_with'}

class Exhausted(Exception):pass

class Budget:
    def __init__(self,limit):self.limit,self.used=limit,0
    def tick(self):
        if self.used>=self.limit:raise Exhausted()
        self.used+=1


def all_matchings(ids):
    if not ids:
        yield []
    else:
        a=ids[0]
        for i in range(1,len(ids)):
            for rest in all_matchings(ids[1:i]+ids[i+1:]):
                yield [(a,ids[i])]+rest


class Miner:
    def __init__(self,repo,index,per_cell,budget,starts):
        self.repo,self.index,self.per_cell,self.limit,self.starts=repo,index,per_cell,budget,starts
        self.g=Graph(repo)
        self.rows,_,_=inventory(repo)
        self.known={signature(row['game'],row) for row in self.rows}
        self.known.update(row['signature'] for row in index['signatures']+index['tombstones'])
        self.seen=set()
        self.cx_quad_triples=set()
        self.cx_tile_sets=[]
        conexiuni_debt=repo.data(FIX+'conexiuni_rejection_tombstones.json')['items'].values()
        lant_debt=repo.data(FIX+'lant_rejection_tombstones.json')['items'].values()
        self.known.update(signature('conexiuni',row) for row in conexiuni_debt)
        self.known.update(signature('lant',row) for row in lant_debt)
        for row in itertools.chain((row for row in self.rows if row['game']=='conexiuni'),conexiuni_debt):
            self.remember_conexiuni(row['groups'].values())
        self.pair_tile_sets={
            tuple(sorted(tile for pair in row.get('payload',row)['pairs'] for tile in pair['members']))
            for row in self.rows if row['game']=='perechi'
        }
        self.pair_tile_sets.update(tuple(row['tile_set']) for row in index['signatures']
                                   if row['game']=='perechi')
        self.hubs=collections.defaultdict(set)
        for e in self.g.edges:
            if e.get('is_distractor') or e['relation'] not in TYPED_HUBS:continue
            child,hub=e['src_id'],e['dst_id']
            self.hubs[(e['relation'],hub,self.g.nodes[child]['node_type'])].add(child)
        self.hubs={k:sorted(v) for k,v in sorted(self.hubs.items())}
        self.captions=None

    def remember_conexiuni(self,groups):
        self.cx_quad_triples.update(triple for group in groups
                                    for triple in itertools.combinations(sorted(group),3))
        self.cx_tile_sets.append(frozenset(itertools.chain.from_iterable(groups)))

    def known_conexiuni_quad(self,group):
        return any(triple in self.cx_quad_triples for triple in itertools.combinations(sorted(group),3))

    def candidates(self,game,category,difficulty):
        self.budget=Budget(self.limit)
        self.results=[]
        self.rejects=collections.Counter()
        self.game,self.category,self.difficulty=game,category,difficulty
        method=getattr(self,game)
        exhausted=False
        try:method()
        except Exhausted:exhausted=True
        return {'cell':f'{game}:{category}:{difficulty}','attempts':self.budget.used,'budget_limit':self.limit,
                'budget_exhausted':exhausted,'requested':self.per_cell,'shortfall':self.per_cell-len(self.results),
                'reject_counts':dict(sorted(self.rejects.items())),'candidates':self.results,
                'search_complete':False,'note':'Deterministic bounded sample; shortfall does not prove the cell has no possible board.'}

    def nodes(self):
        return sorted((id_ for id_,n in self.g.nodes.items() if n['category']==self.category),key=lambda id_:(-self.g.nodes[id_].get('salience',0),id_))

    def emit(self,payload,metrics,refs,required):
        row={'game':self.game,'payload':payload}
        sig=signature(self.game,row)
        if sig in self.known or sig in self.seen:
            self.rejects['existing_or_tombstoned_signature']+=1;return False
        if self.game=='conexiuni':
            groups=partitions(payload['groups'].values())
            if any(self.known_conexiuni_quad(group) for group in groups):
                self.rejects['conexiuni_three_tile_quad_overlap']+=1;return False
            tiles=frozenset(itertools.chain.from_iterable(groups))
            if any(len(tiles & existing)>=8 for existing in self.cx_tile_sets):
                self.rejects['conexiuni_eight_tile_board_overlap']+=1;return False
            self.remember_conexiuni(groups)
        if self.game=='perechi' and tuple(sorted(x for pair in payload['pairs'] for x in pair['members'])) in self.pair_tile_sets:
            self.rejects['existing_perechi_tile_set']+=1;return False
        self.seen.add(sig)
        id_='prospect_'+self.game+'_'+sig[:16]
        self.results.append({'id':id_,'status':'unapproved','game':self.game,'category':self.category,'difficulty':self.difficulty,
            'payload':payload,'signature':sig,'metrics':metrics,'source_refs':sorted(set(refs)),
            'compat_status':'manual_required',
            'required_checks':required+['M2 complete relevant unknown-expression and owner-hold screen','M3 native validation/lint','M4 independent blind gameplay critic','M6/M7 independent review and full cascade'],
            'source_kind':'current_KG_only','no_vocabulary_change':True})
        return len(self.results)>=self.per_cell

    def lant(self):
        if self.captions is None:
            bundle=self.repo.data('go-backend/internal/content/bundled.json')
            self.captions=bundle.get('lant_captions',{})
        ranges={'usor':(2,2),'normal':(3,4),'greu':(4,6)}
        low,high=ranges[self.difficulty]
        for start in self.nodes()[:self.starts]:
            dist=self.g.bfs(start,depth=high)
            targets=[x for x in self.nodes() if low<=dist.get(x,-1)<=high]
            for target in targets:
                self.budget.tick()
                par=dist[target]
                back=self.g.bfs(target,reverse=True,depth=par)
                first=[x for x in self.g.adj[start] if back.get(x)==par-1]
                layers=[[x for x in sorted(dist) if dist[x]==d and dist[x]+back.get(x,100000)==par] for d in range(1,par)]
                if len(first)<2 or any(len(layer)<2 for layer in layers):
                    self.rejects['insufficient_shortest_path_choices_or_width']+=1;continue
                optimal_edges=[(a,b,e) for a in sorted(dist) for b,e in self.g.adj[a].items() if dist[a]+1+back.get(b,100000)==par]
                missing=[(a,b) for a,b,e in optimal_edges if not self.captions.get(a+'\0'+b)]
                if missing:
                    self.rejects['missing_bundled_optimal_edge_caption']+=1;continue
                route=[start]
                while route[-1]!=target:
                    a=route[-1]
                    route.append(next(b for b in sorted(self.g.adj[a]) if back.get(b)==back[a]-1))
                route_edges=[self.g.adj[a][b] for a,b in zip(route,route[1:])]
                typed=sum(e['relation']!='related_to' for e in route_edges)/par
                steps=[{'from':a,'to':b,'caption':self.captions[a+'\0'+b],'relation':self.g.adj[a][b]['relation']} for a,b in zip(route,route[1:])]
                metrics={'raw_directed_bfs_optimal':par,'shortest_first_hops':len(first),'shortest_layer_widths':[len(x) for x in layers],
                         'optimal_dag_edges':len(optimal_edges),'captioned_optimal_dag_edges':len(optimal_edges),
                         'witness_route':route,'witness_steps':steps,'typed_ratio':typed,
                         'typed_definition':'relation != related_to; proposed >=0.50 is WARN only',
                         'warn_typed_ratio_below_050':typed<.5,'generic_caption_edges':sum(self.captions[a+'\0'+b]=='legătură directă' for a,b,e in optimal_edges),
                         'caption_qualification':'Bundled caption existence only; semantic fairness and live export freshness unverified.'}
                if self.emit({'start':start,'target':target,'optimal':par},metrics,[self.g.edge_ref(e) for e in route_edges],['HTTP caption-only play to target within par+2; explain every step','Re-derive BFS after any class-G landing']):return

    def contexto(self):
        existing={r['target'] for r in self.rows if r['game']=='contexto'}
        for target in self.nodes():
            self.budget.tick()
            if target in existing:
                self.rejects['existing_cald_target']+=1;continue
            incoming=len(self.g.rev[target])
            if incoming<5:
                self.rejects['raw_predecessors_below_5']+=1;continue
            distances=self.g.bfs(target,reverse=True)
            reachable=len(distances)-1
            if reachable<120:
                self.rejects['raw_reverse_reachable_below_120']+=1;continue
            n=self.g.nodes[target]
            metrics={'raw_main_graph_predecessors':incoming,'raw_reverse_reachable':reachable,'salience':n.get('salience'),
                     'responsive':None,'native_reachable':None,'difficulty_qualified':False,
                     'warn_gastronomie_freeze':self.category=='gastronomie','native_floor_unverified':'raw graph reachability is not Cald responsive/projection reachability'}
            if self.emit({'target':target},metrics,[self.repo.cite(FIX+'kg_sample.json',json.dumps(target))],['Native reachable>=120 and responsive>=40','Native contexto_incoming_floor and salience_floor','Five blind openers with >=1 within two hops; one dominant sense']):return

    def quads(self):
        groups=[]
        for key,members in self.hubs.items():
            local=[x for x in members if self.g.nodes[x]['category']==self.category]
            if len(local)<4:continue
            for quad in itertools.islice(itertools.combinations(local,4),8):
                self.budget.tick()
                if self.known_conexiuni_quad(quad):
                    self.rejects['conexiuni_three_tile_quad_overlap']+=1;continue
                groups.append((key,quad))
                if len(groups)>=128:return groups
        return groups

    def conexiuni(self):
        quads=self.quads()
        for i,(key,quad) in enumerate(quads):
            selected=[(key,quad)];used=set(quad)
            for other in quads[i+1:]+quads[:i]:
                self.budget.tick()
                if not used.intersection(other[1]) and all(other[0][1]!=x[0][1] for x in selected):
                    selected.append(other);used.update(other[1])
                if len(selected)==4:break
            if len(selected)!=4:continue
            groups={'g'+str(k+1):list(q) for k,(_,q) in enumerate(selected)}
            cross=[]
            for (_,left),(_,right) in itertools.combinations(selected,2):
                for a,b in itertools.product(left,right):
                    if self.g.undirected_strength(a,b)>0:cross.append([a,b])
            band=(0,1) if self.difficulty=='usor' else (1,3)
            refs=[]
            for (relation,hub,_),q in selected:
                refs.extend(self.g.edge_ref(e) for e in self.g.edges if e['relation']==relation and e['src_id'] in q and e['dst_id']==hub and not e.get('is_distractor'))
            metrics={'typed_hubs':[{'relation':k[0],'hub':k[1],'member_type':k[2]} for k,q in selected],
                     'cross_links_count':len(cross),'cross_links':cross,'proposed_cross_link_band':list(band),
                     'warn_cross_link_band':not band[0]<=len(cross)<=band[1],
                     'not_evaluated':['tile_fairness','red_herring_budget','member_overuse','natural predicate uniqueness']}
            # Labels stay unauthored; prospects must be completed before a native candidate file.
            if self.emit({'groups':groups,'group_labels':{k:None for k in groups},'order':sorted(used)},metrics,refs,['Author and source four precise group predicates','All strict Conexiuni checks FAIL-clean','Blind solve 16 shuffled tiles, no alternative partition, 3 recognizable groups']):return

    def intrusul(self):
        for key,members in self.hubs.items():
            self.budget.tick()
            relation,hub,node_type=key
            local=[x for x in members if self.g.nodes[x]['category']==self.category]
            if len(local)<3:continue
            sibling=[]
            parents={b for b,e in self.g.adj[hub].items() if e['relation'] in TYPED_HUBS}
            if not parents:continue
            for other,items in self.hubs.items():
                self.budget.tick()
                if other[0]!=relation or other[1]==hub or other[2]!=node_type:continue
                other_parents={b for b,e in self.g.adj[other[1]].items() if e['relation'] in TYPED_HUBS}
                shared=parents&other_parents
                if shared:
                    sibling.extend((x,other[1],sorted(shared)) for x in items if self.g.nodes[x]['category']==self.category)
            for trio in itertools.islice(itertools.combinations(local,3),64):
                links=[self.g.undirected_strength(a,b) for a,b in itertools.combinations(trio,2)]
                if sum(w>=.6 for w in links)<2:continue
                for odd,other,shared in sorted(sibling):
                    self.budget.tick()
                    if odd in trio or any(self.g.undirected_strength(odd,x)>0 for x in trio):continue
                    payload={'members':list(trio),'intruder':odd,'group_label':None}
                    metrics={'member_link_strengths':links,'intruder_real_member_links':0,'member_type':node_type,
                             'hub':hub,'sibling_hub':other,'hub_common_typed_parents':shared,'hub_relation':relation,
                             'predicate_qualified':False}
                    refs=[self.repo.cite(FIX+'kg_sample.json',json.dumps(x)) for x in trio+(odd,)]
                    if self.emit(payload,metrics,refs,['Author/source natural group predicate; no invented sibling membership','Quick shape: 3 members + distinct intruder','Blind odd-one-out AND natural predicate; reject alternate plausible odd tile']):return

    def perechi(self):
        nodes=set(self.nodes())
        edges=[]
        real_pairs={tuple(sorted((a,b))) for a in nodes for b in self.g.adj[a] if b in nodes and a!=b}
        for a,b in sorted(real_pairs):
            w=self.g.undirected_strength(a,b)
            if w>=.6:edges.append((a,b,w))
        edges.sort(key=lambda r:(-r[2],r[0],r[1]))
        edges=edges[:512]
        for i,edge in enumerate(edges):
            chosen=[edge];used=set(edge[:2])
            for other in edges[i+1:]+edges[:i]:
                self.budget.tick()
                if not used.intersection(other[:2]):chosen.append(other);used.update(other[:2])
                if len(chosen)==4:break
            if len(chosen)!=4:continue
            intended=partitions(e[:2] for e in chosen)
            weights=[]
            for matching in all_matchings(sorted(used)):
                score=sum(self.g.undirected_strength(a,b) for a,b in matching)
                weights.append((round(score,9),partitions(matching)))
            weights.sort(key=lambda x:(-x[0],x[1]))
            if weights[0][1]!=intended or weights[0][0]<=weights[1][0]+1e-9:
                self.rejects['not_unique_maximum_weight_matching']+=1;continue
            intended_edges={tuple(pair) for pair in intended}
            cross=[(a,b,self.g.undirected_strength(a,b)) for a,b in itertools.combinations(sorted(used),2) if (a,b) not in intended_edges]
            if any(w>=.6 for a,b,w in cross):
                self.rejects['cross_link_at_least_060']+=1;continue
            margin=round(weights[0][0]-weights[1][0],9)
            payload={'pairs':[{'members':list(pair),'group_label':None} for pair in intended]}
            metrics={'matchings_evaluated':len(weights),'intended_weight':weights[0][0],'runner_up_weight':weights[1][0],
                     'margin':margin,'warn_margin_below_015':margin<.15,'cross_links_tested':len(cross),
                     'real_cross_links':sum(w>0 for a,b,w in cross),'starter_zero_cross_link_screen':not any(w>0 for a,b,w in cross),
                     'weights_definition':'max strength of either real directed link; no missing-link penalty; semantic uniqueness remains unproved'}
            refs=[self.g.edge_ref(self.g.adj[a].get(b) or self.g.adj[b][a]) for a,b,w in chosen]
            if self.emit(payload,metrics,refs,['Author/source four natural pair predicates','Blind match all eight tiles; reject different matching or ambiguous tile']):return

    def alchimie(self):
        # A graph-neighborhood seed proposal is not an Alchimie recipe projection.
        # No pair->result rule or exact par may be inferred from ordinary KG edges.
        for target in self.nodes()[:self.starts]:
            self.budget.tick()
            back=self.g.bfs(target,reverse=True,depth=3)
            seeds=sorted((x for x,d in back.items() if 1<=d<=3 and self.g.nodes[x]['category']==self.category),key=lambda x:(-self.g.nodes[x].get('salience',0),back[x],x))
            if len(seeds)<5:
                self.rejects['fewer_than_5_local_seed_prospects']+=1;continue
            for offset in range(min(8,len(seeds)-4)):
                self.budget.tick()
                selected=sorted(seeds[offset:offset+min(7,len(seeds)-offset)])
                if len(selected)<5:continue
                metrics={'raw_seed_to_target_hops':{x:back[x] for x in selected},'native_projection':None,
                         'exact_par':None,'productive_openings':None,'productive_pair_ratio':None,
                         'limitation':'Neighborhood prospect only. Raw graph reachability does not establish a craftable pair, a closure, exact par or even solvability.'}
                payload={'seeds':selected,'target':target,'target_depth':None}
                refs=[self.repo.cite(FIX+'kg_sample.json',json.dumps(x)) for x in selected+[target]]
                if self.emit(payload,metrics,refs,['Native audit-projections before M3; discard if no valid closure','Exact par, >=2 productive openings, inferable target, no free pair','Proposed productive-pair cap ~40% WARN; own Alchimie review batch']):return


def main():
    p=argparse.ArgumentParser(description=__doc__)
    add_scratch_argument(p)
    p.add_argument('--root',required=True)
    p.add_argument('--compat',required=True)
    p.add_argument('--cell',action='append',required=True,help='GAME:CATEGORY:DIFFICULTY, repeated; cx/ct/lt/al/iq/pq accepted')
    p.add_argument('--per-cell',type=int,default=3)
    p.add_argument('--budget',type=int,default=4000,help='candidate trials per cell, never runtime minutes')
    p.add_argument('--max-starts',type=int,default=64)
    p.add_argument('--out',required=True)
    a=p.parse_args()
    set_scratch_root(a.scratch_root)
    if not 1<=a.per_cell<=12 or not 1<=a.budget<=20000 or not 1<=a.max_starts<=256 or len(a.cell)>24:fail('bounds: per-cell 1..12, budget 1..20000, starts 1..256, cells <=24')
    repo=Repo(a.root)
    compat_path=scratch(a.compat)
    index_data=read_regular(compat_path)
    index=json_object(index_data)
    if index.get('schema')!='cat-v2-compat-index-1':fail('wrong compatibility schema')
    for binding in index['source_bindings']:
        if hashlib.sha256(repo.read(binding['path'])).hexdigest()!=binding['sha256']:fail('stale compat binding: '+binding['path'])
    for binding in index.get('external_bindings',[]):
        path=repo_or_scratch(binding['path'],repo)
        if digest_file(path)!=binding['sha256']:fail('stale explicit stock binding: '+str(path))
    miner=Miner(repo,index,a.per_cell,a.budget,a.max_starts)
    cells=[]
    seen=set()
    for cell in a.cell:
        parts=cell.split(':')
        if len(parts)!=3:fail('cell must be GAME:CATEGORY:DIFFICULTY')
        game,category,difficulty=parts;game=ALIASES.get(game,game)
        if game not in GAMES or difficulty not in DIFFICULTIES or not any(n['category']==category for n in miner.g.nodes.values()):fail('unknown cell: '+cell)
        key=(game,category,difficulty)
        if key in seen:fail('duplicate requested cell')
        seen.add(key)
        cells.append(miner.candidates(*key))
    out={'schema':'cat-v2-mining-1','status':'unapproved_prospects','cells':cells,
         'compat_binding':{'path':str(compat_path),'sha256':sha256(index_data),'unresolved_expressions':len(index['unresolved'])},
         'limits':{'candidate_trials_per_cell':a.budget,'max_endpoint_starts':a.max_starts,'max_quad_prospects':128,'quads_per_hub':8,'max_matching_edges':512},
         'warning':'No factual source, semantic predicate, runtime qualification, approval or reservation is created. Missing labels/target_depth require authoring after mining. Alchimie yields neighborhood prospects only and cannot pass without native audit-projections.',
         'graph_semantics':'Real (non-distractor) directed edges, reverse only for bidirectional=true, max-strength duplicate winner, source-order tie. Lanț BFS follows these exact raw graph transitions.',
         **repo.provenance()}
    write_json(a.out,out)
    print(json.dumps({'out':str(scratch(a.out)),'cells':len(cells),'prospects':sum(len(r['candidates']) for r in cells),'status':out['status']},sort_keys=True))

if __name__=='__main__':run(main)
