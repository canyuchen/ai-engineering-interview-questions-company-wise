#!/usr/bin/env python3
"""Search and validate the generated catalog using only Python's standard library."""
from __future__ import annotations
import argparse, json, sys
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse
from collect_sources import norm, ROOT, ALLOWED

def load():
    path=ROOT/'expansion/questions.json'
    if not path.exists(): raise ValueError('Catalog not built. Run python tools/collect_sources.py first.')
    return json.loads(path.read_text(encoding='utf-8'))

def validate(rows):
    assert rows, 'Empty catalog'
    ids=set(); prompts=set()
    sources=json.loads((ROOT/'expansion/sources.json').read_text(encoding='utf-8'))
    source_map={s['id']:s for s in sources}
    for r in rows:
        assert r['id'] not in ids, 'Duplicate ID: '+r['id']; ids.add(r['id'])
        key=norm(r['question']); assert key not in prompts, 'Duplicate normalized prompt'; prompts.add(key)
        assert r['kind'] in {'legacy_unverified','derived_practice','community_question_bank'}
        assert urlparse(r['source_url']).scheme in {'http','https'}
        assert isinstance(r['topics'],list) and r['topics']
        assert r['interview_date'] is None, 'Dates must not be invented'
        if r['kind']=='community_question_bank':
            assert r['license'] in ALLOWED
            assert len(r['source_commit'])==40 and r['source_line']>0
            assert r['source_commit'] in r['source_url']
            source=source_map[r['source_id']]
            assert (ROOT/'expansion'/source['license_file']).exists()
    stats=json.loads((ROOT/'expansion/stats.json').read_text(encoding='utf-8'))
    assert stats['total_questions']==len(rows)
    assert stats['new_questions']+stats['baseline_questions']==len(rows)
    assert stats['counts_by_kind']==dict(Counter(r['kind'] for r in rows))
    print('PASS: IDs, normalized duplicates, evidence labels, licenses, source coordinates and counts.')

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('command',choices=['search','stats','validate'])
    p.add_argument('query',nargs='?',default='')
    p.add_argument('--company',default=''); p.add_argument('--topic',default='');p.add_argument('--kind',default='')
    p.add_argument('--limit',type=int,default=30)
    args=p.parse_args(); rows=load()
    if args.command=='validate': validate(rows);return
    if args.command=='stats': print((ROOT/'expansion/stats.json').read_text(encoding='utf-8'));return
    matches=[r for r in rows if args.query.casefold() in (r['question']+' '+r['id']).casefold() and (not args.company or any(args.company.casefold() in c.casefold() for c in r['companies'])) and (not args.topic or args.topic in r['topics']) and (not args.kind or args.kind==r['kind'])]
    for r in matches[:max(0,args.limit)]:
        print(f"[{r['id']}] [{r['kind']}] {r['question']}\n  {r['source_url']}\n")
    print(f'{len(matches)} matches; showing {min(max(args.limit,0),len(matches))}.')
if __name__=='__main__':
    try: main()
    except (OSError, ValueError, KeyError, AssertionError) as exc:
        print('ERROR: '+str(exc),file=sys.stderr);sys.exit(1)
