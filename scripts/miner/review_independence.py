#!/usr/bin/env python3
"""Audit V4 review sidecars and captured source hashes.

The seal supplies author, sealed_at, unsealed_at and urls. Each envelope
supplies reviewer, role (factual or quality), review_path, review_sha256,
signed_at, first_peer_read_at, child_safe_by_item and reviewer_chosen_sources.
Source choices carry url, chosen_by, fetched_by_role, capture_path and
capture_sha256 and fetched_at. The pinned frozen manifest supplies items
(mapping IDs to kg_only or source_backed) and receipts (first capture per
normalized URL, with url, capture_sha256, fetched_by_role and fetched_at).
The M1–M5 index supplies distinct artifacts with stage, path and sha256.
The caller verifies the manifest's provenance and access receipts.
This sidecar checks the initial review. Native promotion has a separate
verifier contract that requires genuine HTTP(S) evidence for every item.
"""
import sys
sys.dont_write_bytecode = True
from collections import Counter
from datetime import datetime
import json
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode

from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import add_scratch_argument, argparse, json_object, output_path, read_regular, scratch, set_scratch_root, sha256, write_json


def timestamp(s):
    d = datetime.fromisoformat(s.replace('Z', '+00:00'))
    if d.tzinfo is None:
        raise ValueError('Timezone required')
    return d

def url(s):
    x = urlsplit(s)
    if x.scheme.lower() not in ('http', 'https') or not x.hostname or x.username or x.password:
        raise ValueError('Expected credential-free HTTP(S) URL')
    host = x.hostname.lower()
    if ':' in host:
        host = '['+host+']'
    port = x.port
    if port is not None and not ((x.scheme.lower() == 'http' and port == 80) or (x.scheme.lower() == 'https' and port == 443)):
        host += ':'+str(port)
    return urlunsplit((x.scheme.lower(), host, x.path or '/', urlencode(sorted(parse_qsl(x.query, keep_blank_values=True))), ''))

def norm(s):
    if not isinstance(s, str):
        raise ValueError('Expected text')
    return ' '.join(s.casefold().split())

def check(author_path, review_paths, artifacts_path, manifest_path, manifest_sha):
    errors = []
    inputs = {str(scratch(p)): read_regular(scratch(p)) for p in [author_path, artifacts_path, manifest_path, *review_paths]}
    author = json_object(inputs[str(scratch(author_path))])
    artifacts = json_object(inputs[str(scratch(artifacts_path))])
    envs = [json_object(inputs[str(scratch(p))]) for p in review_paths]
    manifest_data = inputs[str(scratch(manifest_path))]
    if sha256(manifest_data) != manifest_sha:
        raise ValueError('Frozen manifest hash mismatch')
    manifest = json_object(manifest_data)
    modes = manifest['items']
    if not isinstance(modes, dict) or not modes or any(mode not in ('kg_only', 'source_backed') for mode in modes.values()):
        raise ValueError('Frozen manifest must classify each item as kg_only or source_backed')
    receipts = {}
    for row in manifest['receipts']:
        key = url(row['url'])
        if key in receipts:
            raise ValueError('Duplicate normalized URL in first-fetch receipts')
        receipts[key] = (row['capture_sha256'], row['fetched_by_role'], timestamp(row['fetched_at']))
    names = [env['reviewer'] for env in envs]
    actors = [author['author'], *names]
    if len(set(map(norm, actors))) != 3 or any(not norm(name) for name in actors):
        raise ValueError('Author and reviewers require three distinct fixed identities')
    if {env['role'] for env in envs} != {'factual', 'quality'}:
        raise ValueError('One factual and one quality envelope required')
    signed = [timestamp(e['signed_at']) for e in envs]
    latest = max(signed)
    sealed = timestamp(author['sealed_at'])
    released = timestamp(author['unsealed_at'])
    if not all(sealed < x <= released for x in signed):
        errors.append('author source seal/release chronology invalid')
    stage_seen = set()
    artifact_paths = set()
    artifact_digests = set()
    for row in artifacts['artifacts']:
        stage = row['stage']
        if stage not in ['M1','M2','M3','M4','M5']:
            raise ValueError('Artifact stage outside M1-M5')
        stage_seen.add(stage)
        p = scratch(row['path'])
        blob = read_regular(p)
        digest = sha256(blob)
        if p in artifact_paths or digest in artifact_digests:
            errors.append('artifact reused in M1-M5 inventory: '+str(p))
        artifact_paths.add(p)
        artifact_digests.add(digest)
        if digest != row['sha256']:
            errors.append('artifact hash mismatch: '+str(p))
        text = blob.decode('utf-8', errors='replace').casefold()
        for name in names:
            if name.casefold() in text or name.casefold() in str(p).casefold():
                errors.append('reviewer name occurs in '+stage+' artifact: '+name)
    if stage_seen != {'M1','M2','M3','M4','M5'}:
        errors.append('M1-M5 artifact inventory incomplete')
    author_urls = {url(x) for x in author['urls']}
    reports = []
    duplicate_metrics = []
    for env, signed_at in zip(envs, signed):
        peer = env['first_peer_read_at']
        if peer is not None and timestamp(peer) <= latest:
            errors.append('peer read before both signed: '+env['reviewer'])
        p = scratch(env['review_path'])
        blob = read_regular(p)
        if sha256(blob) != env['review_sha256']:
            errors.append('raw review hash mismatch: '+env['reviewer'])
        raw = json_object(blob)
        if raw.get('reviewer') != env['reviewer']:
            errors.append('review identity mismatch')
        rows = raw['items']
        by_id = {r['id']: r for r in rows}
        if not rows or len(by_id) != len(rows):
            raise ValueError('Nonempty unique item IDs required')
        rationales = [norm(r['rationale']) for r in rows]
        if any(not r for r in rationales):
            errors.append('blank rationale')
        duplicates = sum(n-1 for n in Counter(rationales).values())
        duplicate_metrics.append({'reviewer': env['reviewer'], 'duplicate_rows_beyond_first': duplicates, 'denominator': len(rows)})
        if duplicates*5 > len(rows):
            errors.append('more than 20 percent duplicate rationales: '+env['reviewer'])
        safety = env['child_safe_by_item']
        if set(safety) != set(by_id) or any(value is not True for value in safety.values()):
            errors.append('child-safe affirmation missing or false: '+env['reviewer'])
        choices = env['reviewer_chosen_sources']
        if set(by_id) != set(modes):
            errors.append('review item IDs differ from frozen manifest: '+env['reviewer'])
        if not set(choices) <= set(by_id):
            errors.append('chosen-source item coverage mismatch: '+env['reviewer'])
        for rid, row in by_id.items():
            if modes.get(rid) == 'kg_only':
                if choices.get(rid) or any(urlsplit(source).scheme.lower() in ('http', 'https') for source in row.get('sources', [])):
                    errors.append('external source cited on a frozen KG-only item: '+rid)
                continue
            cited = {url(x) for x in row['sources']}
            valid = []
            for choice in choices.get(rid, []):
                u = url(choice['url'])
                capture = scratch(choice['capture_path'])
                capture_sha = sha256(read_regular(capture))
                role = choice['fetched_by_role']
                fetched = timestamp(choice['fetched_at'])
                if capture_sha != choice['capture_sha256']:
                    errors.append('capture hash mismatch: '+rid)
                elif receipts.get(u) != (capture_sha, role, fetched) or fetched > signed_at:
                    errors.append('source does not bind a frozen first-fetch receipt before signing: '+rid)
                elif choice['chosen_by'] == env['reviewer'] and role in {'factual','quality','critic'} and u in cited and u not in author_urls:
                    valid.append(u)
            if not valid:
                errors.append('no independently fetched reviewer-chosen captured URL outside author set: '+env['reviewer']+':'+rid)
        reports.append(by_id)
    if set(reports[0]) != set(reports[1]):
        errors.append('whole-batch reviewer coverage differs')
    ids = set(reports[0]) | set(reports[1])
    same = sum(rid in reports[0] and rid in reports[1] and norm(reports[0][rid]['rationale']) == norm(reports[1][rid]['rationale']) for rid in ids)
    if same*5 > len(ids):
        errors.append('more than 20 percent identical per-item rationales across pair')
    return {'schema': 'cat-v4-independence-preflight-1', 'status': 'FAIL' if errors else 'PASS',
            'input_sha256': {path: sha256(data) for path, data in inputs.items()},
            'within_report_metrics': duplicate_metrics, 'cross_pair_identical_rows': same,
            'cross_pair_denominator': len(ids), 'errors': errors,
            'limits': 'Sidecar claims and retained capture bindings checked; dispatch/transcript isolation and source semantics still require independent human review. No native schema/gate changed.'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    add_scratch_argument(p)
    p.add_argument('--author-seal', required=True)
    p.add_argument('--reviews', required=True, nargs=2)
    p.add_argument('--artifacts', required=True)
    p.add_argument('--manifest', required=True)
    p.add_argument('--manifest-sha256', required=True)
    p.add_argument('--out', required=True)
    a = p.parse_args()
    try:
        set_scratch_root(a.scratch_root)
        output = output_path(a.out)
        result = check(a.author_seal, a.reviews, a.artifacts, a.manifest, a.manifest_sha256)
        write_json(output, result)
    except (ValueError, KeyError, OSError, TypeError, RecursionError) as e:
        p.error(str(e))
    print(json.dumps({'status':result['status'], 'output':str(output), 'errors':result['errors']}))
    raise SystemExit(0 if result['status']=='PASS' else 1)

if __name__ == '__main__':
    main()
