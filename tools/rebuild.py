#!/usr/bin/env python3
"""Canonical rebuild: structured extraction, rights filtering and reconciled data.

Uses the source collector, the structure-aware extractor and the existing
rights-aware refiner directly. No optional build_catalog APIs are required.
"""
from __future__ import annotations
import argparse
import json
from collections import Counter
import collect_sources as c
import refine_catalog as r
import extract_questions_v2 as e
from question_bank import validate


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--self-test', action='store_true')
    args = parser.parse_args()
    c.self_test()
    e.self_test()
    if args.self_test:
        return
    path = c.OUT / 'questions.json'
    previous = json.loads(path.read_text(encoding='utf-8')) if path.exists() else []
    c.candidates = e.candidates
    c.collect()
    # Audits describe this build, not cumulative counts from unrelated snapshots.
    (c.OUT / 'excluded.json').unlink(missing_ok=True)
    r.main()
    rows = json.loads(path.read_text(encoding='utf-8'))
    sources = json.loads((c.OUT / 'sources.json').read_text(encoding='utf-8'))
    stats = json.loads((c.OUT / 'stats.json').read_text(encoding='utf-8'))
    for row in rows:
        row['extraction_version'] = 'authored-v1' if row['kind'] == 'derived_practice' else 'structured-v2'
    kinds = Counter(row['kind'] for row in rows)
    topics = Counter(topic for row in rows for topic in row['topics'])
    labels = sorted({company for row in rows for company in row['companies']})
    contributions = Counter(row['source_id'] for row in rows if row['kind'] == 'community_question_bank')
    for source in sources:
        source['questions_added'] = contributions[source['id']]
    stats.update({
        'parser_version': 'structured-v2',
        'total_questions': len(rows),
        'baseline_questions': kinds['legacy_unverified'],
        'new_questions': len(rows) - kinds['legacy_unverified'],
        'counts_by_kind': dict(kinds),
        'company_labels': labels,
        'company_label_count': len(labels),
        'counts_by_topic': dict(sorted(topics.items())),
        'topic_count': len(topics),
    })
    c.save('questions.json', rows)
    c.save('sources.json', sources)
    c.save('stats.json', stats)
    assert sum(source['questions_added'] for source in sources) == kinds['community_question_bank']
    validate(rows)
    c.render(rows, sources, stats)
    before = {c.norm(row['question']): row['id'] for row in previous}
    after = {c.norm(row['question']): row['id'] for row in rows}
    audit = {
        'previous_saved_count': len(previous), 'current_count': len(rows),
        'removed_ids': [identifier for key, identifier in before.items() if key not in after],
        'added_ids': [identifier for key, identifier in after.items() if key not in before],
        'rules': 'Explicit Q markers, numbered scenario headings and Q tables; answer/navigation filtering; archived-reprint rights exclusions; inherited company labels remain unverified.',
        'limitations': 'Structural tests and sampled source formats, not exhaustive human review, semantic deduplication or verification of actual employer interviews.'
    }
    c.save('extraction-audit.json', audit)
    # Do not ship stale raw copies that can retain previously excluded material.
    for stale in ['questions.raw.json', 'review-audit.json']:
        (c.OUT / stale).unlink(missing_ok=True)
    report = f'''# Quality and coverage audit\n\nCurrent snapshot: **{len(rows)}** indexed prompts; **{len(labels)}** company labels; **{len(topics)}** topic labels.\n\nThe structure-aware extractor recognizes explicit Q markers, numbered scenarios and question tables, preserving original source line coordinates. Answer and navigation text is filtered before counting. The rights-aware refiner excludes archived reprints with unverified file-level reuse rights and records metadata without republishing excluded text.\n\n[Extraction changes](extraction-audit.json) · [Rights exclusions](excluded.json) · [Source licenses](SOURCES.md) · [Statistics](stats.json) · [Official guidance and reported-source leads](REPORTED-SOURCES.md)\n\nIDs, normalized prompt uniqueness, evidence labels, license files, source coordinates, per-source contributions and category counts are validated. Company tags may originate from shared source sections or inherited Asked at claims; they are not independent proof that an employer asked a question. Topics overlap. Rules can miss valid questions or retain noise; answers are linked and not endorsed. This is not exhaustive editorial review or semantic deduplication.\n\nRebuild in a full Git checkout with `python tools/rebuild.py`, then validate with `python tools/question_bank.py validate`. Offline catalog search does not require rebuilding.\n'''
    (c.OUT / 'REVIEW.md').write_text(report, encoding='utf-8')
    index = c.OUT / 'README.md'
    index.write_text(index.read_text(encoding='utf-8') + '\n[Quality audit](REVIEW.md) · [Official guidance and reported-source leads](REPORTED-SOURCES.md) · [Additional source notes](ADDITIONAL-SOURCES.md)\n', encoding='utf-8')
    print('FINAL_RECONCILED_STATS\n' + json.dumps(stats, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
