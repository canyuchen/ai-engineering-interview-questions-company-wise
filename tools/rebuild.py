#!/usr/bin/env python3
"""Canonical rebuild: structured collection, rights, company evidence and audit."""
from __future__ import annotations
import argparse
import json
from collections import Counter
import collect_sources as c
import build_catalog as b
import refine_catalog as r
import extract_questions_v2 as e

TOPIC_ALIASES={'llm_architecture':'llm-architecture','ml_foundations':'ml-foundations','data_engineering':'data-engineering','context_engineering':'prompt-engineering','experimentation':'statistics','gpu_kernels':'gpu-kernels','distributed_training':'distributed-training'}


def main() -> None:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--self-test',action='store_true')
    args=parser.parse_args()
    c.self_test()
    e.self_test()
    # Run context and tag tests against the exact parser used by this entrypoint.
    b.strict_candidates=e.candidates
    b.self_test()
    if args.self_test: return
    path=c.OUT/'questions.json'
    previous=json.loads(path.read_text(encoding='utf-8')) if path.exists() else []
    c.candidates=e.candidates
    c.tags=b.enhanced_tags
    c.collect()
    raw=json.loads((c.OUT/'questions.json').read_text(encoding='utf-8'))
    original_labels={row['id']:row['companies'] for row in raw if row['kind']=='legacy_unverified'}
    (c.OUT/'excluded.json').unlink(missing_ok=True)
    r.main()
    rows=json.loads((c.OUT/'questions.json').read_text(encoding='utf-8'))
    for row in rows:
        topics={TOPIC_ALIASES.get(topic,topic) for topic in row['topics']}
        topics.update(b.enhanced_tags(row['question'],row.get('source_path','')))
        topics.discard('general')
        row['topics']=sorted(topics) or ['general']
        row['extraction_version']='authored-v1' if row['kind']=='derived_practice' else 'structured-v2'
        if row['kind']=='legacy_unverified':
            # A shared consumer-company chapter is not six specific interview claims.
            row['companies']=original_labels.get(row['id'],[])
            row.pop('company_relation',None)
    c.save('questions.json',rows)
    b.enrich()
    final_rows=json.loads((c.OUT/'questions.json').read_text(encoding='utf-8'))
    sources=json.loads((c.OUT/'sources.json').read_text(encoding='utf-8'))
    stats=json.loads((c.OUT/'stats.json').read_text(encoding='utf-8'))
    stats['parser_version']='structured-v2'
    stats['topic_count']=len(stats['counts_by_topic'])
    assert stats['counts_by_topic']==dict(Counter(topic for row in final_rows for topic in row['topics']))
    assert stats['company_label_count']==len({company for row in final_rows for company in row['companies']})
    assert sum(source['questions_added'] for source in sources)==stats['counts_by_kind'].get('community_question_bank',0)
    c.save('stats.json',stats)
    before={c.norm(row['question']):row['id'] for row in previous}
    after={c.norm(row['question']):row['id'] for row in final_rows}
    audit={'previous_saved_count':len(previous),'current_count':len(final_rows),'removed_ids':[identifier for key,identifier in before.items() if key not in after],'added_ids':[identifier for key,identifier in after.items() if key not in before],'rules':'Explicit Q markers, numbered scenario headings and Q tables; answer/preparation/navigation exclusions; rights filter and inherited company evidence retained. Source snapshots may change on rebuild.','limitations':'Structural tests and sampled source formats, not exhaustive human review, semantic deduplication, or verification of actual employer interviews.'}
    c.save('extraction-audit.json',audit)
    report=c.OUT/'REVIEW.md'
    report.write_text(report.read_text(encoding='utf-8')+'\n## Structured extraction, rights and reconciliation\n\nExplicit Q markers, numbered scenario headings and Q tables are recognized. Answer and preparation text are filtered before counting. Archived reprints with unverified file-level rights are excluded; their metadata is in [excluded.json](excluded.json). Changes from the previous saved index are in [extraction-audit.json](extraction-audit.json). Source contributions, topic counts and company counts reconcile with the question records. Neither audit proves interview authenticity.\n',encoding='utf-8')
    print('FINAL_RECONCILED_STATS\n'+json.dumps(stats,ensure_ascii=False,indent=2))


if __name__=='__main__': main()
