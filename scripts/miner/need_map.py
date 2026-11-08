#!/usr/bin/env python3
"""Demand map for the live four pack games plus both quick catalogs."""
import sys
sys.dont_write_bytecode = True
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import *


def main():
    p = argparse.ArgumentParser(description=__doc__)
    add_scratch_argument(p)
    p.add_argument('--root', required=True)
    p.add_argument('--out', required=True)
    p.add_argument('--target', type=int, default=4)
    a = p.parse_args()
    set_scratch_root(a.scratch_root)
    if not 1 <= a.target <= 100:
        fail('target must be 1..100')
    repo = Repo(a.root)
    rows, held, quick_held = inventory(repo)
    for path in ('go-backend/internal/pack/pack.go', 'go-backend/internal/catalog/catalog.go', 'go-backend/internal/contentbuild/build.go', 'go-backend/internal/contentops/rank.go'):
        repo.read(path)
    kg = repo.data(FIX+'kg_sample.json')
    cats = sorted({n['category'] for n in kg['kg_nodes']} | {r['category'] for r in rows})
    cells = []
    for game in GAMES:
        for category in cats:
            for difficulty in DIFFICULTIES:
                group = [r for r in rows if (r['game'], r['category'], r['difficulty']) == (game, category, difficulty)]
                free = [r for r in group if not r['held']]
                if game in PACK_GAMES:
                    elig = [r for r in free if r['status']=='approved' and r['pilot_eligible']]
                    approved = sum(r.get('status')=='approved' for r in group)
                    starter = []
                    shelf = 'ranked_pilot_eligible'
                else:
                    preferred = [r for r in free if r['standard_score'] >= 55]
                    elig = preferred or free
                    approved = None  # Catalog authority is not a pack status field.
                    starter_pool = [r for r in free if r['starter_eligible']]
                    starter_preferred = [r for r in starter_pool if r['standard_score'] >= 55]
                    starter = starter_preferred or starter_pool
                    shelf = 'preferred_standard' if preferred else 'fallback_standard'
                cells.append({'game':game,'category':category,'difficulty':difficulty,'target':a.target,
                    'total':len(group),'approved':approved,'held':len(group)-len(free),'eligible':len(elig),
                    'starter_eligible':len(starter) if game not in PACK_GAMES else None,
                    'distinct_eligible_sources':len({r.get('source_id', r['id']) for r in elig}),
                    'deficit':max(0,a.target-len(elig)),'shelf':shelf,
                    'ids':{'eligible':sorted(r['id'] for r in elig),'held':sorted(r['id'] for r in group if r['held'])}})
    out = {'schema':'cat-v2-need-map-1','target':a.target,'categories':cats,
        'eligibility_definition':{
          'pack':'approved AND shipped board_rankings_v37.pilot_eligible=true AND not in owner demotion/reserve manifests; does not recompute lint',
          'quick':'union of derived_catalog_v38.boards + quick_games_v92.boards minus release_reserve_v1.quick IDs; for this exact category/difficulty prefer standard_score>=55 if nonempty, else all; mirrors catalog preferredShelf',
          'starter':'quick starter_eligible=true, then same preferredShelf by standard_score; separate from standard demand',
          'approved_null':'quick catalogs have no approved status; null is deliberate',
          'runtime_limit':'No source authority, stale digest, resolver, current-lint, serving or HTTP qualification is inferred.'},
        'holds':[{'id':k,'refs':v} for k,v in sorted(held.items())]+[{'id':k,'refs':[v]} for k,v in sorted(quick_held.items())],
        'cells':cells,'priority':[{k:r[k] for k in ('game','category','difficulty','eligible','deficit')} for r in sorted(cells,key=lambda r:(r['eligible'],-r['deficit'],r['game'],r['category'],DIFFICULTIES.index(r['difficulty']))) if r['deficit']],
        'summary':{'cells':len(cells),'deficient_cells':sum(r['deficit']>0 for r in cells),'eligible_by_game':{g:sum(r['eligible'] for r in cells if r['game']==g) for g in GAMES}},
        **repo.provenance()}
    write_json(a.out,out)
    print(json.dumps({'out':str(scratch(a.out)),**out['summary']},sort_keys=True))

if __name__ == '__main__':
    run(main)
