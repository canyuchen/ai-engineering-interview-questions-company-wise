#!/usr/bin/env python3
"""Canonical rebuild: source collection, conservative rights filter, labels, and quality audit."""
from __future__ import annotations
import argparse
import json
from collections import Counter
import collect_sources as c
import build_catalog as b
import refine_catalog as r

TOPIC_ALIASES={'llm_architecture':'llm-architecture','ml_foundations':'ml-foundations','data_engineering':'data-engineering','context_engineering':'prompt-engineering','experimentation':'statistics','gpu_kernels':'gpu-kernels','distributed_training':'distributed-training'}

def main() -> None:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--self-test',action='store_true')
    args=parser.parse_args()
    c.self_test(); b.self_test()
    if args.self_test: return
    c.candidates=b.strict_candidates
    c.tags=b.enhanced_tags
    c.collect()
    raw=json.loads((c.OUT/'questions.json').read_text(encoding='utf-8'))
    original_labels={row['id']:row['companies'] for row in raw if row['kind']=='legacy_unverified'}
    # A fresh collection must not append yesterday's exclusion records again.
    (c.OUT/'excluded.json').unlink(missing_ok=True)
    r.main()
    rows=json.loads((c.OUT/'questions.json').read_text(encoding='utf-8'))
    for row in rows:
        topics={TOPIC_ALIASES.get(topic,topic) for topic in row['topics']}
        topics.update(b.enhanced_tags(row['question'],row.get('source_path','')))
        topics.discard('general')
        row['topics']=sorted(topics) or ['general']
        if row['kind']=='legacy_unverified':
            # Shared consumer-company sections are not six specific company claims.
            # enrich() restores exact section labels and explicit Asked at claims.
            row['companies']=original_labels.get(row['id'],[])
            row.pop('company_relation',None)
    c.save('questions.json',rows)
    b.enrich()
    final_rows=json.loads((c.OUT/'questions.json').read_text(encoding='utf-8'))
    sources=json.loads((c.OUT/'sources.json').read_text(encoding='utf-8'))
    stats=json.loads((c.OUT/'stats.json').read_text(encoding='utf-8'))
    stats['topic_count']=len(stats['counts_by_topic'])
    assert stats['counts_by_topic']==dict(Counter(topic for row in final_rows for topic in row['topics']))
    assert stats['company_label_count']==len({company for row in final_rows for company in row['companies']})
    assert sum(source['questions_added'] for source in sources)==stats['counts_by_kind'].get('community_question_bank',0)
    c.save('stats.json',stats)
    report=c.OUT/'REVIEW.md'
    report.write_text(report.read_text(encoding='utf-8')+'\n## Rights and wrapper filtering\n\nArchived reprints with unverified file-level rights are excluded. Exclusion metadata (without copied question text) is retained in [excluded.json](excluded.json). Cross-reference wrappers are normalized and merged with their source records. Final source contributions, topic counts and company counts reconcile with the question records.\n',encoding='utf-8')
    print('FINAL_RECONCILED_STATS\n'+json.dumps(stats,ensure_ascii=False,indent=2))

if __name__=='__main__': main()
